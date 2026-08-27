import time


class LatencyMetrics:
    def __init__(self):
        self.latencies = []
        self.start_timestamp_ns = 0
        self.end_timestamp_ns = 0
        self.total_orders_processed = 0
        self.total_trades_generated = 0

    def start_timer(self) -> int:
        """Start tracking a simulation/matching session with high-resolution timer."""
        self.start_timestamp_ns = time.perf_counter_ns()
        self.end_timestamp_ns = 0
        return self.start_timestamp_ns

    def stop_timer(self) -> int:
        """Stop tracking session and record end timestamp."""
        self.end_timestamp_ns = time.perf_counter_ns()
        return self.end_timestamp_ns

    def record(self, latency_ns: int):
        """Record an individual trade or order latency measurement."""
        self.latencies.append(latency_ns)
        self.total_trades_generated += 1

    def record_batch(
        self,
        order_count: int,
        trade_count: int,
        start_ns: int,
        end_ns: int,
        avg_latency_ns: float = None,
    ):
        """Record a completed batch matching run."""
        self.start_timestamp_ns = start_ns
        self.end_timestamp_ns = end_ns
        self.total_orders_processed += order_count
        self.total_trades_generated += trade_count

        elapsed_ns = max(1, end_ns - start_ns)
        if avg_latency_ns is not None:
            self.latencies.append(int(avg_latency_ns))
        elif order_count > 0:
            self.latencies.append(int(elapsed_ns / order_count))

    def count(self) -> int:
        return len(self.latencies)

    def minimum(self) -> int:
        if not self.latencies:
            return 0
        return min(self.latencies)

    def maximum(self) -> int:
        if not self.latencies:
            return 0
        return max(self.latencies)

    def average(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def total_processing_time_ns(self) -> int:
        if self.start_timestamp_ns > 0 and self.end_timestamp_ns > self.start_timestamp_ns:
            return self.end_timestamp_ns - self.start_timestamp_ns
        return 0

    def total_processing_time_s(self) -> float:
        return self.total_processing_time_ns() / 1_000_000_000.0

    def throughput(self) -> float:
        duration_s = self.total_processing_time_s()
        if duration_s > 0 and self.total_orders_processed > 0:
            return self.total_orders_processed / duration_s
        return 0.0

    def reset(self):
        self.latencies.clear()
        self.start_timestamp_ns = 0
        self.end_timestamp_ns = 0
        self.total_orders_processed = 0
        self.total_trades_generated = 0

    def summary(self) -> dict:
        total_time_ns = self.total_processing_time_ns()
        total_time_s = self.total_processing_time_s()
        avg_lat = self.average()
        tp = self.throughput()

        return {
            "start_timestamp_ns": self.start_timestamp_ns,
            "end_timestamp_ns": self.end_timestamp_ns,
            "total_processing_time_ns": total_time_ns,
            "total_processing_time_s": total_time_s,
            "avg_latency_ns": avg_lat,
            "throughput_ops": tp,
            "total_orders": self.total_orders_processed,
            "total_trades": self.total_trades_generated,
            "count": self.count(),
            "min_latency_ns": self.minimum(),
            "max_latency_ns": self.maximum(),
        }