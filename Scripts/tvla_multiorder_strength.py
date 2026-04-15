import numpy as np
import os
import sys
import json

EPS = 1e-20
TVLA_THRESHOLD = 4.5


def load_optional(base, name):
    path = os.path.join(base, f"{name}.npy")
    if os.path.exists(path):
        return np.load(path)
    return None


def max_abs(arr):
    a = np.abs(arr)
    idx = int(np.nanargmax(a))
    return float(a[idx]), idx


def estimate_required_traces(t_obs, n_current):
    """
    If current t = t_obs with n traces,
    then required n for t=4.5 is:

    n_req = n_current * (4.5 / t_obs)^2
    """
    if t_obs < 1e-12:
        return np.inf
    return n_current * (TVLA_THRESHOLD / t_obs)**2


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_tvla_strength_multiorder.py <stats_folder>")
        sys.exit(1)

    base = sys.argv[1]

    print("\n=== Multi-Order TVLA Strength Analysis ===")
    print("Folder:", base)

    # load core
    delta_mu   = load_optional(base, "delta_mu")
    pooled_var = load_optional(base, "pooled_var")
    t1         = load_optional(base, "t1")

    # optional higher-order
    t2  = load_optional(base, "t2")
    t2g = load_optional(base, "t2_group")
    t3  = load_optional(base, "t3")
    t3g = load_optional(base, "t3_group")
    t4  = load_optional(base, "t4")
    t4g = load_optional(base, "t4_group")

    # detect number of traces (approx)
    # infer from folder name if possible
    try:
        n_current = int(base.split("_")[-3])
    except:
        n_current = None

    print("\n--- First-order metrics")

    if delta_mu is not None and pooled_var is not None:
        snr_like = np.abs(delta_mu) / np.sqrt(pooled_var + EPS)
        max_snr, idx_snr = max_abs(snr_like)
        print(f"Max SNR-like: {max_snr:.6e} @ index {idx_snr}")

    if t1 is not None:
        t1_max, idx = max_abs(t1)
        print(f"Max |t1|: {t1_max:.4f} @ index {idx}")

        if n_current:
            n_req = estimate_required_traces(t1_max, n_current)
            print(f"Estimated traces needed (t1): {n_req:.2e}")

    # helper for higher-order
    def analyze_order(name, arr):
        if arr is None:
            return None

        val, idx = max_abs(arr)
        print(f"Max |{name}|: {val:.4f} @ index {idx}")

        if n_current:
            n_req = estimate_required_traces(val, n_current)
            print(f"Estimated traces needed ({name}): {n_req:.2e}")

        return val, idx

    print("\n--- Higher-order TVLA")

    analyze_order("t2", t2)
    analyze_order("t2_group", t2g)

    analyze_order("t3", t3)
    analyze_order("t3_group", t3g)

    analyze_order("t4", t4)
    analyze_order("t4_group", t4g)

    # summary JSON
    summary = {}

    if t1 is not None:
        val, idx = max_abs(t1)
        summary["t1"] = {"max": val, "idx": idx}

    for name, arr in [
        ("t2", t2), ("t2_group", t2g),
        ("t3", t3), ("t3_group", t3g),
        ("t4", t4), ("t4_group", t4g),
    ]:
        if arr is not None:
            val, idx = max_abs(arr)
            summary[name] = {"max": val, "idx": idx}

    with open(os.path.join(base, "multiorder_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nSaved → multiorder_summary.json")


if __name__ == "__main__":
    main()