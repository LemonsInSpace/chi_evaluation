import numpy as np
import os
import sys
# -----------------------------------------------------------------------------
# TVLA Crossing Extraction Utility
# -----------------------------------------------------------------------------
#
# This script loads precomputed TVLA statistics (t1–t4 and grouped variants)
# and extracts all sample indices where |t| exceeds a given threshold.
#
# It reports:
#   - Total number of crossings per statistic
#   - Sorted list of crossings by magnitude
#
# Purpose:
#   Provides a direct view of where statistical detection occurs in the trace,
#   enabling comparison between configurations (e.g., correct vs broken masking)
#   and supporting analysis of leakage density and distribution.
#
# Input:
#   - Folder containing .npy files (t1.npy, t2.npy, etc.)
#
# Output:
#   - Console report of crossing locations and magnitudes
# -----------------------------------------------------------------------------
THRESHOLD = 4.5


def list_crossings(arr, name, threshold):
    if arr is None:
        print(f"{name}: not found")
        return

    abs_arr = np.abs(arr)
    # Find indices where |t| exceeds threshold (TVLA detection condition)
    crossing_indices = np.where(abs_arr >= threshold)[0]

    if len(crossing_indices) == 0:
        print(f"\n{name}: No crossings (|t| >= {threshold})")
        return

    print(f"\n{name}: {len(crossing_indices)} crossings (|t| >= {threshold})")

    # Collect data
    entries = []
    for idx in crossing_indices:
        entries.append((idx, arr[idx], abs_arr[idx]))

    # Sort crossings by strength (largest |t| first) for easier inspection
    entries.sort(key=lambda x: x[2], reverse=True)

    print("\nIndex      t-value        |t|")
    print("------------------------------------")
    for idx, tval, absval in entries:
        print(f"{idx:<10d} {tval:<14.6f} {absval:<10.6f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tvla_list_crossings.py <stats_folder> [threshold]")
        sys.exit(1)

    base = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else THRESHOLD

    print("\n=== TVLA Crossing Report ===")
    print("Folder:", base)
    print("Threshold:", threshold)

    t1 = np.load(os.path.join(base, "t1.npy")) if os.path.exists(os.path.join(base, "t1.npy")) else None
    t2 = np.load(os.path.join(base, "t2.npy")) if os.path.exists(os.path.join(base, "t2.npy")) else None
    t2g = np.load(os.path.join(base, "t2_group.npy")) if os.path.exists(os.path.join(base, "t2_group.npy")) else None
    t3 = np.load(os.path.join(base, "t3.npy")) if os.path.exists(os.path.join(base, "t3.npy")) else None
    t3g = np.load(os.path.join(base, "t3_group.npy")) if os.path.exists(os.path.join(base, "t3_group.npy")) else None
    t4 = np.load(os.path.join(base, "t4.npy")) if os.path.exists(os.path.join(base, "t4.npy")) else None
    t4g = np.load(os.path.join(base, "t4_group.npy")) if os.path.exists(os.path.join(base, "t4_group.npy")) else None

    list_crossings(t1, "t1", threshold)
    list_crossings(t2, "t2", threshold)
    list_crossings(t2g, "t2_group", threshold)
    list_crossings(t3, "t3", threshold)
    list_crossings(t3g, "t3_group", threshold)
    list_crossings(t4, "t4", threshold)
    list_crossings(t4g, "t4_group", threshold)


if __name__ == "__main__":
    main()
