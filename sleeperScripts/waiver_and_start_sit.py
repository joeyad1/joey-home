from __future__ import annotations

import csv
import json
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


def normalize_rank(value: str) -> int:
    value = (value or "").strip()
    if not value:
        return 999999
    try:
        return int(value)
    except ValueError:
        return 999999


def player_key(row: Dict[str, str]) -> str:
    return f"{row.get('league_name','')}|{row.get('team_name','')}|{row.get('player_name','')}|{row.get('player_position','')}"


def build_recommendations() -> List[Dict[str, str]]:
    rows = load_rows()
    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("league_name", ""), row.get("team_name", ""))].append(row)

    recs: List[Dict[str, str]] = []
    for (league_name, team_name), roster in grouped.items():
        starters = [r for r in roster if r.get("starter") == "true"]
        bench = [r for r in roster if r.get("starter") != "true"]

        starter_by_pos: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for row in starters:
            starter_by_pos[row.get("player_position", "")].append(row)

        for player in bench + starters:
            pos = player.get("player_position", "")
            if pos in {"K", "DEF"}:
                continue
            if player.get("starter") == "true":
                status = "starter"
            else:
                status = "bench"

            rank_half = normalize_rank(player.get("boone_rank_half", ""))
            rank_ppr = normalize_rank(player.get("boone_rank_ppr", ""))
            flex_half = normalize_rank(player.get("flex_rank_half", ""))
            flex_ppr = normalize_rank(player.get("flex_rank_ppr", ""))
            rank_used = min(rank_half, rank_ppr, flex_half, flex_ppr)

            comparable = [
                r for r in roster
                if r.get("player_position") == pos and r.get("player_name") != player.get("player_name")
            ]
            comparable = sorted(
                comparable,
                key=lambda r: min(
                    normalize_rank(r.get("boone_rank_half", "")),
                    normalize_rank(r.get("boone_rank_ppr", "")),
                    normalize_rank(r.get("flex_rank_half", "")),
                    normalize_rank(r.get("flex_rank_ppr", "")),
                ),
            )[:5]

            best_alt = comparable[0] if comparable else {}
            best_rank = min(
                normalize_rank(best_alt.get("boone_rank_half", "")),
                normalize_rank(best_alt.get("boone_rank_ppr", "")),
                normalize_rank(best_alt.get("flex_rank_half", "")),
                normalize_rank(best_alt.get("flex_rank_ppr", "")),
            ) if best_alt else 999999

            waiver_flag = ""
            if player.get("starter") != "true" and best_rank < rank_used:
                waiver_flag = "upgrade_candidate"
            elif player.get("starter") == "true" and best_rank < rank_used:
                waiver_flag = "bench_upgrade"
            else:
                waiver_flag = "hold"

            recs.append({
                "league_name": league_name,
                "team_name": team_name,
                "player_name": player.get("player_name", ""),
                "player_position": pos,
                "status": status,
                "boone_rank_half": player.get("boone_rank_half", ""),
                "boone_rank_ppr": player.get("boone_rank_ppr", ""),
                "flex_rank_half": player.get("flex_rank_half", ""),
                "flex_rank_ppr": player.get("flex_rank_ppr", ""),
                "best_comparable_player": best_alt.get("player_name", ""),
                "best_comparable_rank": str(best_rank) if best_alt else "",
                "recommendation": waiver_flag,
                "note": "bench upgrade candidate" if waiver_flag == "upgrade_candidate" else "starter depth check" if waiver_flag == "bench_upgrade" else "hold",
            })

    return recs


def main() -> None:
    recs = build_recommendations()
    output = OUTPUT_DIR / "waiver_and_start_sit.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "league_name",
            "team_name",
            "player_name",
            "player_position",
            "status",
            "boone_rank_half",
            "boone_rank_ppr",
            "flex_rank_half",
            "flex_rank_ppr",
            "best_comparable_player",
            "best_comparable_rank",
            "recommendation",
            "note",
        ])
        writer.writeheader()
        writer.writerows(recs)

    print(f"Wrote {len(recs)} start/sit recommendations to {output}")


if __name__ == "__main__":
    main()
