/*MIT License

Copyright (c) 2025 Adam Beattie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
*/

#include "hal.h"
#include "simpleserial.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include "stm32f4xx.h"      // <-- defines IRQn_Type, SysTick_IRQn, etc.
#include "core_cm4.h"       // <-- defines __get_PRIMASK(), __DSB(), etc.

//Rho offsets
const uint8_t keccak_rho_offsets[5][5] = {
    {  0, 36,  3, 41, 18 },
    {  1, 44, 10, 45,  2 },
    { 62,  6, 43, 15, 61 },
    { 28, 55, 25, 21, 56 },
    { 27, 20, 39,  8, 14 }
};

#ifndef UNUSED
#define UNUSED(x) ((void)(x))
#endif

//error return value for CW
#define SS_ERR_LEN 0xA1

//Maximum usable 
#define MAX_ORDER 7 

#ifndef MASKING_ORDER
#define MASKING_ORDER 2
#endif

#define NROUNDS 24 //Not used
#define MASKING_N_VAL (MASKING_ORDER + 1)
#define MASKING_N MASKING_N_VAL

#define ENABLE_TIMING 1  

typedef struct {
    uint64_t share[MASKING_N];
} masked_uint64_t;

//fundamental masked object
typedef struct {
    uint64_t share[MASKING_N][5][5];   // share[s][x][y]
} masked_state_t;


#if ENABLE_TIMING
  #define TSTAMP(var) uint32_t var = DWT->CYCCNT
#else
  #define TSTAMP(var) do {} while (0)
#endif

// --- Exact-NOP macro using GAS .rept (no loop overhead) -----------------
#define NOP_BLOCK(N) asm volatile (".rept " #N "\n\tnop\n\t.endr\n" ::: "memory")

//Macro for setting state
#define ST(st, s, x, y)   ((st)->share[(s)][(x)][(y)])


//Main global state
volatile masked_state_t global_state;


// Random matrices for masked_chi()
volatile uint64_t randmat[5][5][MASKING_N][MASKING_N];
volatile uint64_t randmat_and [5][5][MASKING_N][MASKING_N];
volatile uint64_t randmat_in[5][5][4][MASKING_N][MASKING_N];
volatile uint64_t randmat_mid[5][5][MASKING_N][MASKING_N];
volatile uint64_t randmat_out[5][5][MASKING_N][MASKING_N];
volatile masked_state_t out_state;


/**
 * ----------------------------------------------------------------------------
 * Macros: TEST_PROLOGUE / TEST_EPILOGUE
 * ----------------------------------------------------------------------------
 * Purpose:
 *   Bracket a code region with:
 *     - IRQ masking (save/restore PRIMASK),
 *     - DSB/ISB barriers,
 *     - trace trigger high/low,
 *     - fixed NOP paddings (NOP_BLOCK(128)) to create clean capture windows.
 *
 * Side-channel Notes:
 *   - Stabilizes measurement alignment on ChipWhisperer;
 *   - Ensures reproducible trace length and boundaries.
 * ----------------------------------------------------------------------------
 */
#define TEST_PROLOGUE()                                    \
    do {                                                    \
        uint32_t __primask = __get_PRIMASK();              \
        __disable_irq();                                   \
        __DSB(); __ISB();                               \
        NOP_BLOCK(128);                                    \
        trigger_high();                                    \
        __DSB(); __ISB();

#define TEST_EPILOGUE()                                    \
        NOP_BLOCK(128);                                    \
        trigger_low();                                      \
        __DSB(); __ISB();                                  \
        if (!__primask) __enable_irq();                    \
    } while (0)


void dwt_init(void) {
    // Enable TRC (trace)
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    
    // Reset the cycle counter
    DWT->CYCCNT = 0;
    
    // Enable the cycle counter
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}


// ----------------------------------------------------------------------------
// K_NOT_SPLIT[] holds a fixed public Boolean share decomposition of 0xFFFF...FFFF.
// Used by masked_not() to implement bitwise NOT securely under Boolean masking.
// Constructed so that XOR of all shares == 0xFFFFFFFFFFFFFFFFULL.
// ----------------------------------------------------------------------------
uint64_t K_NOT_SPLIT[MASKING_N];


// ----------------------------------------------------------------------------
// The chip used for capture was not returning accurate 64 bit xor sums 
// This method splits each 64 bit xor into two 32 bit ones
// Seems to be working correctly now, unsure what the issue was so if required
// This should be able to be safely removed. However kept in to not disturb 
// analysis results
// ----------------------------------------------------------------------------
uint64_t xor64_safe(uint64_t a, uint64_t b) {
    uint32_t a_lo = (uint32_t)(a & 0xFFFFFFFFULL);
    uint32_t a_hi = (uint32_t)(a >> 32);
    uint32_t b_lo = (uint32_t)(b & 0xFFFFFFFFULL);
    uint32_t b_hi = (uint32_t)(b >> 32);

    uint64_t res_lo = (uint64_t)(a_lo ^ b_lo);
    uint64_t res_hi = (uint64_t)(a_hi ^ b_hi);

    return (res_hi << 32) | res_lo;
}


/**
 * Generates a 64-bit random value using two 32-bit RNG calls.
 *
 * Combines two outputs from the underlying RNG (`get_rand`) to construct
 * a full 64-bit value. The first call provides the high 32 bits and the
 * second provides the low 32 bits.
 *
 * This helper is used throughout the masking implementation to generate
 * randomness for share initialization and ISW masking gadgets.
 *
 * @return A 64-bit pseudo-random value.
 */
uint64_t get_rand64(void)
{
    uint64_t hi = get_rand();
    uint64_t lo = get_rand();
    return (hi << 32) | lo;
}


/**
 * Initializes the NOT-splitting constants used in masked Boolean NOT operations.
 *
 * This routine constructs a deterministic set of constants that allow the
 * masked NOT operation to be applied share-wise while preserving correctness
 * across the recombined value. Each share receives a different constant
 * derived from a fixed base value combined with an index-dependent pattern.
 *
 * The final share is chosen such that the XOR of all constants equals the
 * bitwise negation mask (~0ULL), ensuring the correct masked inversion
 * when shares are recombined.
 *
 * This initialization must be performed before masked NOT operations that
 * rely on the K_NOT_SPLIT constants.
 */
void init_not_split(void) {
    uint64_t acc = 0;
    for (size_t i = 0; i < MASKING_N - 1; i++) {
        K_NOT_SPLIT[i] = xor64_safe(0x9E3779B97F4A7C15ULL,
                                    0x0101010101010101ULL * (i + 1));
        acc = xor64_safe(acc, K_NOT_SPLIT[i]);
    }
    K_NOT_SPLIT[MASKING_N - 1] = xor64_safe(~0ULL, acc);
}


/**
 * Generates all randomness matrices required for masked Keccak gadget CHI.
 *
 * This command handler prepares the pre-generated randomness used by the
 * ISW-style masked AND operations and subsequent share-refresh steps inside
 * the masked Chi implementation.
 *
 * The following randomness matrices are populated:
 *
 *  - randmat_and : Random values used in ISW cross-terms for masked AND.
 *  - randmat_in  : Randomness used for input refresh stages before nonlinear
 *                  processing (multiple instances per lane).
 *  - randmat_mid : Randomness applied after the AND operation to refresh shares.
 *  - randmat_out : Randomness applied after storing results to maintain masking.
 *
 * Each matrix is symmetric (r[i][j] == r[j][i]) with zeros on the diagonal,
 * matching the requirements of ISW masking where randomness is shared
 * between share pairs.
 *
 * Random values are generated using `get_rand64()` for every unique pair
 * of shares across all 5×5 Keccak lanes.
 *
 * @param cmd   SimpleSerial command identifier (unused).
 * @param scmd  Subcommand identifier (unused).
 * @param len   Length of received data (unused).
 * @param buf   Input buffer (unused).
 *
 * @return 0x00 on success.
 */
 uint8_t prepare_randmat_cmd(uint8_t cmd, uint8_t scmd,
                                   uint8_t len, uint8_t *buf)
{
    UNUSED(cmd); UNUSED(scmd); UNUSED(len); UNUSED(buf);

    // --- Fill AND randomness (ISW) ---
    for (int y = 0; y < 5; y++) {
        for (int x = 0; x < 5; x++) {
            for (int i = 0; i < MASKING_N; i++) {
                for (int j = 0; j < MASKING_N; j++) {
                    if (i == j) {
                        randmat_and[x][y][i][j] = 0;
                    } else if (j > i) {
                        uint64_t r = get_rand64();
                        randmat_and[x][y][i][j] = r;
                        randmat_and[x][y][j][i] = r;
                    }
                }
            }
        }
    }
for (int y = 0; y < 5; y++) {
    for (int x = 0; x < 5; x++) {

        for (int k = 0; k < 4; k++) {   

            for (int i = 0; i < MASKING_N; i++) {
                for (int j = 0; j < MASKING_N; j++) {

                    if (i == j) {
                        randmat_in[x][y][k][i][j] = 0;
                    }
                    else if (j > i) {
                        uint64_t r = get_rand64();
                        randmat_in[x][y][k][i][j] = r;
                        randmat_in[x][y][k][j][i] = r;
                    }
                }
            }

        }
    }
}

    // --- Fill post-AND refresh randomness (r_mid) ---
    for (int y = 0; y < 5; y++) {
        for (int x = 0; x < 5; x++) {
            for (int i = 0; i < MASKING_N; i++) {
                for (int j = 0; j < MASKING_N; j++) {
                    if (i == j) {
                        randmat_mid[x][y][i][j] = 0;
                    } else if (j > i) {
                        uint64_t r = get_rand64();
                        randmat_mid[x][y][i][j] = r;
                        randmat_mid[x][y][j][i] = r;
                    }
                }
            }
        }
    }

    // --- Fill post-store refresh randomness (r_out) ---
    for (int y = 0; y < 5; y++) {
        for (int x = 0; x < 5; x++) {
            for (int i = 0; i < MASKING_N; i++) {
                for (int j = 0; j < MASKING_N; j++) {
                    if (i == j) {
                        randmat_out[x][y][i][j] = 0;
                    } else if (j > i) {
                        uint64_t r = get_rand64();
                        randmat_out[x][y][i][j] = r;
                        randmat_out[x][y][j][i] = r;
                    }
                }
            }
        }
    }

    return 0x00;
}

/**
 * Initializes the global masked Keccak state with a controlled test pattern.
 *
 * This command handler prepares the internal 5×5 masked Keccak state used
 * during side-channel testing. A lane value is selected according to the
 * requested test pattern and then split into MASKING_N shares for every
 * lane of the state.
 *
 * For each lane:
 *   - MASKING_N-1 shares are filled with fresh random values.
 *   - The final share is computed so that the XOR of all shares equals the
 *     selected lane value, preserving the masked representation.
 *
 * The selected pattern allows deterministic test vectors or fully random
 * inputs to be used during leakage experiments.
 *
 * Supported patterns:
 *   0 : Fully random lane value
 *   1 : Fixed constant (0x3F84A12BC9D07E55)
 *   2 : All-zero value
 *   3 : All bits set (~0ULL)
 *   4 : Alternating bits (0xAAAAAAAAAAAAAAAA)
 *   5 : Repeating pattern (0xA5A5A5A5A5A5A5A5)
 *   6 : Fixed test constant (0x123456789ABCDEF0)
 *
 * A fresh random seed (`chi_jitter_seed`) is also generated for later use
 * in Chi timing jitter.
 *
 * @param cmd   SimpleSerial command identifier (unused).
 * @param scmd  Subcommand identifier (unused).
 * @param len   Length of received data.
 * @param buf   Input buffer where buf[0] selects the test pattern.
 *
 * @return 0x00 on success.
 */
uint8_t prepare_state_cmd(uint8_t cmd, uint8_t scmd,
                         uint8_t len, uint8_t *buf)
{
    UNUSED(cmd); UNUSED(scmd); UNUSED(len);

    int pattern = buf[0];
    for (int y = 0; y < 5; y++) {
        for (int x = 0; x < 5; x++) {

            uint64_t lane_rand = get_rand64();
            uint64_t lane_val  = 0;

            switch (pattern) {
                case 0:  lane_val = lane_rand; break;                    // masked random native value
                case 1:  lane_val = 0x3F84A12BC9D07E55ULL; break;        // masked fixed native value
                case 2:  lane_val = 0x0ULL; break;
                case 3:  lane_val = ~0ULL; break;
                case 4:  lane_val = 0xAAAAAAAAAAAAAAAAULL; break;
                case 5:  lane_val = 0xA5A5A5A5A5A5A5A5ULL; break;
                case 6:  lane_val = 0x123456789ABCDEF0ULL; break;

                case 7:  lane_val = lane_rand; break;                    // UNMASKED random control
                case 8:  lane_val = 0x3F84A12BC9D07E55ULL; break;        // UNMASKED fixed control

                default: lane_val = 0ULL; break;
            }

            if (pattern == 7 || pattern == 8) {
                // ---- blatant first-order visible control ----
                global_state.share[0][x][y] = lane_val;
                for (int s = 1; s < MASKING_N; s++) {
                    global_state.share[s][x][y] = 0;
                }
            } else {
                // ---- normal Boolean masking ----
                uint64_t acc = 0;

                for (int s = 0; s < MASKING_N - 1; s++) {
                    uint64_t r = get_rand64();
                    global_state.share[s][x][y] = r;
                    acc ^= r;
                }

                global_state.share[MASKING_N - 1][x][y] = lane_val ^ acc;
            }
        }
    }

    return 0x00;
}

/**
 * Clears the global masked Keccak state.
 *
 * Sets all shares of every lane in the global state to zero. This is
 * typically used between experiments or before initializing a new test
 * configuration to ensure no residual masked values remain.
 */
void clear_global_state(void)
{
    for (int s = 0; s < MASKING_N; s++)
        for (int x = 0; x < 5; x++)
            for (int y = 0; y < 5; y++)
                global_state.share[s][x][y] = 0ULL;
}

/**
 * Clears all internal masked state used by the test harness.
 *
 * This helper currently resets the global masked state but exists as a
 * separate abstraction to allow additional internal structures to be
 * cleared in the future if needed.
 */
static void clear_internal()
{
    clear_global_state();
}

/**
 * Refreshes a Boolean-masked value using a precomputed symmetric randomness matrix.
 *
 * This operation re-randomizes the shares of a masked value without changing
 * the underlying recombined secret. For each distinct share pair (i, j), the
 * same random value r[i][j] is XORed into both shares. Because the value is
 * added twice, the global XOR of all shares remains unchanged.
 *
 * This is a standard share-refresh step used in masking schemes to decorrelate
 * intermediate values and reduce leakage accumulation between operations.
 *
 * The randomness matrix is expected to be symmetric with zeros on the diagonal,
 * matching the usual ISW-style pairwise refresh layout.
 *
 * @param v  Masked value to refresh in place.
 * @param r  Pairwise randomness matrix used for share refreshing.
 */
static inline void masked_refresh(
    volatile masked_uint64_t *v,
    const volatile uint64_t r[MASKING_N][MASKING_N])
{
    for (size_t i = 0; i < MASKING_N; i++) {
        for (size_t j = i + 1; j < MASKING_N; j++) {
            uint64_t rij = r[i][j];
            v->share[i] ^= rij;
            v->share[j] ^= rij;
        }
    }
}

/**
 * Stores a single masked lane back into the Keccak state.
 *
 * This helper writes all shares of a masked lane into the state position
 * (x, y). Each share is stored explicitly to preserve predictable code shape.
 *
 * After each store, a compiler barrier is applied and the temporary register is
 * precharged to zero. This mirrors the load-side behavior and is intended to
 * reduce unwanted data-dependent register effects in side-channel measurements.
 *
 * @param st   Destination masked Keccak state.
 * @param x    Lane x-coordinate.
 * @param y    Lane y-coordinate.
 * @param src  Source masked lane to store.
 */
__attribute__((optimize("O0")))
void lane_store(masked_state_t *st,
                              int x, int y,
                              const masked_uint64_t *src)
{
    uint64_t t = 0;

    for (int s = 0; s < MASKING_N; s++) {

        t = src->share[s];
        ST(st, s, x, y) = t;

        // --- precharge ---
        barrier_u64(t);
        t = 0;
        barrier_u64(t);
    }
}


/**
 * Computes the share-wise XOR of two Boolean-masked values.
 *
 * Since Boolean masking is linear with respect to XOR, this operation is
 * performed independently on each share. The recombined result therefore
 * equals the XOR of the two underlying unmasked values.
 *
 * This is one of the fundamental linear operations used throughout masked
 * Keccak and other Boolean-masked computations.
 *
 * @param out  Destination masked value.
 * @param a    First masked input.
 * @param b    Second masked input.
 */
void masked_xor(volatile masked_uint64_t *out,
                const volatile  masked_uint64_t *a,
                const volatile masked_uint64_t *b) {
    for (size_t i = 0; i < MASKING_N; i++) {
        out->share[i] = xor64_safe(a->share[i], b->share[i]);
    }
}


/**
 * Computes a Boolean-masked AND using the ISW masking scheme.
 *
 * This function implements a secure nonlinear AND between two Boolean-masked
 * values. Unlike XOR, AND is not linear under Boolean masking, so the output
 * cannot be computed share-wise alone. Instead, the ISW construction is used:
 *
 *   - diagonal terms compute (a_i & b_i) for each share
 *   - cross-terms combine (a_i & b_j) and (a_j & b_i)
 *   - shared randomness r[i][j] is used to mask the cross-term contributions
 *
 * The result is a fresh masked sharing of the bitwise AND of the underlying
 * values, while preserving the required security order under the masking model.
 *
 * The implementation is specialized by `MASKING_N` for clarity and efficiency.
 * The randomness matrix is expected to be symmetric, with the upper triangle
 * providing the pairwise random masks used by the ISW correction terms.
 *
 * @param out  Destination masked value.
 * @param a    First masked input.
 * @param b    Second masked input.
 * @param r    Pairwise randomness matrix for ISW cross-term protection.
 */
#if MASKING_N == 1
void masked_and(volatile masked_uint64_t *out,
                const volatile masked_uint64_t *a,
                const volatile masked_uint64_t *b,
                const volatile uint64_t r[1][1]) {
    out->share[0] = a->share[0] & b->share[0];
}

#elif MASKING_N == 2
static inline void masked_and(masked_uint64_t *out,
                              const volatile masked_uint64_t *a,
                              const volatile masked_uint64_t *b,
                              const volatile uint64_t r[2][2])
{
    // Compute diagonal terms
    uint64_t t00 = a->share[0] & b->share[0];
    uint64_t t11 = a->share[1] & b->share[1];

    // Cross-term (shared randomness)
    uint64_t t01 = xor64_safe((a->share[0] & b->share[1]),
                              (a->share[1] & b->share[0]));

    // Apply ISW correction
    out->share[0] = xor64_safe(t00, r[0][1]);
    out->share[1] = xor64_safe(t11, xor64_safe(t01, r[0][1]));
}

#elif MASKING_N == 3
static inline void masked_and(volatile masked_uint64_t *out,
                              const volatile masked_uint64_t *a,
                              const volatile masked_uint64_t *b,
                              const volatile uint64_t r[3][3]) {
    // Diagonal terms
    out->share[0] = a->share[0] & b->share[0];
    out->share[1] = a->share[1] & b->share[1];
    out->share[2] = a->share[2] & b->share[2];

    // Cross terms
    uint64_t t01 = xor64_safe((a->share[0] & b->share[1]),
                              (a->share[1] & b->share[0]));
    out->share[0] = xor64_safe(out->share[0], r[0][1]);
    out->share[1] = xor64_safe(out->share[1], xor64_safe(t01, r[0][1]));

    uint64_t t02 = xor64_safe((a->share[0] & b->share[2]),
                              (a->share[2] & b->share[0]));
    out->share[0] = xor64_safe(out->share[0], r[0][2]);
    out->share[2] = xor64_safe(out->share[2], xor64_safe(t02, r[0][2]));

    uint64_t t12 = xor64_safe((a->share[1] & b->share[2]),
                              (a->share[2] & b->share[1]));
    out->share[1] = xor64_safe(out->share[1], r[1][2]);
    out->share[2] = xor64_safe(out->share[2], xor64_safe(t12, r[1][2]));
}

#elif MASKING_N == 4
static inline void masked_and(volatile masked_uint64_t *out,
                              const volatile masked_uint64_t *a,
                              const volatile masked_uint64_t *b,
                              const volatile uint64_t r[4][4]) {
    // Diagonal terms
    out->share[0] = a->share[0] & b->share[0];
    out->share[1] = a->share[1] & b->share[1];
    out->share[2] = a->share[2] & b->share[2];
    out->share[3] = a->share[3] & b->share[3];

    // Cross terms
    uint64_t t01 = xor64_safe((a->share[0] & b->share[1]),
                              (a->share[1] & b->share[0]));
    out->share[0] = xor64_safe(out->share[0], r[0][1]);
    out->share[1] = xor64_safe(out->share[1], xor64_safe(t01, r[0][1]));

    uint64_t t02 = xor64_safe((a->share[0] & b->share[2]),
                              (a->share[2] & b->share[0]));
    out->share[0] = xor64_safe(out->share[0], r[0][2]);
    out->share[2] = xor64_safe(out->share[2], xor64_safe(t02, r[0][2]));

    uint64_t t03 = xor64_safe((a->share[0] & b->share[3]),
                              (a->share[3] & b->share[0]));
    out->share[0] = xor64_safe(out->share[0], r[0][3]);
    out->share[3] = xor64_safe(out->share[3], xor64_safe(t03, r[0][3]));

    uint64_t t12 = xor64_safe((a->share[1] & b->share[2]),
                              (a->share[2] & b->share[1]));
    out->share[1] = xor64_safe(out->share[1], r[1][2]);
    out->share[2] = xor64_safe(out->share[2], xor64_safe(t12, r[1][2]));

    uint64_t t13 = xor64_safe((a->share[1] & b->share[3]),
                              (a->share[3] & b->share[1]));
    out->share[1] = xor64_safe(out->share[1], r[1][3]);
    out->share[3] = xor64_safe(out->share[3], xor64_safe(t13, r[1][3]));

    uint64_t t23 = xor64_safe((a->share[2] & b->share[3]),
                              (a->share[3] & b->share[2]));
    out->share[2] = xor64_safe(out->share[2], r[2][3]);
    out->share[3] = xor64_safe(out->share[3], xor64_safe(t23, r[2][3]));
}

#elif MASKING_N == 5
static inline void masked_and(volatile masked_uint64_t *out,
                              const volatile masked_uint64_t *a,
                              const volatile masked_uint64_t *b,
                              const volatile uint64_t r[5][5]) {
    // Diagonal
    for (int i = 0; i < 5; i++)
        out->share[i] = a->share[i] & b->share[i];

    // Cross terms
    for (int i = 0; i < 5; i++) {
        for (int j = i + 1; j < 5; j++) {
            uint64_t t = xor64_safe((a->share[i] & b->share[j]),
                                    (a->share[j] & b->share[i]));
            out->share[i] = xor64_safe(out->share[i], r[i][j]);
            out->share[j] = xor64_safe(out->share[j], xor64_safe(t, r[i][j]));
        }
    }
}

#else
static inline void masked_and(volatile masked_uint64_t *out,
                              const volatile masked_uint64_t *a,
                              const volatile masked_uint64_t *b,
                              const volatile uint64_t r[MASKING_N][MASKING_N]) {
    // Diagonal
    for (size_t i = 0; i < MASKING_N; i++)
        out->share[i] = a->share[i] & b->share[i];

    // Cross terms
    for (size_t i = 0; i < MASKING_N; i++) {
        for (size_t j = i + 1; j < MASKING_N; j++) {
            uint64_t t = xor64_safe((a->share[i] & b->share[j]),
                                    (a->share[j] & b->share[i]));
            out->share[i] = xor64_safe(out->share[i], r[i][j]);
            out->share[j] = xor64_safe(out->share[j], xor64_safe(t, r[i][j]));
        }
    }
}
#endif

/**
 * Computes the Boolean NOT of a masked value.
 *
 * In Boolean masking, a direct bitwise NOT cannot simply be applied to
 * each share independently because the recombined value would not equal
 * the negation of the underlying secret. Instead, a predefined constant
 * vector `K_NOT_SPLIT` is XORed into the shares.
 *
 * The constants are constructed such that the XOR of all constants equals
 * the all-ones mask (~0ULL). As a result, when the shares are recombined,
 * the resulting value is the correct bitwise negation of the original
 * unmasked value.
 *
 * @param dst  Destination masked value.
 * @param src  Source masked value to invert.
 */
static inline void masked_not(volatile masked_uint64_t *dst, const volatile masked_uint64_t *src) {
    for (size_t i = 0; i < MASKING_N; ++i)
        dst->share[i] = xor64_safe(src->share[i],  K_NOT_SPLIT[i]);
}


// ----------------------------------------------------------------------------
// copy_share_scalar64()
// ----------------------------------------------------------------------------
// Performs a controlled 64-bit copy using two explicit 32-bit loads and stores
// via inline assembly.
//
// Instead of relying on a standard 64-bit assignment or memcpy, this function
// splits the operation into two 32-bit transfers:
//
//     lo = src[31:0]
//     hi = src[63:32]
//
// and writes them separately to the destination.
//
// Rationale:
//   - Ensures a predictable instruction sequence (ldr/str pairs) on the target
//     microcontroller, avoiding compiler-dependent optimisations or register
//     reuse that may occur with normal 64-bit assignments.
//   - Provides stable and inspectable behaviour at the assembly level, which
//     is important for side-channel analysis and trace alignment.
//   - Avoids potential issues with 64-bit load/store handling on embedded
//     platforms where such operations may be decomposed unpredictably.
//
// The "memory" clobber prevents the compiler from reordering memory accesses
// around this block, preserving the intended execution structure.
//
// This function is used when copying masked shares to maintain consistency
// in data movement during leakage measurements.
//
// Note:
// This is not intended as a performance optimisation. It is a measurement-
// oriented helper to enforce deterministic low-level behaviour.
// ----------------------------------------------------------------------------
static inline void copy_share_scalar64(uint64_t *dst, const uint64_t *src)
{
    uint32_t lo, hi;
    const uint32_t *s32 = (const uint32_t *)src;
    uint32_t *d32 = (uint32_t *)dst;
    // Explicit 32-bit load/store sequence to avoid compiler-generated 64-bit moves
    __asm__ volatile (
        "ldr %[lo], [%[s], #0]\n\t"
        "ldr %[hi], [%[s], #4]\n\t"
        "str %[lo], [%[d], #0]\n\t"
        "str %[hi], [%[d], #4]\n\t"
        : [lo] "=&r" (lo), [hi] "=&r" (hi)
        : [s] "r" (s32), [d] "r" (d32)
        : "memory"
    );
}

// ----------------------------------------------------------------------------
// masked_chi_no_not()
// ----------------------------------------------------------------------------
// Reference masked Chi implementation variant without an explicit masked NOT.
// Instead of computing (~b) & c directly, the function evaluates an equivalent
// split form using separately loaded masked lanes and a refreshed duplicate of
// the c lane for the nonlinear masked AND.
//
// The main purpose of this version is experimental control:
//   - a, b, and c are loaded as masked lanes from the input state
//   - c is duplicated into c_for_and
//   - only the duplicate used in the AND is refreshed
//   - the original c_loc is preserved for the subsequent masked XOR
//
// This separation is intended to reduce direct reuse of the same masked value
// across nonlinear and linear steps, allowing the effect of the AND path and
// refresh step to be studied more clearly in leakage experiments.
//
// Computation performed per lane:
//   bc  = b AND refresh(copy(c))
//   tmp = a XOR c
//   o   = tmp XOR bc
//
// The function is marked noinline and O0 so that the compiled structure remains
// as stable and inspectable as possible during trace capture and assembly-level
// analysis. Timing markers (TSTAMP) are included for coarse execution profiling.
//
// Note:
// The current version contains break statements inside both x and y loops,
// meaning that only the first lane processed by the nested loop body is
// evaluated during this debug/testing build. This is intentional for focused
// measurement and should be removed for full-state execution.
// ----------------------------------------------------------------------------
__attribute__((noinline,optimize("O0")))
void masked_chi_no_not(
    masked_state_t *out,
    const masked_state_t *in,
    const uint64_t r_and[5][5][MASKING_N][MASKING_N],
    const uint64_t r_refresh[5][5][MASKING_N][MASKING_N]   // <-- add this
)
{
    TSTAMP(begin_method);
    static const uint8_t xb_lut[5] = {1,2,3,4,0};
    static const uint8_t xc_lut[5] = {2,3,4,0,1};
    TSTAMP(at_loop);
    for (int y = 0; y < 5; y++) {
        TSTAMP(outter_loop);
        for (int x = 0; x < 5; x++) {
            TSTAMP(inner_loop);
            int xb = xb_lut[x];
            int xc = xc_lut[x];

            masked_uint64_t a;
            masked_uint64_t b_loc, c_loc;
            masked_uint64_t c_for_and;   // <-- new
            masked_uint64_t bc;
            masked_uint64_t tmp;
            masked_uint64_t o;

            for (int s = 0; s < MASKING_N; s++) {
                copy_share_scalar64(&a.share[s],     &ST(in, s, x,  y));
                copy_share_scalar64(&b_loc.share[s], &ST(in, s, xb, y));
                copy_share_scalar64(&c_loc.share[s], &ST(in, s, xc, y));
            }

            // --- duplicate c ---
            for (int s = 0; s < MASKING_N; s++) {
                c_for_and.share[s] = c_loc.share[s];
            }

            // --- refresh ONLY the AND copy ---
            masked_refresh(&c_for_and, r_refresh[x][y]);

            // --- use separated versions ---
            masked_and(&bc, &b_loc, &c_for_and, r_and[x][y]);
            masked_xor(&tmp, &a, &c_loc);      // original
            masked_xor(&o, &tmp, &bc);

            lane_store(out, x, y, &o);
          
          break; 
        }
       break; 
    } 
}

// ----------------------------------------------------------------------------
// masked_chi_no_not_broken()
// ----------------------------------------------------------------------------
// Intentionally broken variant of masked_chi_no_not() used as a positive
// leakage control.
//
// This function is structurally almost identical to the non-broken version,
// except that after loading the masked lane a, all shares except share 0 are
// explicitly zeroed:
//
//     for (int s = 1; s < MASKING_N; s++) {
//         a.share[s] = 0;
//     }
//
// This collapses the masking of a into a single effective share, destroying the
// share-independence assumptions required for secure masking while preserving
// the surrounding control flow and overall computation pattern as closely as
// possible.
//
// The goal is to create a controlled comparison case where:
//   - masking correctness is deliberately violated
//   - the nonlinear and dataflow structure remain otherwise similar
//   - leakage detection methods can be validated against known broken masking
//
// As in the non-broken version, c is duplicated and refreshed only on the copy
// used for the AND path. The resulting computation is:
//
//   bc  = b AND refresh(copy(c))
//   tmp = broken(a) XOR c
//   o   = tmp XOR bc
//
// This function is also compiled with noinline and O0 to preserve a stable
// and easily inspectable instruction sequence for side-channel experiments.
//
// Note:
// As with the corresponding debug/reference variant, the inner break statements
// cause only the first visited lane to be processed in this build.
// ----------------------------------------------------------------------------

__attribute__((noinline,optimize("O0")))
void masked_chi_no_not_broken(
    masked_state_t *out,
    const masked_state_t *in,
    const uint64_t r_and[5][5][MASKING_N][MASKING_N],
    const uint64_t r_refresh[5][5][MASKING_N][MASKING_N]
)
{
    TSTAMP(being_method);
    static const uint8_t xb_lut[5] = {1,2,3,4,0};
    static const uint8_t xc_lut[5] = {2,3,4,0,1};
    TSTAMP(at_loop);
    for (int y = 0; y < 5; y++) {
        TSTAMP(outter_loop);
        for (int x = 0; x < 5; x++) {
            TSTAMP(inner_loop);

            int xb = xb_lut[x];
            int xc = xc_lut[x];

            masked_uint64_t a;
            masked_uint64_t b_loc, c_loc;
            masked_uint64_t c_for_and;
            masked_uint64_t bc;
            masked_uint64_t tmp;
            masked_uint64_t o;

            // --- load shares ---
            for (int s = 0; s < MASKING_N; s++) {
                copy_share_scalar64(&a.share[s],     &ST(in, s, x,  y));
                copy_share_scalar64(&b_loc.share[s], &ST(in, s, xb, y));
                copy_share_scalar64(&c_loc.share[s], &ST(in, s, xc, y));
            }

            // 🔴 BLATANT BREAK: collapse masking of 'a'
            for (int s = 1; s < MASKING_N; s++) {
                a.share[s] = 0;
            }

            // --- duplicate c ---
            for (int s = 0; s < MASKING_N; s++) {
                c_for_and.share[s] = c_loc.share[s];
            }

            // --- refresh ONLY the AND copy ---
            masked_refresh(&c_for_and, r_refresh[x][y]);

            // --- masked computation ---
            masked_and(&bc, &b_loc, &c_for_and, r_and[x][y]);
            masked_xor(&tmp, &a, &c_loc);
            masked_xor(&o, &tmp, &bc);

            lane_store(out, x, y, &o);
            break;
        }
        break;
    }
}

/**
 * Debug capture wrapper for the masked_chi_no_not() experiment.
 *
 * This SimpleSerial command handler executes the non-broken masked Chi variant
 * under controlled timing conditions for trace capture.
 *
 * Execution flow:
 *  - enforce instruction/data synchronization barriers
 *  - run the test prologue and optional padding NOPs
 *  - capture the cycle counter immediately before and after masked_chi_no_not()
 *  - run the test epilogue used by the measurement framework
 *
 * The measured cycle count is currently retained only for local debugging and
 * is not transmitted to the host.
 *
 * Randomness inputs:
 *  - randmat_and : ISW-style randomness used by masked_and()
 *  - randmat_mid : refresh randomness used for the duplicated AND input
 *
 * This handler is intended for side-channel trace acquisition and timing /
 * structural debugging rather than full functional execution of the Keccak
 * permutation.
 *
 * @param cmd   SimpleSerial command identifier (unused).
 * @param scmd  SimpleSerial subcommand identifier (unused).
 * @param len   Input length (unused).
 * @param buf   Input buffer (unused).
 *
 * @return 0x00 on success.
 */
__attribute__((optimize("O0")))
static uint8_t chi_test_no_save_debug_base_not(uint8_t cmd, uint8_t scmd,
                                uint8_t len, uint8_t *buf)
{
    UNUSED(cmd); UNUSED(scmd); UNUSED(len); UNUSED(buf);

    uint32_t start, end, time;

    __DSB();
    __ISB();
    TEST_PROLOGUE();
    NOP_BLOCK(128);
    start = DWT->CYCCNT;

    masked_chi_no_not(&out_state,
                   &global_state,
                   randmat_and, randmat_mid);

    end = DWT->CYCCNT;
    TEST_EPILOGUE();

    time = end - start;
    (void)time;

    return 0x00;
}

/**
 * Debug capture wrapper for the intentionally broken masked_chi_no_not_broken()
 * experiment.
 *
 * This handler is identical in structure to chi_test_no_save_debug_base_not(),
 * but invokes the deliberately broken masking variant in which one operand has
 * its masking collapsed to a single effective share.
 *
 * It is used as a known-leaky reference case for:
 *  - validating trace capture
 *  - confirming that the analysis pipeline detects broken masking
 *  - comparing timing and leakage behaviour against the non-broken variant
 *
 * Execution is surrounded by synchronization barriers, capture prologue /
 * epilogue hooks, and cycle counter measurements in the same manner as the
 * non-broken test wrapper.
 *
 * Randomness inputs:
 *  - randmat_and : ISW-style randomness for masked_and()
 *  - randmat_mid : refresh randomness for the duplicated AND input
 *
 * @param cmd   SimpleSerial command identifier (unused).
 * @param scmd  SimpleSerial subcommand identifier (unused).
 * @param len   Input length (unused).
 * @param buf   Input buffer (unused).
 *
 * @return 0x00 on success.
 */
__attribute__((optimize("O0")))
static uint8_t chi_test_no_save_debug_base_not_broken(uint8_t cmd, uint8_t scmd,
                                uint8_t len, uint8_t *buf)
{
    UNUSED(cmd); UNUSED(scmd); UNUSED(len); UNUSED(buf);

    uint32_t start, end, time;

    __DSB();
    __ISB();
    TEST_PROLOGUE();
    NOP_BLOCK(128);
    start = DWT->CYCCNT;

    masked_chi_no_not_broken(&out_state,
                   &global_state,
                   randmat_and, randmat_mid);

    end = DWT->CYCCNT;
    TEST_EPILOGUE();

    time = end - start;
    (void)time;

    return 0x00;
}

int main(void)
{
    platform_init();
    init_uart();
    trigger_setup();
    init_not_split();
    dwt_init();
    simpleserial_init();       

    simpleserial_addcmd(0x20, 0, prepare_state_cmd);
    simpleserial_addcmd(0x22, 0, prepare_randmat_cmd);

    simpleserial_addcmd(0x42, 0, chi_test_no_save_debug_base_not);
    simpleserial_addcmd(0x43, 0, chi_test_no_save_debug_base_not_broken);


    while (1)
        simpleserial_get();
}

/*-----------------------------------------------------------------------------
 * End of File
 *---------------------------------------------------------------------------*/