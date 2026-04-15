import numpy as np
from scipy.stats import ttest_ind

TRACES_PATH = "<PATH>/traces.npy"
LABELS_PATH = "<PATH>/labels.npy"

LEAKAGE_FILE = "<PATH>/peak_indices.npy"

WINDOW_GAP = 8
MAX_WINDOW = 30 
TOP_K = 200  


def load_data():
    traces = np.load(TRACES_PATH)
    labels = np.load(LABELS_PATH)

    uniq = np.unique(labels)
    if set(uniq) == {7, 8}:
        labels = (labels == 8).astype(np.uint8)

    print("Traces:", traces.shape)
    print("Labels:", np.unique(labels))
    return traces, labels


def load_peaks_npy(path, top_k=None):
    indices = np.load(path)

    if top_k is not None:
        indices = indices[:top_k]

    print(f"Loaded {len(indices)} peaks")
    return sorted(indices.tolist())


def build_windows(indices, window_gap=WINDOW_GAP, max_window=MAX_WINDOW):
    if not indices:
        return []

    indices = sorted(indices)
    windows = []
    current = [indices[0]]

    for idx in indices[1:]:
        if idx - current[-1] <= window_gap:
            current.append(idx)
        else:
            windows.append(current)
            current = [idx]

    windows.append(current)

    clipped = []
    for w in windows:
        if len(w) <= max_window:
            clipped.append(w)
        else:
            for i in range(0, len(w), max_window):
                clipped.append(w[i:i + max_window])

    return clipped


def second_order_windows(traces, labels, indices):
    g0 = labels == 0
    g1 = labels == 1

    results = []

    windows = build_windows(indices)
    print(f"\nTotal windows: {len(windows)}")

    for w in windows:
        X = traces[:, w]

        X0 = X[g0]
        X1 = X[g1]

        mu0 = np.mean(X0, axis=0)
        mu1 = np.mean(X1, axis=0)

        Xc0 = X0 - mu0
        Xc1 = X1 - mu1

        for i in range(len(w)):
            feat0 = Xc0[:, i] ** 2
            feat1 = Xc1[:, i] ** 2
            t, _ = ttest_ind(feat0, feat1, equal_var=False)
            results.append(("sq", w[i], abs(t)))

        for i in range(len(w)):
            for j in range(i + 1, len(w)):
                feat0 = Xc0[:, i] * Xc0[:, j]
                feat1 = Xc1[:, i] * Xc1[:, j]
                t, _ = ttest_ind(feat0, feat1, equal_var=False)
                results.append(("cross", (w[i], w[j]), abs(t)))

    return results


def summarize(results, top_n=20):
    results.sort(key=lambda x: x[-1], reverse=True)

    print("\n=== TOP ===")
    for r in results[:top_n]:
        print(r)

    tvals = np.array([r[-1] for r in results], dtype=np.float64)
    print("\n=== GLOBAL ===")
    print("max:", np.max(tvals))
    print("mean:", np.mean(tvals))
    print("median:", np.median(tvals))


def main():
    traces, labels = load_data()
    indices = load_peaks_npy(LEAKAGE_FILE, TOP_K)
    results = second_order_windows(traces, labels, indices)
    summarize(results)


if __name__ == "__main__":
    main()