import numpy as np
import json
import os
import sys

EPS = 1e-20


def load_array(base, name):
    path = os.path.join(base, f"{name}.npy")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {name}.npy")
    return np.load(path)


def main():
    base = "<PATH>/"


    print("\n=== TVLA Strength Analysis ===")
    print("Folder:", base)

    #Load required arrays
    delta_mu   = load_array(base, "delta_mu")
    pooled_var = load_array(base, "pooled_var")
    t1         = load_array(base, "t1")

    #Basic stats
    max_gap = np.max(np.abs(delta_mu))
    max_gap_idx = int(np.argmax(np.abs(delta_mu)))

    print(f"\nMax mean gap: {max_gap:.6e} @ index {max_gap_idx}")

    #SNR-like metric
    snr_like = np.abs(delta_mu) / np.sqrt(pooled_var + EPS)
    max_snr = np.max(snr_like)
    max_snr_idx = int(np.argmax(snr_like))

    print(f"Max SNR-like: {max_snr:.6e} @ index {max_snr_idx}")

    #Estimated traces required for TVLA detection
    # t = (Δμ) / (σ / sqrt(n)) => n ≈ (4.5 * σ / Δμ)^2
    required_n = (4.5 * np.sqrt(pooled_var + EPS) / (np.abs(delta_mu) + EPS))**2

    min_required_n = np.min(required_n)
    min_required_idx = int(np.argmin(required_n))

    print(f"\nEstimated traces needed for TVLA (best point):")
    print(f"{min_required_n:.2e} traces @ index {min_required_idx}")

    #Compare with current t-values
    max_t = np.max(np.abs(t1))
    print(f"\nMax |t1| observed: {max_t:.4f}")

    #Optional: window analysis if peak_indices.npy exists
    peak_path = os.path.join(base, "peak_indices.npy")
    if os.path.exists(peak_path):
        peak_indices = np.load(peak_path)

        print(f"\nWindowed analysis (radius=100 around peaks):")

        for idx in peak_indices[:10]:  # limit to first 10
            start = max(0, idx - 100)
            end   = min(len(delta_mu), idx + 100)

            local_gap = np.max(np.abs(delta_mu[start:end]))
            local_snr = np.max(snr_like[start:end])

            print(f"Window [{start}:{end}] -> gap={local_gap:.3e}, snr={local_snr:.3e}")

    #Save summary
    summary = {
        "max_mean_gap": float(max_gap),
        "max_mean_gap_idx": max_gap_idx,
        "max_snr_like": float(max_snr),
        "max_snr_idx": max_snr_idx,
        "min_required_traces": float(min_required_n),
        "min_required_traces_idx": min_required_idx,
        "max_t1": float(max_t),
    }

    with open(os.path.join(base, "strength_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nSaved summary → strength_summary.json")


if __name__ == "__main__":
    main()