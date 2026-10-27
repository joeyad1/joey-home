from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
BOONE_DIR = REPO_ROOT / "justin_boone_scraper" / "data"
SLEEPER_STATE_DIR = REPO_ROOT / "APIcalls" / "sleeperDicts"
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET_LEAGUES = {
    "The Lamb",
    "Gamers of America",
    "The Slif Bowl",
}


def normalize_player_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def fetch_json(url: str) -> object:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def load_player_map() -> Dict[str, Dict[str, str]]:
    local_path = SLEEPER_STATE_DIR / "players.json"
    if local_path.exists():
        with local_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return {str(k): v for k, v in raw.items()}

    raw = fetch_json("https://api.sleeper.app/v1/players/nfl")
    return {str(k): v for k, v in raw.items()}


def load_boone_rankings() -> Dict[str, Dict[str, Dict[str, str]]]:
    file_path = BOONE_DIR / "justin_boone_rankings_flattened.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing Boone rankings file: {file_path}")

    index: Dict[str, Dict[str, Dict[str, str]]] = defaultdict(dict)
    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("player_name", "").strip()
            key = normalize_player_name(name)
            score = (row.get("scoring_format") or "HALF").upper()
            index[key][score] = row
    return index


def load_trade_value_map() -> Dict[str, Dict[str, str]]:
    value_map: Dict[str, Dict[str, str]] = {}
    for pattern in ["trade_value", "dynasty"]:
        for file_path in sorted(BOONE_DIR.glob(f"*{pattern}*.csv")):
            if file_path.name.endswith(".csv"):
                with file_path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get("player_name", "").strip() or row.get("Player", "").strip()
                        if not name:
                            continue
                        value_map[normalize_player_name(name)] = row
    return value_map


def get_current_season() -> str:
    local_state = SLEEPER_STATE_DIR / "sleeperNFLState.json"
    if local_state.exists():
        with local_state.open("r", encoding="utf-8") as f:
            state = json.load(f)
            if state.get("season"):
                return str(state["season"])
    state = fetch_json("https://api.sleeper.app/v1/state/nfl")
    return str(state["season"])


def get_leagues_for_user(username: str, season: str) -> List[Dict[str, object]]:
    local_user_dir = SLEEPER_STATE_DIR / username
    local_all = local_user_dir / "allLeagues.json"
    if local_all.exists():
        with local_all.open("r", encoding="utf-8") as f:
            leagues = json.load(f)
    else:
        leagues = fetch_json(f"https://api.sleeper.app/v1/user/{username}/leagues/nfl/{season}")

    active = []
    for league in leagues:
        name = league.get("name") or ""
        if "CHOP" in name.upper():
            continue
        if name in TARGET_LEAGUES:
            active.append(league)
    return active


def get_user_display_name(user_id: str, users: List[Dict[str, object]]) -> str:
    for user in users:
        if str(user.get("user_id")) == str(user_id):
            return str(user.get("display_name") or user.get("username") or "Unknown")
    return str(user_id)


def determine_league_type(name: str) -> str:
    if name == "The Lamb":
        return "dynasty"
    if name in {"Gamers of America", "The Slif Bowl"}:
        return "keeper_half_ppr"
    return "standard"


def write_csv(rows: List[Dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_my_user_id() -> str:
    user_file = REPO_ROOT / "APIcalls" / "sleeperDicts" / "joeyad" / "userInfo.json"
    if user_file.exists():
        with user_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("user_id"):
                return str(data["user_id"])
    return "439870479407247360"


def build_team_rows() -> List[Dict[str, str]]:
    username = "joeyad"
    season = get_current_season()
    players_by_id = load_player_map()
    boone_lookup = load_boone_rankings()
    trade_lookup = load_trade_value_map()
    my_user_id = get_my_user_id()

    rows: List[Dict[str, str]] = []
    league_rows = []

    for league in get_leagues_for_user(username, season):
        league_name = str(league.get("name") or "")
        league_type = determine_league_type(league_name)
        league_id = str(league.get("league_id") or "")

        users = fetch_json(f"https://api.sleeper.app/v1/league/{league_id}/users")
        rosters = fetch_json(f"https://api.sleeper.app/v1/league/{league_id}/rosters")

        for roster in rosters:
            if str(roster.get("owner_id") or "") != my_user_id:
                continue
            owner_id = str(roster.get("owner_id") or "")
            team_name = get_user_display_name(owner_id, users)
            roster_id = str(roster.get("roster_id") or "")
            starters = {str(x) for x in roster.get("starters", [])}

            for player_id in roster.get("players", []):
                player_id_str = str(player_id)
                player_meta = players_by_id.get(player_id_str, {})
                first_name = str(player_meta.get("first_name") or "")
                last_name = str(player_meta.get("last_name") or "")
                full_name = f"{first_name} {last_name}".strip()
                if not full_name:
                    full_name = str(player_id)
                position = str(player_meta.get("position") or "")
                team_abbr = str(player_meta.get("team") or "")

                key = normalize_player_name(full_name)
                boone_row = (boone_lookup.get(key) or {}).get("HALF", {})
                ppr_row = (boone_lookup.get(key) or {}).get("PPR", {})

                half_rank = boone_row.get("rank", "")
                ppr_rank = ppr_row.get("rank", "")
                flex_half = boone_row.get("flex_rank", "")
                flex_ppr = ppr_row.get("flex_rank", "")

                trade_value_row = trade_lookup.get(key, {})
                trade_value = trade_value_row.get("Value", trade_value_row.get("value", ""))
                dynasty_value = trade_value_row.get("Value", trade_value_row.get("value", ""))
                if league_type == "dynasty":
                    trade_value = trade_value_row.get("Value", trade_value_row.get("value", ""))

                row = {
                    "league_name": league_name,
                    "league_id": league_id,
                    "league_type": league_type,
                    "team_name": team_name,
                    "owner_id": owner_id,
                    "roster_id": roster_id,
                    "player_id": player_id_str,
                    "player_name": full_name,
                    "player_position": position,
                    "player_team": team_abbr,
                    "starter": "true" if player_id_str in starters else "false",
                    "boone_rank_half": half_rank,
                    "boone_rank_ppr": ppr_rank,
                    "flex_rank_half": flex_half,
                    "flex_rank_ppr": flex_ppr,
                    "trade_value": trade_value,
                    "dynasty_value": dynasty_value,
                    "keeper_rule": "1 round prior to prior-year draft position" if league_type in {"keeper_half_ppr"} else "n/a",
                    "keeper_round": "",
                }
                rows.append(row)
                league_rows.append(row)

    return rows


def summarize_team_recommendations(team_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in team_rows:
        grouped[(row["league_name"], row["team_name"])].append(row)

    summary_rows: List[Dict[str, str]] = []
    for (league_name, team_name), roster_rows in grouped.items():
        starters = [r for r in roster_rows if r["starter"] == "true"]
        bench = [r for r in roster_rows if r["starter"] != "true"]

        best_bench = None
        for row in sorted(bench, key=lambda x: int(x["boone_rank_half"] or 999999))[:3]:
            best_bench = row
            break

        best_start = None
        for row in sorted(starters, key=lambda x: int(x["boone_rank_half"] or 999999))[:3]:
            best_start = row
            break

        summary_rows.append({
            "league_name": league_name,
            "team_name": team_name,
            "starter_count": str(len(starters)),
            "bench_count": str(len(bench)),
            "best_bench_player": (best_bench or {}).get("player_name", ""),
            "best_bench_rank": (best_bench or {}).get("boone_rank_half", ""),
            "best_starter_player": (best_start or {}).get("player_name", ""),
            "best_starter_rank": (best_start or {}).get("boone_rank_half", ""),
            "suggested_focus": "waiver + matchup optimization" if best_bench else "watch depth",
        })

    return summary_rows


def main() -> None:
    rows = build_team_rows()
    write_csv(rows, OUTPUT_DIR / "sleeper_team_snapshot.csv")

    summary = summarize_team_recommendations(rows)
    write_csv(summary, OUTPUT_DIR / "roster_optimization_summary.csv")

    print(f"Wrote {len(rows)} roster rows to {OUTPUT_DIR / 'sleeper_team_snapshot.csv'}")
    print(f"Wrote {len(summary)} team-level recommendations to {OUTPUT_DIR / 'roster_optimization_summary.csv'}")


if __name__ == "__main__":
    main()
