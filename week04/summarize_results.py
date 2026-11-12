#!/usr/bin/env python3
"""저장된 원본만 읽어 4주차 보고서 집계를 다시 만든다.

실행: python3 week04/summarize_results.py
외부 API 호출·전략 실행·주문은 하지 않는다. 출력은 results/summary/에 저장한다.
총손익에는 슬리피지가 이미 포함된다. 비용 전 손익은 총손익에 실제 체결
기록의 슬리피지를 다시 더해 계산하며, 수수료는 별도로 차감한다.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

WEEK = Path(__file__).resolve().parent
RESULTS = WEEK / "results"
OUT = RESULTS / "summary"
STRATEGIES = ("week04_zf_zn_spread", "week04_z3n_zn_spread")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def close(actual: float, expected: float, label: str):
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-7), label


def write_json(name: str, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict]):
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def local_time(value: str):
    # 원본의 opened_at은 오프셋이 없지만 journal.time과 동일한 KST를 사용한다.
    return datetime.fromisoformat(value).replace(tzinfo=None)


def main():
    provenance = read_json(RESULTS / "provenance.json")
    for entry in provenance["files"]:
        payload = (WEEK / entry["destination"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"], entry["destination"]

    runs, all_trades, costs, sweeps = [], [], [], []
    for strategy in STRATEGIES:
        for meta_path in sorted((RESULTS / strategy).glob("*/*/meta.json")):
            run_dir = meta_path.parent
            meta = read_json(meta_path)
            result = read_json(run_dir / "result.json")
            rows = [row for path in sorted((run_dir / "journal").glob("*.jsonl")) for row in read_jsonl(path)]
            trades = [row for row in rows if row["kind"] == "trade"]
            fills = [row for row in rows if row["kind"] == "fill"]
            decisions = [row for row in rows if row["kind"] == "decision"]
            assert len(trades) == result["trade_count"], meta["run_id"]
            assert sum(row["net_pnl"] > 0 for row in trades) == result["win_count"]
            assert sum(row["net_pnl"] < 0 for row in trades) == result["loss_count"]
            for field in ("gross_pnl", "fee", "net_pnl"):
                close(sum(row[field] for row in trades), result[field], f"{meta['run_id']}: {field}")
            close(sum(row["fee"] for row in fills), result["fee"], "fill fee")
            close(result["gross_pnl"] - result["fee"], result["net_pnl"], "net pnl")
            if "final_equity" in result:
                close(result["initial_capital"] + result["net_pnl"], result["final_equity"], "final equity")
                close(result["net_pnl"] / result["initial_capital"], result["return_rate"], "return rate")

            holding_days = []
            for trade in trades:
                holding = (local_time(trade["time"]) - local_time(trade["opened_at"])).total_seconds() / 86400
                holding_days.append(holding)
                all_trades.append({
                    "strategy_id": strategy, "run_id": meta["run_id"], "mode": meta["mode"],
                    "entry_id": trade["entry_id"], "side": trade["side"], "quantity": trade["quantity"],
                    "opened_at": trade["opened_at"], "closed_at": trade["time"],
                    "entry_price": trade["entry_price"], "exit_price": trade["exit_price"],
                    "gross_pnl": trade["gross_pnl"], "fee": trade["fee"], "net_pnl": trade["net_pnl"],
                    "holding_days": holding,
                })
            multiplier = meta["instrument"]["multiplier"]
            slippage = sum(abs(row["price"] - row["raw_price"]) * row["quantity"] * multiplier for row in fills)
            before_cost = result["gross_pnl"] + slippage
            close(before_cost - slippage - result["fee"], result["net_pnl"], "cost decomposition")
            costs.append({
                "strategy_id": strategy, "run_id": meta["run_id"], "mode": meta["mode"],
                "trade_count": len(trades), "fill_count": len(fills),
                "pnl_before_slippage_and_fee": before_cost, "slippage_cost": slippage,
                "gross_pnl_after_slippage": result["gross_pnl"], "fee": result["fee"],
                "net_pnl": result["net_pnl"], "max_holding_days": max(holding_days, default=0),
            })
            summary = {
                "strategy_id": strategy, "run_id": meta["run_id"], "mode": meta["mode"],
                "source": run_dir.relative_to(WEEK).as_posix(), "params": meta["params"],
                "started_at": meta["started_at"], "ended_at": meta["ended_at"],
                "duration_seconds": (datetime.fromisoformat(meta["ended_at"]) - datetime.fromisoformat(meta["started_at"])).total_seconds(),
                "period": meta.get("period"),
                "summary": {key: value for key, value in result.items() if not isinstance(value, (dict, list))},
                "journal_counts": dict(Counter(row["kind"] for row in rows)),
                "decision_reasons": dict(Counter(row["reason"] for row in decisions)),
                "max_holding_days": max(holding_days, default=0),
            }
            if meta["mode"] == "paper":
                summary["account_changes"] = {key: value for key, value in result["account"].items() if key.endswith("_change")}
                summary["decision_first"] = decisions[0]["time"] if decisions else None
                summary["decision_last"] = decisions[-1]["time"] if decisions else None
                spreads = [row["detail"]["spread"] for row in decisions]
                summary["spread_min"] = min(spreads) if spreads else None
                summary["spread_max"] = max(spreads) if spreads else None
                bands = []
                for row in decisions:
                    band = row["detail"]["band"]
                    if band and band not in bands:
                        bands.append(band)
                summary["bands"] = bands
            runs.append(summary)

        sweep_path = RESULTS / "sweeps" / strategy / "results.jsonl"
        for row in read_jsonl(sweep_path):
            trade_rows = read_jsonl(sweep_path.parent / "trades" / f"{row['id']}.jsonl")
            completed = [trade for trade in trade_rows if trade["kind"] == "trade"]
            assert len(completed) == row["summary"]["trade_count"], row["id"]
            for field in ("gross_pnl", "fee", "net_pnl"):
                close(sum(trade[field] for trade in completed), row["summary"][field], f"{row['id']}: {field}")
            sweeps.append({key: value for key, value in row.items() if key != "daily_equity"})

    OUT.mkdir(parents=True, exist_ok=True)
    write_json("run-summary.json", runs)
    write_csv("trades.csv", all_trades)
    write_json("sweep-summary.json", sweeps)
    write_csv("cost-summary.csv", costs)
    print(f"Verified {len(provenance['files'])} copied files, {len(runs)} runs, {len(all_trades)} trades, {len(sweeps)} sweep results.")
    print("Wrote results/summary/{run-summary.json,trades.csv,sweep-summary.json,cost-summary.csv}")


if __name__ == "__main__":
    main()
