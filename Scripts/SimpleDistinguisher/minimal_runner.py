import numpy as np

class AttackRunner:
    def __init__(self, distinguisher, metric=None):
        self.distinguisher = distinguisher
        self.metric = metric

    def run(self, traces, *, group_labels=None, windows=None, ctx=None):
        """
        traces: (N, T)
        group_labels: (N,) 0/1
        windows: list of (start, end)
        """

        assert traces.ndim == 2
        N, T = traces.shape

        if windows is None:
            windows = [(0, T)]

        results = []

        for (start, end) in windows:
            X = traces[:, start:end]

            score = self.distinguisher.score(
                X,
                group_labels=group_labels,
                ctx=ctx
            )

            result = {
                "window": (start, end),
                "score": score
            }

            if self.metric is not None:
                metric_out = self.metric.compute(
                    score,
                    true_key=0,   # dummy for now
                    X=X,
                    labels=group_labels
                )
                result["metric"] = metric_out

            results.append(result)

        return results