import statistics
import subprocess
import sys
import re


RUNS = 5


def run_benchmark():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmarks.benchmark_process_matching",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    output = result.stdout

    throughput_match = re.search(
        r"Throughput:\s*([\d.]+)",
        output,
    )

    latency_match = re.search(
        r"Average latency:\s*([\d.]+)",
        output,
    )

    orders_match = re.search(
        r"Orders processed:\s*(\d+)",
        output,
    )

    trades_match = re.search(
        r"Trades generated:\s*(\d+)",
        output,
    )

    if not all(
        [
            throughput_match,
            latency_match,
            orders_match,
            trades_match,
        ]
    ):
        raise RuntimeError(
            "Could not parse benchmark output:\n"
            + output
        )

    return {
        "throughput": float(
            throughput_match.group(1)
        ),
        "latency": float(
            latency_match.group(1)
        ),
        "orders": int(
            orders_match.group(1)
        ),
        "trades": int(
            trades_match.group(1)
        ),
    }


def main():
    results = []

    print("=== Week 3 Metrics Baseline ===")
    print()
    print(f"Running {RUNS} benchmark runs...")
    print()

    for run_number in range(1, RUNS + 1):
        result = run_benchmark()
        results.append(result)

        print(
            f"Run {run_number}: "
            f"{result['throughput']:.2f} orders/sec | "
            f"{result['latency']:.3f} us"
        )

    throughputs = [
        result["throughput"]
        for result in results
    ]

    latencies = [
        result["latency"]
        for result in results
    ]

    print()
    print("=== Baseline Summary ===")
    print()
    print(
        f"Orders processed : "
        f"{results[0]['orders']}"
    )

    print(
        f"Trades generated : "
        f"{results[0]['trades']}"
    )

    print()
    print(
        f"Average throughput: "
        f"{statistics.mean(throughputs):.2f} orders/sec"
    )

    print(
        f"Best throughput   : "
        f"{max(throughputs):.2f} orders/sec"
    )

    print(
        f"Average latency   : "
        f"{statistics.mean(latencies):.3f} us"
    )

    print(
        f"Best latency      : "
        f"{min(latencies):.3f} us"
    )

    print()
    print("Baseline measurement completed.")


if __name__ == "__main__":
    main()
