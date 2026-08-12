from simulator.matching_pipeline import run_matching_pipeline


def test_matching_pipeline_runs():
    trades = run_matching_pipeline(100)

    assert isinstance(trades, list)


def test_matching_pipeline_trade_objects():
    trades = run_matching_pipeline(100)

    for trade in trades:
        assert trade.buy_order_id > 0
        assert trade.sell_order_id > 0
        assert trade.price > 0
        assert trade.quantity > 0