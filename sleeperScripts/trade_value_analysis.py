from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "sleeper_team_snapshot.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_rows() -> List[Dict[str, str]]:
    with SNAPSHOT_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def safe_int(value: str) -> int:
    value = (value or "").strip()
    if not value:
        return 999999
    try:
        return int(value)
    except ValueError:
        return 999999


def build_analysis() -> List[Dict[str, str]]:
    rows = load_rows()
    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("league_name", ""), row.get("team_name", ""))].append(row)

    out: List[Dict[str, str]] = []
    for (league_name, team_name), roster in grouped.items():
        league_type = next((r.get("league_type", "") for r in roster if r.get("league_type")), "standard")
        for row in roster:
            pos = row.get("player_position", "")
            if pos in {"K", "DEF"}:
                continue

            half_rank = safe_int(row.get("boone_rank_half", ""))
            ppr_rank = safe_int(row.get("boone_rank_ppr", ""))
            flex_half = safe_int(row.get("flex_rank_half", ""))
            flex_ppr = safe_int(row.get("flex_rank_ppr", ""))
            trade_value = safe_int(row.get("trade_value", "")) if row.get("trade_value", "") else 0
            dynasty_value = safe_int(row.get("dynasty_value", "")) if row.get("dynasty_value", "") else 0

            rank_score = min(half_rank, ppr_rank, flex_half, flex_ppr)
            value_score = trade_value if league_type == "dynasty" else dynasty_value
            if not value_score:
                value_score = 0

            if row.get("starter") == "true":
                status = "starter"
            else:
                status = "bench"

            out.append({
                "league_name": league_name,
                "team_name": team_name,
                "player_name": row.get("player_name", ""),
                "player_position": pos,
                "status": status,
                "league_type": league_type,
                "boone_rank_half": row.get("boone_rank_half", ""),
                "boone_rank_ppr": row.get("boone_rank_ppr", ""),
                "trade_value": row.get("trade_value", ""),
                "dynasty_value": row.get("dynasty_value", ""),
                "rank_score": str(rank_score),
                "value_score": str(value_score),
                "trade_signal": "sell_high" if rank_score <= 10 and value_score >= 50 else "hold" if rank_score <= 25 else "buy_low" if rank_score >= 35 and value_score <= 20 else "watch",
            })

    return out


def main() -> None:
    rows = build_analysis()
    output = OUTPUT_DIR / "trade_value_analysis.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "league_name",
            "team_name",
            "player_name",
            "player_position",
            "status",
            "league_type",
            "boone_rank_half",
            "boone_rank_ppr",
            "trade_value",
            "dynasty_value",
            "rank_score",
            "value_score",
            "trade_signal",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} trade-value analysis rows to {output}")


if __name__ == "__main__":
    main()
