import re
import sys
from collections import defaultdict

# -----------------------------------------------------------------------------
# TVLA Crossing and Spike Analysis Tool
# -----------------------------------------------------------------------------
#
# This script parses TVLA output logs and extracts threshold crossings
# (|t| > threshold) for further structural analysis.
#
# It provides:
#   - Grouping of consecutive crossings into spike regions
#   - Gap-tolerant clustering of spikes (robust to noise)
#   - Optional periodicity analysis relative to a known execution period
#
# Purpose:
#   Used to distinguish structured, repeating behaviour in traces from
#   isolated statistical fluctuations. In particular, periodic clustering
#   of spikes is used as evidence of deterministic implementation structure
#   rather than random or secret-dependent leakage.
#
# Input:
#   - Text-based TVLA report (index + t-value per crossing)
#
# Output:
#   - Printed summary of spike regions
#   - Optional periodic grouping statistics
# -----------------------------------------------------------------------------

LANE_PERIOD = 1246  # adjust if needed

# Parse TVLA output file and extract crossing indices per statistic
def parse_tvla_file(filepath):
    sections = defaultdict(list)
    current_section = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            # Detect section header like "t1:", "t2_group:", etc.
            m = re.match(r'^(t\d+(_group)?):', line)
            if m:
                current_section = m.group(1)
                continue

            # Detect crossing line: starts with integer index
            m = re.match(r'^(\d+)\s+([-+]?\d+\.\d+)', line)
            if m and current_section is not None:
                index = int(m.group(1))
                sections[current_section].append(index)

    return sections



def report_spikes(sections):
    print("\n=== Spike Regions ===\n")

    for section, indices in sections.items():
        groups = group_with_gap(indices)

        print(f"{section}:")
        print(f"  Total crossings: {len(indices)}")
        print(f"  Total spike regions: {len(groups)}")

        for i, (start, end) in enumerate(groups):
            if start == end:
                print(f"    Spike {i+1}: index {start}")
            else:
                print(f"    Spike {i+1}: {start} → {end}")

        print()

# Group nearby crossings into spike regions allowing small gaps
# (prevents fragmentation due to noise or minor threshold oscillations)
def group_with_gap(indices, max_gap=5):
    """
    Group indices into spike regions.
    A new spike starts only if the gap between
    consecutive indices is > max_gap.
    """
    if not indices:
        return []

    indices = sorted(indices)
    groups = []
    start = indices[0]
    prev = indices[0]

    for idx in indices[1:]:
        if idx - prev <= max_gap:
            prev = idx
        else:
            groups.append((start, prev))
            start = idx
            prev = idx

    groups.append((start, prev))
    return groups

# Group spike locations modulo the Keccak lane execution period
# Used to identify repeating structural patterns in the trace
def group_by_lane_period(indices, lane_period):
    buckets = {}

    for idx in indices:
        rel = idx % lane_period
        key = int(round(rel / 5) * 5)  # round to nearest 5 samples
        buckets.setdefault(key, []).append(idx)

    return buckets

# Analyze periodic structure of spikes by grouping relative to lane period
# Consistent offsets indicate deterministic implementation behaviour
def analyze_spikes(indices):
    buckets = group_by_lane_period(indices, LANE_PERIOD)

    print("\n=== Periodic Spike Grouping (t1) ===\n")
    print(f"Lane period assumed: {LANE_PERIOD}")
    print(f"Unique relative spike locations: {len(buckets)}\n")

    for rel_offset in sorted(buckets.keys()):
        occurrences = buckets[rel_offset]
        print(f"Relative offset ~{rel_offset:4d} : {len(occurrences)} occurrences")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_tvla_crossings.py <tvla_report.txt>")
        sys.exit(1)

    filepath = sys.argv[1]

    sections = parse_tvla_file(filepath)

    report_spikes(sections)

    # Only analyze t1 periodic structure (if present)
    if "t1" in sections:
        analyze_spikes(sections["t1"])
