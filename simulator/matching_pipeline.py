from engine.matching_engine import MatchingEngine
from simulator.market_firehose import MarketFirehose


def run_matching_pipeline(order_count=100):
    firehose = MarketFirehose()
    engine = MatchingEngine()
    trades = []

    for _ in range(order_count):
        order = firehose.generate_order()

        new_trades = engine.process_order(order)
        trades.extend(new_trades)

    return trades


if __name__ == "__main__":
    trades = run_matching_pipeline(100)

    print("Matching pipeline completed.")
    print(f"Trades generated: {len(trades)}")