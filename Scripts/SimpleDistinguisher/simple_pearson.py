import numpy as np
# -----------------------------------------------------------------------------
# Simple Pearson Correlation Distinguisher
# -----------------------------------------------------------------------------
#
# Computes a correlation trace between binary group labels and each sample point
# across the trace set. This is used as a model-free distinguisher to test
# whether statistically detected differences correspond to direct linear
# dependence on the fixed-vs-random class labels.
# -----------------------------------------------------------------------------

def pearson(x, y):
    x = x - np.mean(x)
    y = y - np.mean(y)
    denom = np.sqrt(np.sum(x**2) * np.sum(y**2))
    if denom == 0:
        return 0.0
    return np.sum(x * y) / denom


class CorrelationDistinguisher:
    def __init__(self, config=None):
        self.config = config or {}

    @classmethod
    def from_config(cls, config: dict):
        return cls(config=config)

# Compute absolute Pearson correlation independently at each sample index
    def score(self, traces: np.ndarray, group_labels=None, ctx=None, **kwargs):
        """
        traces: (N, T)
        group_labels: (N,) binary labels (fixed vs random)

        returns:
            correlation trace: (T,)
        """

        if group_labels is None:
            raise ValueError("CorrelationDistinguisher requires group_labels")

        predicted = group_labels.astype(np.float32)

        N, T = traces.shape
        corrs = np.zeros(T, dtype=np.float32)

        for t in range(T):
            corrs[t] = abs(pearson(predicted, traces[:, t]))

        return corrs