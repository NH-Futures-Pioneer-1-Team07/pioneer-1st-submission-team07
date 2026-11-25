"""Rebuild the report's CSV from the archived backtest records."""

import csv
import json
import math
import sys
import tarfile
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
STRATEGY_MARGIN_PER_CONTRACT = 2083
COMPARISON_MARGIN_PER_CONTRACT = 1875


def journal_rows(run):
    with tarfile.open(run / "journal.tar.gz", "r:gz") as archive:
        for member in sorted(archive.getmembers(), key=lambda file: file.name):
            with archive.extractfile(member) as entries:
                yield from map(json.loads, entries)


def summarize(run):
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
    result = json.loads((run / "result.json").read_text(encoding="utf-8"))
    capital = result["initial_capital"]
    equity = [capital, *(point["equity"] for point in result["equity_curve"])]
    daily_returns = [current / previous - 1 for previous, current in zip(equity, equity[1:])]
    downside_volatility = math.sqrt(sum(min(change, 0) ** 2 for change in daily_returns) / len(daily_returns))

    position = max_position = 0
    realized_pnl = paid_fees = 0.0
    min_margin_adjusted_equity = capital
    for row in sorted(journal_rows(run), key=lambda entry: entry["seq"]):
        if row["kind"] == "fill":
            position += row["quantity"] if row["side"] == "buy" else -row["quantity"]
            max_position = max(max_position, abs(position))
            paid_fees += row["fee"]
        elif row["kind"] == "trade":
            realized_pnl += row["gross_pnl"]
        elif row["kind"] == "decision":
            today = row["detail"]["today"]
            holding = today["holding"]
            unrealized_pnl = (today["pnl_ratio"] or 0) * STRATEGY_MARGIN_PER_CONTRACT * holding
            margin_adjusted_equity = (
                capital + realized_pnl - paid_fees + unrealized_pnl - COMPARISON_MARGIN_PER_CONTRACT * holding
            )
            min_margin_adjusted_equity = min(min_margin_adjusted_equity, margin_adjusted_equity)

    return {
        "strategy_id": meta["strategy_id"],
        "run_id": meta["run_id"],
        "exit_threshold_pct": round(100 * meta["params"]["profit_loss_rate"]),
        "net_pnl_usd": f"{result['net_pnl']:.2f}",
        "return_pct": f"{100 * result['return_rate']:.2f}",
        "trade_count": result["trade_count"],
        "fee_usd": f"{result['fee']:.2f}",
        "max_drawdown_usd": f"{result['max_drawdown']:.2f}",
        "max_drawdown_pct": f"{100 * result['max_drawdown_rate']:.2f}",
        "downside_volatility_pct": f"{100 * downside_volatility:.2f}",
        "worst_daily_return_pct": f"{100 * min(daily_returns):.2f}",
        "max_position_contracts": max_position,
        "min_margin_adjusted_equity_usd": f"{min_margin_adjusted_equity:.0f}",
    }


def main():
    rows = [summarize(run) for run in RESULTS.iterdir() if run.is_dir()]
    rows.sort(key=lambda row: (row["strategy_id"], row["exit_threshold_pct"]))
    writer = csv.DictWriter(sys.stdout, fieldnames=rows[0], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
