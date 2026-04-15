#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# OFFLINE TVLA / STATISTICAL ANALYSIS PIPELINE
# -----------------------------------------------------------------------------
#
# This script performs full statistical analysis on previously captured traces,
# supporting both raw binary and NumPy (.npy) formats.
#
# It computes:
#   - First-order TVLA (t1) and variance-based TVLA (t_var)
#   - Higher-order TVLA (t2–t4, group-centered and pooled variants)
#   - Full moment statistics (mean, variance, skewness, kurtosis)
#   - Trace energy statistics and drift behaviour
#   - Threshold crossings and peak locations
#
# Additional features:
#   - Chunked processing for large datasets (memory efficient)
#   - Support for trimmed analysis windows
#   - Automatic dataset parameter extraction from folder naming
#
# Purpose:
#   This script is the core analysis pipeline used to evaluate statistical
#   leakage behaviour and distinguish between true leakage and structured
#   implementation artefacts.
# -----------------------------------------------------------------------------
import argparse
import sys
import json
import math
import pathlib
import re
import pickle
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt


EPS = 1e-20
TVLA_THRESH = 4.5


# -------------------- I/O helpers --------------------

def read_json_if_exists(p: pathlib.Path) -> Optional[dict]:
    if p.exists():
        with p.open("r") as f:
            return json.load(f)
    return None


def write_json(p: pathlib.Path, obj: dict):
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True))
    tmp.replace(p)

def pick_existing(dsdir: pathlib.Path, candidates):
    for name in candidates:
        p = dsdir / name
        if p.exists():
            return p
    return None

def save_npy(p: pathlib.Path, arr: np.ndarray):
    np.save(p, np.asarray(arr, dtype=np.float64))


def is_true_npy(path: pathlib.Path) -> bool:
    # True .npy starts with b"\x93NUMPY"
    try:
        with path.open("rb") as f:
            magic = f.read(6)
        return magic == b"\x93NUMPY"
    except Exception:
        return False


def parse_folder_name(dsdir: pathlib.Path) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Supports both:
      1) <opname>_<opcodehex>_<samples>_<ntraces>
         e.g. iota_33_5000_100000
      2) <opname>_cmd<opcodehex>_S<samples>_N<ntraces>_run<k>
         e.g. chi_cmd34_S140000_N100000_run1

    Returns (opcode_int, samples, ntraces) or (None,None,None) if no match.
    """
    name = dsdir.name

    # old style
    m = re.match(r"^[A-Za-z0-9]+_([0-9A-Fa-f]{2})_(\d+)_(\d+)$", name)
    if m:
        return (int(m.group(1), 16), int(m.group(2)), int(m.group(3)))

    # new style
    m = re.match(r"^[A-Za-z0-9]+_cmd([0-9A-Fa-f]{2})_S(\d+)_N(\d+)(?:_run\d+)?$", name)
    if m:
        return (int(m.group(1), 16), int(m.group(2)), int(m.group(3)))

    return (None, None, None)



def validate_raw_sizes(traces_path: pathlib.Path, labels_path: pathlib.Path,
                       ntraces: int, samples: int,
                       traces_dtype: np.dtype, labels_dtype: np.dtype):
    t_bytes = traces_path.stat().st_size
    l_bytes = labels_path.stat().st_size

    expect_t = int(ntraces) * int(samples) * int(np.dtype(traces_dtype).itemsize)
    expect_l = int(ntraces) * int(np.dtype(labels_dtype).itemsize)

    if t_bytes < expect_t:
        raise RuntimeError(
            f"traces file too small: {t_bytes} bytes, expected at least {expect_t} "
            f"(N={ntraces}, S={samples}, dtype={traces_dtype})"
        )
    if t_bytes != expect_t:
        # allow exact mismatch only if user wants; otherwise warn hard
        raise RuntimeError(
            f"traces file size mismatch: {t_bytes} bytes, expected exactly {expect_t} "
            f"(N={ntraces}, S={samples}, dtype={traces_dtype}). "
            f"If your file includes padding/headers or multiple blocks, this must be handled explicitly."
        )

    if l_bytes < expect_l:
        raise RuntimeError(
            f"labels file too small: {l_bytes} bytes, expected at least {expect_l} "
            f"(N={ntraces}, dtype={labels_dtype})"
        )
    if l_bytes != expect_l:
        raise RuntimeError(
            f"labels file size mismatch: {l_bytes} bytes, expected exactly {expect_l} "
            f"(N={ntraces}, dtype={labels_dtype})."
        )


# -------------------- math helpers --------------------

def centered_moment_from_raw(m: Dict[int, np.ndarray], c: np.ndarray, k: int) -> np.ndarray:
    # mu_k = E[(X-c)^k] = sum_{j=0..k} C(k,j) (-c)^(k-j) E[X^j]
    out = np.zeros_like(c, dtype=np.float64)
    for j in range(k + 1):
        out += math.comb(k, j) * ((-c) ** (k - j)) * m[j]
    return out


def centered_moment_2k_from_raw(m: Dict[int, np.ndarray], c: np.ndarray, k: int) -> np.ndarray:
    kk = 2 * k
    out = np.zeros_like(c, dtype=np.float64)
    for j in range(kk + 1):
        out += math.comb(kk, j) * ((-c) ** (kk - j)) * m[j]
    return out


def welch_t(E0: np.ndarray, E1: np.ndarray, V0: np.ndarray, V1: np.ndarray, n0: int, n1: int) -> np.ndarray:
    V0 = np.clip(V0, EPS, None)
    V1 = np.clip(V1, EPS, None)
    return (E0 - E1) / np.sqrt(V0 / n0 + V1 / n1 + 1e-12)


def max_abs_and_argmax(arr: np.ndarray) -> Tuple[float, int]:
    a = np.abs(arr)
    idx = int(np.nanargmax(a))
    return float(a[idx]), idx


def crossings(arr: np.ndarray, thresh: float) -> np.ndarray:
    idx = np.where(np.abs(arr) >= thresh)[0]
    if idx.size == 0:
        return np.zeros((0, 3), dtype=np.float64)
    vals = arr[idx]
    out = np.zeros((idx.size, 3), dtype=np.float64)
    out[:, 0] = idx.astype(np.float64)
    out[:, 1] = vals
    out[:, 2] = np.abs(vals)
    out = out[np.argsort(-out[:, 2])]  # sort by descending |t|
    return out


def save_crossings_csv(path: pathlib.Path, name: str, cross: np.ndarray):
    with path.open("w") as f:
        f.write("name,index,t_value,abs_t\n")
        for row in cross:
            f.write(f"{name},{int(row[0])},{row[1]:.12g},{row[2]:.12g}\n")


def plot_tvla(outdir: pathlib.Path, name: str, t: np.ndarray, first_n: int = 2000, thresh: float = TVLA_THRESH):
    plt.figure()
    plt.plot(t)
    plt.axhline(+thresh, linestyle=":")
    plt.axhline(-thresh, linestyle=":")
    plt.title(f"{name} (full)")
    plt.xlabel("sample index")
    plt.ylabel("t value")
    plt.tight_layout()
    plt.savefig(outdir / f"{name}_full.png", dpi=150)
    plt.close()

    n = min(int(first_n), t.shape[0])
    plt.figure()
    plt.plot(t[:n])
    plt.axhline(+thresh, linestyle=":")
    plt.axhline(-thresh, linestyle=":")
    plt.title(f"{name} (first {n} samples)")
    plt.xlabel("sample index")
    plt.ylabel("t value")
    plt.tight_layout()
    plt.savefig(outdir / f"{name}_first{n}.png", dpi=150)
    plt.close()


# -------------------- accumulators --------------------

@dataclass
class Accum:
    sums: list   # sums[k] for k=1..8; sums[0] unused (kept for indexing)
    n: int

    # energy stats
    e_sum: float
    e_sum2: float
    e_min: float
    e_max: float

    def to_moments(self) -> Dict[int, np.ndarray]:
        m = {0: np.ones_like(self.sums[1], dtype=np.float64)}
        for k in range(1, 9):
            m[k] = self.sums[k] / float(self.n)
        return m


# -------------------- core analysis --------------------

def open_traces_and_labels(dsdir: pathlib.Path,
                           traces_dtype: str,
                           labels_dtype: str,
                           samples: Optional[int],
                           ntraces: Optional[int]) -> Tuple[np.ndarray, np.ndarray, int, int, dict]:
    """
    Returns (traces, labels, N, S, format_info)

    Supports mixed formats:
      - traces can be true .npy OR raw binary blob
      - labels can be true .npy OR raw binary blob

    Raw mode requires N and S (from folder name or CLI overrides).
    """
    traces_path = pick_existing(dsdir, ["traces.npy", "traces.dat", "traces.bin"])
    labels_path = pick_existing(dsdir, ["labels.npy", "labels.dat", "labels.bin"])
    if traces_path is None:
        raise RuntimeError(f"Missing traces file (expected one of traces.npy/traces.dat/traces.bin) in {dsdir}")
    if labels_path is None:
        raise RuntimeError(f"Missing labels file (expected one of labels.npy/labels.dat/labels.bin) in {dsdir}")


    meta = read_json_if_exists(dsdir / "meta.json") or {}
    opcode, s_from_name, n_from_name = parse_folder_name(dsdir)

    td = np.dtype(traces_dtype)
    ld = np.dtype(labels_dtype)

    # --- open traces ---
    traces_is_npy = (traces_path.suffix == ".npy") and is_true_npy(traces_path)
    if traces_is_npy:
        traces = np.load(traces_path, mmap_mode="r")
        if traces.ndim != 2:
            raise RuntimeError(f"True-npy traces must be 2D (N,S). Got {traces.shape}")
        N_t, S_t = int(traces.shape[0]), int(traces.shape[1])
    else:
        # need N,S for raw traces
        S_t = samples if samples is not None else s_from_name
        N_t = ntraces if ntraces is not None else n_from_name
        if S_t is None or N_t is None:
            raise RuntimeError(
                "Raw traces require samples and ntraces (folder name <op>_<opcode>_<samples>_<ntraces> "
                "or pass --samples/--ntraces)."
            )
        # validate traces size exactly
        t_bytes = traces_path.stat().st_size
        expect_t = int(N_t) * int(S_t) * int(td.itemsize)
        if t_bytes != expect_t:
            raise RuntimeError(
                f"traces raw size mismatch: {t_bytes} bytes, expected {expect_t} "
                f"(N={N_t}, S={S_t}, dtype={td})"
            )
        traces = np.memmap(traces_path, dtype=td, mode="r", shape=(int(N_t), int(S_t)))

    # --- open labels ---
    labels_is_npy = (labels_path.suffix == ".npy") and is_true_npy(labels_path)
    if labels_is_npy:
        labels = np.load(labels_path, mmap_mode="r")
        if labels.ndim != 1:
            raise RuntimeError(f"True-npy labels must be 1D (N,). Got {labels.shape}")
        N_l = int(labels.shape[0])
    else:
        # need N for raw labels. Prefer N from traces if available.
        if traces_is_npy:
            N_l = int(traces.shape[0])
        else:
            N_l = int(N_t)
        l_bytes = labels_path.stat().st_size
        expect_l = int(N_l) * int(ld.itemsize)
        if l_bytes != expect_l:
            raise RuntimeError(
                f"labels raw size mismatch: {l_bytes} bytes, expected {expect_l} "
                f"(N={N_l}, dtype={ld})"
            )
        labels = np.memmap(labels_path, dtype=ld, mode="r", shape=(int(N_l),))

    # --- reconcile N,S ---
    if traces.shape[0] != labels.shape[0]:
        raise RuntimeError(
            f"N mismatch: traces N={traces.shape[0]} vs labels N={labels.shape[0]}"
        )
    N = int(traces.shape[0])
    S = int(traces.shape[1])

    return traces, labels, N, S, {
        "format": {
            "traces": "true_npy" if traces_is_npy else "raw_binary",
            "labels": "true_npy" if labels_is_npy else "raw_binary",
        },
        "opcode": opcode,
        "samples": S,
        "ntraces": N,
        "traces_dtype": str(traces.dtype),
        "labels_dtype": str(labels.dtype),
        "meta": meta,
    }

def analyze_dataset(dsdir: pathlib.Path,
                    outdir: pathlib.Path,
                    chunk_traces: int,
                    fixed_label: int,
                    traces_dtype: str,
                    labels_dtype: str,
                    random_label: Optional[int],
                    samples: Optional[int],
                    ntraces: Optional[int],
                    start_sample: int,
                    end_sample: Optional[int],
                    save_energy_series: bool) -> dict:

    outdir.mkdir(parents=True, exist_ok=True)

    traces, labels, N, S, fmtinfo = open_traces_and_labels(
        dsdir,
        traces_dtype=traces_dtype,
        labels_dtype=labels_dtype,
        samples=samples,
        ntraces=ntraces,
    )
    # ---- sample trimming ----
    start_sample = int(start_sample)
    if end_sample is None:
        end_sample = S
    end_sample = int(end_sample)

    if not (0 <= start_sample < end_sample <= S):
        raise RuntimeError(
            f"Invalid sample window [{start_sample}:{end_sample}] for trace length S={S}"
        )

    # record original + effective sample window
    fmtinfo["sample_window"] = {
        "start_sample": start_sample,
        "end_sample": end_sample,
        "original_S": int(S),
        "effective_S": int(end_sample - start_sample),
    }

    # effective number of samples after trimming
    S_eff = end_sample - start_sample


    labels_i = np.asarray(labels, dtype=np.int64)
    fixed_label = int(fixed_label)

    uniq = np.unique(labels_i)
    binary = (uniq.size <= 2) and np.all(np.isin(uniq, [0, 1]))

    if random_label is None:
        if binary:
            random_label = 1 - fixed_label
        else:
            raise RuntimeError(
                f"Non-binary labels detected: {uniq[:16]}{'...' if uniq.size>16 else ''}. "
                f"Provide --random-label explicitly."
            )
    random_label = int(random_label)

    idxF = np.where(labels_i == fixed_label)[0]
    idxR = np.where(labels_i == random_label)[0]

    if idxF.size < 2:
        raise RuntimeError(f"Need >=2 FIXED traces. fixed_label={fixed_label}, count={idxF.size}")
    if idxR.size < 2:
        raise RuntimeError(f"Need >=2 RANDOM traces. random_label={random_label}, count={idxR.size}")

    nF = int(idxF.size)
    nR = int(idxR.size)

    # Drift series (global scalar per trace, in capture order)
    
    global_mean_series_full = np.zeros((N,), dtype=np.float64)
    global_var_series_full  = np.zeros((N,), dtype=np.float64)
    global_mean_series_win  = np.zeros((N,), dtype=np.float64)
    global_var_series_win   = np.zeros((N,), dtype=np.float64)
    global_energy_series = np.zeros((N,), dtype=np.float64) if save_energy_series else None

    # Power sums
    sumsF = [np.zeros((S_eff,), dtype=np.float64) for _ in range(9)]
    sumsR = [np.zeros((S_eff,), dtype=np.float64) for _ in range(9)]


    # Energy stats accum
    e_sum_F = e_sum2_F = 0.0
    e_sum_R = e_sum2_R = 0.0
    e_min_F = float("inf");  e_max_F = float("-inf")
    e_min_R = float("inf");  e_max_R = float("-inf")

    # Chunked processing
    n_chunks = (N + chunk_traces - 1) // chunk_traces
    disable_bar = not sys.stderr.isatty()
    
    for start in tqdm(
        range(0, N, chunk_traces),
        total=n_chunks,
        desc="Processing chunks",
        unit="chunk",
        file=sys.stderr,
        dynamic_ncols=True,
        ascii=True,
        mininterval=0.2,
        disable=disable_bar,
        leave=True,
    ):
        end = min(N, start + chunk_traces)

        # Full chunk for drift/energy
        x_full = np.asarray(traces[start:end, :], dtype=np.float64)  # (B,S)
        if not np.isfinite(x_full).all():
            raise RuntimeError(f"Non-finite values (NaN/Inf) in traces chunk {start}:{end}")
        y = labels_i[start:end]
        
        # Trimmed window used only for TVLA/stat sums
        x = x_full[:, start_sample:end_sample]  # (B, S_eff)


        # Drift on full trace
        mu_full = x_full.mean(axis=1)
        va_full = x_full.var(axis=1, ddof=1)
        global_mean_series_full[start:end] = mu_full
        global_var_series_full[start:end]  = va_full

        # window
        mu_win = x.mean(axis=1)
        va_win = x.var(axis=1, ddof=1)
        global_mean_series_win[start:end] = mu_win
        global_var_series_win[start:end]  = va_win


        # Energy on full trace
        en = np.einsum("ij,ij->i", x_full, x_full)
        if global_energy_series is not None:
            global_energy_series[start:end] = en

        mF = (y == fixed_label)
        mR = (y == random_label)

        if np.any(mF):
            enF = en[mF]
            e_sum_F  += float(enF.sum())
            e_sum2_F += float(np.dot(enF, enF))
            e_min_F = min(e_min_F, float(enF.min()))
            e_max_F = max(e_max_F, float(enF.max()))

        if np.any(mR):
            enR = en[mR]
            e_sum_R  += float(enR.sum())
            e_sum2_R += float(np.dot(enR, enR))
            e_min_R = min(e_min_R, float(enR.min()))
            e_max_R = max(e_max_R, float(enR.max()))
        # Accumulate raw powers (X, X^2, ..., X^8) for moment-based TVLA computation
        p = np.ones_like(x, dtype=np.float64)
        for k in range(1, 9):
            p *= x
            if np.any(mF):
                sumsF[k] += p[mF].sum(axis=0)
            if np.any(mR):
                sumsR[k] += p[mR].sum(axis=0)

    accF = Accum(sums=sumsF, n=nF, e_sum=e_sum_F, e_sum2=e_sum2_F, e_min=e_min_F, e_max=e_max_F)
    accR = Accum(sums=sumsR, n=nR, e_sum=e_sum_R, e_sum2=e_sum2_R, e_min=e_min_R, e_max=e_max_R)

    mF = accF.to_moments()
    mR = accR.to_moments()

    mean_fixed  = mF[1]
    mean_random = mR[1]
    delta_mu = mean_fixed - mean_random

    var_fixed_raw  = (sumsF[2] - nF * mean_fixed**2) / (nF - 1)
    var_random_raw = (sumsR[2] - nR * mean_random**2) / (nR - 1)
    var_fixed  = np.clip(var_fixed_raw, EPS, None)
    var_random = np.clip(var_random_raw, EPS, None)

    Ntot = nF + nR
    sum1_total = sumsF[1] + sumsR[1]
    sum2_total = sumsF[2] + sumsR[2]
    mu_total = sum1_total / float(Ntot)
    pooled_var = np.clip((sum2_total - Ntot * mu_total**2) / (Ntot - 1), EPS, None)

    rms_fixed  = np.sqrt(np.clip(mF[2], 0.0, None))
    rms_random = np.sqrt(np.clip(mR[2], 0.0, None))

    mu2F = np.clip(centered_moment_from_raw(mF, mean_fixed, 2), EPS, None)
    mu3F = centered_moment_from_raw(mF, mean_fixed, 3)
    mu4F = centered_moment_from_raw(mF, mean_fixed, 4)

    mu2R = np.clip(centered_moment_from_raw(mR, mean_random, 2), EPS, None)
    mu3R = centered_moment_from_raw(mR, mean_random, 3)
    mu4R = centered_moment_from_raw(mR, mean_random, 4)

    skew_fixed  = mu3F / (mu2F ** 1.5)
    skew_random = mu3R / (mu2R ** 1.5)
    kurt_fixed  = mu4F / (mu2F ** 2)
    kurt_random = mu4R / (mu2R ** 2)

    t1 = welch_t(mean_fixed, mean_random, var_fixed, var_random, nF, nR)

    t_var = (var_fixed - var_random) / np.sqrt(
        (2.0 * (var_fixed**2)) / (nF - 1) +
        (2.0 * (var_random**2)) / (nR - 1) + 1e-12
    )

    mu_pooled = (sumsF[1] + sumsR[1]) / float(Ntot)

    t_group = {}
    t_pooled = {}
    # Group-centered vs pooled-centered higher-order statistics
    # (tests sensitivity to centering choice in higher-order TVLA)
    for k in (2, 3, 4):
        E0  = centered_moment_from_raw(mF, mean_fixed, k)
        E1  = centered_moment_from_raw(mR, mean_random, k)
        E20 = centered_moment_2k_from_raw(mF, mean_fixed, k)
        E21 = centered_moment_2k_from_raw(mR, mean_random, k)
        V0  = np.clip(E20 - E0**2, EPS, None)
        V1  = np.clip(E21 - E1**2, EPS, None)
        t_group[k] = welch_t(E0, E1, V0, V1, nF, nR)

        E0p  = centered_moment_from_raw(mF, mu_pooled, k)
        E1p  = centered_moment_from_raw(mR, mu_pooled, k)
        E20p = centered_moment_2k_from_raw(mF, mu_pooled, k)
        E21p = centered_moment_2k_from_raw(mR, mu_pooled, k)
        V0p  = np.clip(E20p - E0p**2, EPS, None)
        V1p  = np.clip(E21p - E1p**2, EPS, None)
        t_pooled[k] = welch_t(E0p, E1p, V0p, V1p, nF, nR)

    # ---------------- save arrays ----------------
    save_npy(outdir / "mean_fixed.npy", mean_fixed)
    save_npy(outdir / "mean_random.npy", mean_random)
    save_npy(outdir / "delta_mu.npy", delta_mu)

    save_npy(outdir / "var_fixed.npy", var_fixed)
    save_npy(outdir / "var_random.npy", var_random)
    save_npy(outdir / "var_fixed_raw.npy", var_fixed_raw)
    save_npy(outdir / "var_random_raw.npy", var_random_raw)

    save_npy(outdir / "pooled_var.npy", pooled_var)

    save_npy(outdir / "rms_fixed.npy", rms_fixed)
    save_npy(outdir / "rms_random.npy", rms_random)
    save_npy(outdir / "skew_fixed.npy", skew_fixed)
    save_npy(outdir / "skew_random.npy", skew_random)
    save_npy(outdir / "kurt_fixed.npy", kurt_fixed)
    save_npy(outdir / "kurt_random.npy", kurt_random)

    save_npy(outdir / "t1.npy", t1)
    save_npy(outdir / "t_var.npy", t_var)
    for k in (2, 3, 4):
        save_npy(outdir / f"t{k}_group.npy", t_group[k])
        save_npy(outdir / f"t{k}.npy", t_pooled[k])

    save_npy(outdir / "global_mean_series_full.npy", global_mean_series_full)
    save_npy(outdir / "global_var_series_full.npy",  global_var_series_full)
    save_npy(outdir / "global_mean_series_win.npy",  global_mean_series_win)
    save_npy(outdir / "global_var_series_win.npy",   global_var_series_win)

    if global_energy_series is not None:
        save_npy(outdir / "global_energy_series.npy", global_energy_series)

    # ---------------- plots ----------------
    plot_tvla(outdir, "t1", t1, first_n=2000, thresh=TVLA_THRESH)
    plot_tvla(outdir, "t_var", t_var, first_n=2000, thresh=TVLA_THRESH)
    for k in (2, 3, 4):
        plot_tvla(outdir, f"t{k}_group", t_group[k], first_n=2000, thresh=TVLA_THRESH)
        plot_tvla(outdir, f"t{k}", t_pooled[k], first_n=2000, thresh=TVLA_THRESH)

    plt.figure()
    plt.plot(global_mean_series_full)
    plt.title("Global per-trace mean (full trace)")
    plt.xlabel("trace index")
    plt.ylabel("mean(trace)")
    plt.tight_layout()
    plt.savefig(outdir / "global_mean_series_full.png", dpi=150)
    plt.close()
    
    plt.figure()
    plt.plot(global_mean_series_win)
    plt.title("Global per-trace mean (trimmed window)")
    plt.xlabel("trace index")
    plt.ylabel("mean(trace)")
    plt.tight_layout()
    plt.savefig(outdir / "global_mean_series_win.png", dpi=150)
    plt.close()

    plt.figure()
    plt.plot(global_var_series_full)
    plt.title("Global per-trace variance (full trace)")
    plt.xlabel("trace index")
    plt.ylabel("var(trace)")
    plt.tight_layout()
    plt.savefig(outdir / "global_var_series_full.png", dpi=150)
    plt.close()
    
    plt.figure()
    plt.plot(global_var_series_win)
    plt.title("Global per-trace variance (trimmed window)")
    plt.xlabel("trace index")
    plt.ylabel("var(trace)")
    plt.tight_layout()
    plt.savefig(outdir / "global_var_series_win.png", dpi=150)
    plt.close()

    # energy stats json
    def energy_stats(es, es2, n, emin, emax):
        meanE = es / n
        varE = max(es2 / n - meanE * meanE, 0.0)
        return dict(n=int(n), mean=float(meanE), std=float(math.sqrt(varE)), min=float(emin), max=float(emax))

    trace_energy_stats = dict(
        energy_definition="sum(trace^2)",
        fixed=energy_stats(accF.e_sum, accF.e_sum2, accF.n, accF.e_min, accF.e_max),
        random=energy_stats(accR.e_sum, accR.e_sum2, accR.n, accR.e_min, accR.e_max),
    )
    write_json(outdir / "trace_energy_stats.json", trace_energy_stats)

    # peaks + crossings
    t_peaks = {}
    for name, arr in [
        ("t1", t1),
        ("t_var", t_var),
        ("t2_group", t_group[2]),
        ("t2", t_pooled[2]),
        ("t3_group", t_group[3]),
        ("t3", t_pooled[3]),
        ("t4_group", t_group[4]),
        ("t4", t_pooled[4]),
    ]:
        m, ix = max_abs_and_argmax(arr)
        t_peaks[name] = dict(max_abs=m, index=int(ix))
    write_json(outdir / "t_peaks.json", t_peaks)

    crossings_dir = outdir / "crossings"
    crossings_dir.mkdir(parents=True, exist_ok=True)
    all_crossings = {}

    for name, arr in [
        ("t1", t1),
        ("t_var", t_var),
        ("t2_group", t_group[2]),
        ("t2", t_pooled[2]),
        ("t3_group", t_group[3]),
        ("t3", t_pooled[3]),
        ("t4_group", t_group[4]),
        ("t4", t_pooled[4]),
    ]:
        # Extract threshold crossings (|t| >= threshold) for leakage localisation
        c = crossings(arr, TVLA_THRESH)
        all_crossings[name] = dict(
            count=int(c.shape[0]),
            top_10=[dict(index=int(r[0]), t_value=float(r[1]), abs_t=float(r[2])) for r in c[:10]],
        )
        save_crossings_csv(crossings_dir / f"{name}_crossings.csv", name, c)

    write_json(outdir / "crossings_summary.json", all_crossings)

    report = dict(
        format=fmtinfo,
        input=dict(
            dataset_dir=str(dsdir),
            N=int(N),
            S=int(S_eff),
            n_fixed=int(nF),
            n_random=int(nR),
            fixed_label=int(fixed_label),
            random_label=int(random_label) if random_label is not None else "!=fixed_label",
            traces_dtype=str(traces.dtype),
            labels_dtype=str(labels.dtype),
        ),
        tvla=dict(
            threshold=float(TVLA_THRESH),
            t_peaks=t_peaks,
            crossings=all_crossings,
        ),
        energy=trace_energy_stats,
    )
    with (outdir / "final_raw_sums.pkl").open("wb") as f:
        pickle.dump(
            dict(sumsF=sumsF, sumsR=sumsR, nF=nF, nR=nR),
            f,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    write_json(outdir / "report.json", report)
    return report


def main():
    ap = argparse.ArgumentParser(description="Offline TVLA/stats from traces.npy + labels.npy (raw or true-npy).")
    ap.add_argument("dataset_dir", type=str, help="Directory containing traces.npy and labels.npy")
    ap.add_argument("--out", type=str, default=None, help="Output directory (default: <dataset_dir>/analysis_out)")
    ap.add_argument("--chunk", type=int, default=256, help="Traces per chunk (memory/speed tradeoff)")
    ap.add_argument("--start-sample", type=int, default=0, help="Start sample index (inclusive). Default: 0")
    ap.add_argument("--end-sample", type=int, default=None, help="End sample index (exclusive). Default: full trace length")
    ap.add_argument("--fixed-label", type=int, default=0, help="Label value that means FIXED group (default: 0)")
    ap.add_argument("--random-label", type=int, default=None, help="Label value that means RANDOM group. Required if labels are not binary {0,1}.")
    ap.add_argument("--traces-dtype", type=str, default="float32", help="Raw traces dtype (default: float32)")
    ap.add_argument("--labels-dtype", type=str, default="uint8", help="Raw labels dtype (default: uint8)")
    ap.add_argument("--samples", type=int, default=None, help="Override samples per trace (raw mode)")
    ap.add_argument("--ntraces", type=int, default=None, help="Override number of traces (raw mode)")
    ap.add_argument("--save-energy-series", action="store_true", help="Also save global_energy_series.npy (large)")
    args = ap.parse_args()

    dsdir = pathlib.Path(args.dataset_dir).expanduser().resolve()
    if not dsdir.exists():
        raise SystemExit(f"Missing dataset_dir: {dsdir}")

    outdir = pathlib.Path(args.out).expanduser().resolve() if args.out else (dsdir / "analysis_out")
    outdir.mkdir(parents=True, exist_ok=True)

    # copy meta.json if present
    meta = read_json_if_exists(dsdir / "meta.json")
    if meta is not None:
        write_json(outdir / "meta_copy.json", meta)

    report = analyze_dataset(
        dsdir=dsdir,
        outdir=outdir,
        chunk_traces=int(args.chunk),
        fixed_label=int(args.fixed_label),
        traces_dtype=str(args.traces_dtype),
        labels_dtype=str(args.labels_dtype),
        random_label=args.random_label,
        samples=args.samples,
        ntraces=args.ntraces,
        start_sample=int(args.start_sample),
        end_sample=args.end_sample,
        save_energy_series=bool(args.save_energy_series),
    )


    print("Wrote analysis to:", str(outdir))
    print("Key peaks:", json.dumps(report["tvla"]["t_peaks"], indent=2))


if __name__ == "__main__":
    main()
