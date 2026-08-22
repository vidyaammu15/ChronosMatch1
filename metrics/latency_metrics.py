class LatencyMetrics:
    def __init__(self):
        self.latencies = []

    def record(self, latency_ns):
        self.latencies.append(latency_ns)

    def count(self):
        return len(self.latencies)

    def minimum(self):
        if not self.latencies:
            return 0
        return min(self.latencies)

    def maximum(self):
        if not self.latencies:
            return 0
        return max(self.latencies)

    def average(self):
        if not self.latencies:
            return 0
        return sum(self.latencies) / len(self.latencies)

    def summary(self):
        return {
            "count": self.count(),
            "min_latency_ns": self.minimum(),
            "max_latency_ns": self.maximum(),
            "avg_latency_ns": self.average(),
        }