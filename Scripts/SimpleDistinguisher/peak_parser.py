#!/usr/bin/env python3

import numpy as np

# ----------------------------------------------------------------------------
# Peak Alignment and Scaling Analysis
# ----------------------------------------------------------------------------
#
# Compares peak locations between two TVLA runs (e.g., different trace counts)
# to analyse:
#
#   - Spatial stability of leakage (index alignment across runs)
#   - Growth behaviour of statistical peaks (magnitude scaling)
#
# For each peak in the "low" run:
#   - Finds the nearest peak in the "high" run
#   - Computes distance in samples
#   - Computes ratio of t-values (growth factor)
#
# This helps determine whether observed peaks:
#   - Persist across runs (structure)
#   - Scale with trace count (true leakage behaviour)
#
# Inputs:
#   - Two manually pasted text blocks of peak data:
#       index   t_value   |t|
#
# Outputs:
#   - Per-peak alignment report
#   - Distance statistics
#   - Growth ratio statistics
# ----------------------------------------------------------------------------

# PASTE RAW TEXT HERE
low_run_text = """
# PASTE FIRST RUN HERE
1821       -4.500013    4.500013
"""

high_run_text = """
# PASTE SECOND RUN HERE
"""


#  PARSER 
def parse_text_block(text):
    indices = []
    values = []

    for line in text.strip().split("\n"):
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            idx = int(parts[0])
            val = float(parts[1])
        except ValueError:
            continue
        indices.append(idx)
        values.append(val)

    return np.array(indices), np.array(values)


low_idx, low_val = parse_text_block(low_run_text)
high_idx, high_val = parse_text_block(high_run_text)


#  VALIDATION 
if len(low_idx) == 0:
    raise RuntimeError("No low-run peaks provided")

if len(high_idx) == 0:
    raise RuntimeError("No high-run peaks provided")


#  ANALYSIS 
TOLERANCES = [5, 10, 20, 50]

nearest_distances = []
ratios = []

print("\n=== Peak Matching ===\n")

for i, idx in enumerate(low_idx):
    distances = np.abs(high_idx - idx)
    nearest = np.argmin(distances)

    dist = distances[nearest]
    nearest_distances.append(dist)

    if low_val[i] == 0:
        ratio = np.nan
    else:
        ratio = high_val[nearest] / low_val[i]

    ratios.append(ratio)

    print(
        f"Low idx {idx:6d} → High idx {high_idx[nearest]:6d} | "
        f"dist={dist:3d} | ratio={ratio:.3f}"
    )

nearest_distances = np.array(nearest_distances)
ratios = np.array(ratios)


#SUMMARY 
print("\n=== Summary ===")

print(f"Mean distance:   {np.mean(nearest_distances):.2f}")
print(f"Median distance: {np.median(nearest_distances):.2f}")

for tol in TOLERANCES:
    count = np.sum(nearest_distances <= tol)
    print(f"Within {tol:2d} samples: {count}/{len(nearest_distances)}")

print(f"\nMean growth ratio:   {np.nanmean(ratios):.3f}")
print(f"Median growth ratio: {np.nanmedian(ratios):.3f}")