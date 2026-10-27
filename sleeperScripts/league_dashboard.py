from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_dashboard() -> List[Dict[str, str]]:
    snapshot = read_csv(DATA_DIR / "sleeper_team_snapshot.csv")
    waiver = read_csv(DATA_DIR / "waiver_and_start_sit.csv")
    trade = read_csv(DATA_DIR / "trade_value_analysis.csv")

    by_team: Dict[Tuple[str, str], Dict[str, List[Dict[str, str]]]] = defaultdict(lambda: {"snapshot": [], "waiver": [], "trade": []})

    for row in snapshot:
        by_team[(row.get("league_name", ""), row.get("team_name", ""))]["snapshot"].append(row)
    for row in waiver:
        by_team[(row.get("league_name", ""), row.get("team_name", ""))]["waiver"].append(row)
    for row in trade:
        by_team[(row.get("league_name", ""), row.get("team_name", ""))]["trade"].append(row)

    dashboard_rows: List[Dict[str, str]] = []
    for (league_name, team_name), payload in sorted(by_team.items()):
        snapshot_rows = payload["snapshot"]
        waiver_rows = payload["waiver"]
        trade_rows = payload["trade"]

        starters = [r for r in snapshot_rows if r.get("starter") == "true"]
        bench = [r for r in snapshot_rows if r.get("starter") != "true"]
        better_starts = [r for r in waiver_rows if r.get("recommendation") in {"upgrade_candidate", "bench_upgrade"}]
        trade_alerts = [r for r in trade_rows if r.get("trade_signal") in {"sell_high", "buy_low", "watch"}]

        dashboard_rows.append({
            "league_name": league_name,
            "team_name": team_name,
            "starter_count": str(len(starters)),
            "bench_count": str(len(bench)),
            "upgrade_candidates": str(len(better_starts)),
            "trade_alerts": str(len(trade_alerts)),
            "top_upgrade": better_starts[0].get("player_name", "") if better_starts else "",
            "top_trade_alert": trade_alerts[0].get("player_name", "") if trade_alerts else "",
            "best_start_sit_summary": "; ".join(f"{r.get('player_name')}:{r.get('recommendation')}" for r in better_starts[:3]),
            "trade_summary": "; ".join(f"{r.get('player_name')}:{r.get('trade_signal')}" for r in trade_alerts[:3]),
        })

    return dashboard_rows


def main() -> None:
    rows = build_dashboard()
    output = DATA_DIR / "league_dashboard.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "league_name",
            "team_name",
            "starter_count",
            "bench_count",
            "upgrade_candidates",
            "trade_alerts",
            "top_upgrade",
            "top_trade_alert",
            "best_start_sit_summary",
            "trade_summary",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} team dashboard rows to {output}")


if __name__ == "__main__":
    main()
