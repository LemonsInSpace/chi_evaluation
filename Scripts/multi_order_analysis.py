#!/usr/bin/env python3

import pathlib
import numpy as np
import matplotlib.pyplot as plt
import json
import argparse


# -----------------------------------------------------------------------------
# Multi-Order Aggregated TVLA Analysis
# -----------------------------------------------------------------------------
#
# Aggregates TVLA results across multiple statistical orders to analyse
# combined leakage structure.
#
# For a set of TVLA arrays (t1, t2, t3, t4, etc.), the script computes:
#   - Sum of absolute values across orders
#   - L2 norm across orders
#   - Maximum absolute value across orders
#
# These aggregated metrics provide a global view of statistical structure,
# highlighting regions where multiple orders contribute simultaneously.
#
# This is used to support analysis of whether observed signals arise from
# structured implementation effects rather than isolated leakage sources.
#
# Inputs:
#   - Directory containing TVLA arrays for multiple orders
#
# Outputs:
#   - Aggregated traces (sum_abs, l2, max_abs)
#   - Per-order and aggregated summary statistics (JSON)
#   - Plots visualising combined statistical structure
# -----------------------------------------------------------------------------

# CONFIG
ORDERS = [
    "t1",
    "t_var",
    "t2", "t2_group",
    "t3", "t3_group",
    "t4", "t4_group"
]

THRESHOLD = 4.5


def load_arrays(base):
    arrays = {}
    for name in ORDERS:
        path = base / f"{name}.npy"
        if path.exists():
            arrays[name] = np.load(path)
        else:
            arrays[name] = None
    return arrays


def aggregate(arrays):
    valid = [a for a in arrays.values() if a is not None]

    if not valid:
        raise RuntimeError("No arrays loaded")

    stacked = np.stack(valid, axis=0)

    agg = {}

    # Sum of absolute values
    agg["sum_abs"] = np.sum(np.abs(stacked), axis=0)

    # L2 norm
    agg["l2"] = np.sqrt(np.sum(stacked**2, axis=0))

    # Max absolute across orders
    agg["max_abs"] = np.max(np.abs(stacked), axis=0)

    return agg


def compute_metrics(arr):
    abs_arr = np.abs(arr)

    return {
        "max": float(np.max(abs_arr)),
        "argmax": int(np.argmax(abs_arr)),
        "mean": float(np.mean(abs_arr)),
        "mass": float(np.sum(abs_arr)),
        "exceed_2": int(np.sum(abs_arr > 2.0)),
        "exceed_3": int(np.sum(abs_arr > 3.0)),
        "exceed_4.5": int(np.sum(abs_arr > THRESHOLD)),
    }


def plot(arr, title, outpath):
    plt.figure(figsize=(12,4))
    plt.plot(arr)

    plt.axhline(THRESHOLD, linestyle="--")
    plt.axhline(-THRESHOLD, linestyle="--")

    plt.title(title)
    plt.xlabel("Sample Index")
    plt.ylabel("Aggregated Magnitude")
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Multi-order TVLA aggregation")
    parser.add_argument("input_dir", help="Directory containing TVLA .npy files")
    args = parser.parse_args()

    base = pathlib.Path(args.input_dir)

    if not base.exists():
        raise RuntimeError("Invalid path")

    arrays = load_arrays(base)
    shapes = [a.shape for a in arrays.values() if a is not None]
    if len(set(shapes)) > 1:
        raise RuntimeError(f"Inconsistent TVLA array shapes detected: {shapes}")
    agg = aggregate(arrays)
    loaded = [name for name, a in arrays.items() if a is not None]
    print(f"Loaded {len(loaded)} TVLA arrays: {', '.join(loaded)}")
    results = {}

    # per-order metrics
    results["orders"] = {}
    for name, arr in arrays.items():
        if arr is not None:
            results["orders"][name] = compute_metrics(arr)

    # aggregated metrics
    results["aggregate"] = {}
    for name, arr in agg.items():
        results["aggregate"][name] = compute_metrics(arr)

    # save results
    with open(base / "multi_order_summary.json", "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)

    print("\n=== AGGREGATE RESULTS ===")
    for k, v in results["aggregate"].items():
        print(f"\n{k}")
        for kk, vv in v.items():
            print(f"  {kk}: {vv}")

    # plots
    for name, arr in agg.items():
        plot(arr, f"Aggregate: {name}", base / f"agg_{name}.png")

    print("\nSaved:")
    print(" - multi_order_summary.json")
    for name in agg:
        print(f" - agg_{name}.png")


if __name__ == "__main__":
    main()