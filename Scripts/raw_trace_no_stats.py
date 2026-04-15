# -----------------------------------------------------------------------------
# Full Trace Capture Script (ChipWhisperer)
# -----------------------------------------------------------------------------
#
# This script performs full trace acquisition for masked Keccak Chi experiments.
# Unlike the statistics-only script, it stores complete traces for offline
# analysis (e.g., plotting, manual inspection, alternative distinguishers).
#
# Overview:
#   - Captures traces using ChipWhisperer with firmware-triggered alignment
#   - Uses fixed-vs-random style input selection via pattern switching
#   - Stores full traces and corresponding labels as NumPy arrays
#
# Key features:
#   - Deterministic hardware setup (clock, ADC, baud resynchronisation)
#   - Robust command protocol with acknowledgement checks
#   - Per-trace random pattern selection (avoids ordering bias)
#
# Output:
#   - <name>_traces.npy : shape (n_traces, samples)
#   - <name>_labels.npy : corresponding input labels
#
# Notes:
#   - This script is used to generate datasets for validation and visualisation.
#   - Large datasets may require significant storage.
#   - For high-volume experiments, the statistics-only script is preferred.
# -----------------------------------------------------------------------------
# import numpy as np
import time
from tqdm import tqdm
import random
import chipwhisperer as cw
import os

CMD = 0x42
SAMPLES = 7500
OUT_PATH = "/home/adam/Desktop/CurrentInUse/full_traces/FirstOrder_one_loop_x4"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

scope  = cw.scope()
target = cw.target(scope, cw.targets.SimpleSerial2)

scope.default_setup()

# non-streaming capture
scope.adc.stream_mode = False
scope.adc.presamples = 0
scope.adc.offset = 0
scope.adc.timeout = 8.0
scope.trace.capture.trigger_source = "firmware trigger"

# set 24MHz and reset target
scope.clock.clkgen_src = "system"
scope.clock.adc_mul = 1
scope.clock.reset_dcms()

old_clk  = float(scope.clock.clkgen_freq) or 7.37e6
old_baud = int(target.baud)
# --- ADC clock: 4x target (≈96 MHz) ---

#scope.clock.adc_src = "clkgen_x4"     # multiply clkgen by 4
scope.clock.adc_mul = 4
scope.clock.reset_dcms()

NEW_CLK = 24e6
scope.clock.clkgen_freq = NEW_CLK
scope.io.nrst = "low";  time.sleep(0.05)
scope.io.nrst = "high"; time.sleep(0.05)

# baud guess based on clock ratio + fallbacks
ratio = NEW_CLK / old_clk
for guess in (int(round(old_baud * ratio)), 748800, 921600):
    try:
        target.baud = guess
        break
    except Exception:
        pass

print("clk:", float(scope.clock.clkgen_freq),
      "adc:", float(scope.clock.adc_freq),
      "baud:", target.baud)

print("clkgen:", float(scope.clock.clkgen_freq))
print("adc   :", float(scope.clock.adc_freq))
print("ratio :", float(scope.clock.adc_freq)/float(scope.clock.clkgen_freq))


scope.adc.samples = SAMPLES
print("ADC samples set to:", scope.adc.samples)

payload = b"\x00" * 16

# -----------------------------------------------------------------------------
# Firmware preparation sequence
# -----------------------------------------------------------------------------
# Each trace requires setting the internal device state before triggering:
#
#   0x20 : load pattern (controls fixed/random input selection)
#   0x22 : prepare randomness / internal state (for Chi operations)
#   0x21 : additional setup for specific commands (not used here)
#
# This ensures that each captured trace corresponds to a correctly initialised
# execution of the target operation.
# -----------------------------------------------------------------------------
def prepare(pattern, cmd):
    target.flush()

    target.send_cmd(0x20, 0x00, bytes([pattern]))
    ack = target.read_cmd('e', timeout=1000)
    target.flush()
    if not ack or ack[1] != ord('e'):
        raise RuntimeError(f"prepare_state 0x20 bad ack: {ack}")

    if cmd in {0x34, 0x35, 0x42, 0x43, 0x70}:
        target.send_cmd(0x22, 0x00, b"\x00")
        ack = target.read_cmd('e', timeout=1000)
        target.flush()
        if not ack or ack[1] != ord('e'):
            raise RuntimeError("prepare_state 0x22 bad ack")

    if cmd in {0x33}:
        target.send_cmd(0x21, 0x00, b"\x00")
        ack = target.read_cmd('e', timeout=1000)
        target.flush()
        if not ack or ack[1] != ord('e'):
            raise RuntimeError("prepare_state 0x21 bad ack")


def capture_once(cmd):
    scope.arm()
    time.sleep(0.001)

    target.send_cmd(cmd, 0x00, payload)

    if scope.capture(poll_done=True):
        raise RuntimeError("Capture timeout")

    trace = scope.get_last_trace()
    if trace is None or len(trace) != SAMPLES:
        raise RuntimeError("Trace length mismatch")

    return np.array(trace, dtype=np.float32)



# -----------------------------------------------------------------------------
# Trace capture loop
# -----------------------------------------------------------------------------
# For each trace:
#   - A random bit selects between two input patterns
#   - The device is prepared using the selected pattern
#   - A single trace is captured using firmware trigger alignment
#
# Labels:
#   - Stored as the selected pattern value (not the random bit)
#   - Used for fixed-vs-random statistical tests and analysis
#
# This corresponds to a standard two-class side-channel acquisition model.
# -----------------------------------------------------------------------------
def run_capture(cmd, n_traces, patterns, out_path):
    traces = np.zeros((n_traces, SAMPLES), dtype=np.float32)
    labels = np.zeros(n_traces, dtype=np.uint8)

    for i in tqdm(range(n_traces), desc=out_path):

        # Random selection avoids deterministic ordering effects (e.g. drift or bias)
        bit = random.getrandbits(1)
        pattern = patterns[bit]

        labels[i] = pattern

        prepare(pattern, cmd)

        tr = capture_once(cmd)
        traces[i] = tr

    np.save(f"{out_path}_traces.npy", traces)
    np.save(f"{out_path}_labels.npy", labels)

    print("Saved:", out_path)
# ================= runs =================


run_capture(0x42, 50000, (1, 0), OUT_PATH + "_50k_1_0_correct_masking_correct_chi_one")
run_capture(0x42, 50000, (7, 8), OUT_PATH + "_50k_7_8_wrong_masking_correct_chi_one")
run_capture(0x43, 50000, (1, 0), OUT_PATH + "_50k_1_0_correct_masking_incorrect_chi_one")
run_capture(0x43, 50000, (7, 8), OUT_PATH + "_50k_7_8_wrong_masking_incorrect_chi_one")
run_capture(0x42, 10000, (1, 0), OUT_PATH + "_10k_1_0_correct_masking_correct_chi_two")
run_capture(0x42, 10000, (7, 8), OUT_PATH + "_10k_7_8_wrong_masking_correct_chi_two")
run_capture(0x43, 10000, (1, 0), OUT_PATH + "_10k_1_0_correct_masking_incorrect_chi_two")
run_capture(0x43, 10000, (7, 8), OUT_PATH + "_10k_7_8_wrong_masking_incorrect_chi_two")
print("Done.")