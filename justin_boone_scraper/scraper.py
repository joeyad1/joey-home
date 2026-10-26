from __future__ import annotations

import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, urlparse

import requests
import schedule
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

RANKINGS_SEED_URLS = [
    "https://sports.yahoo.com/fantasy/article/fantasy-football-week-7-rankings-from-justin-boone-163325767.html",
    "https://sports.yahoo.com/fantasy/article/week-6-fantasy-football-rankings-from-justin-boone-164604693.html",
    "https://sports.yahoo.com/fantasy/article/fantasy-football-week-6-rankings-from-justin-boone-164604693.html",
]

TRADE_VALUE_URLS = {
    "qb": "https://sports.yahoo.com/fantasy/article/2026-trade-value-charts--justin-boones-fantasy-football-quarterback-breakdown-for-week-7-150025496.html",
    "rb": "https://sports.yahoo.com/fantasy/article/2026-trade-value-charts--justin-boones-fantasy-football-running-back-breakdown-for-week-7-150033672.html",
    "wr": "https://sports.yahoo.com/fantasy/article/2026-trade-value-charts--justin-boones-fantasy-football-wide-receiver-breakdown-for-week-7-150030573.html",
    "te": "https://sports.yahoo.com/fantasy/article/2026-trade-value-charts--justin-boones-fantasy-football-tight-end-breakdown-for-week-7-150018094.html",
}

DYNASTY_URLS = {
    "qb": "https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-rankings-trade-value-charts-justin-boone-qb-quarterback-162928894.html",
    "rb": "https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-rankings-trade-value-charts-justin-boone-rb-running-back-163059931.html",
    "wr": "https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-rankings-2026-trade-value-charts-justin-boone-wr-wide-receiver-182932306.html",
    "te": "https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-rankings-trade-value-charts-justin-boone-te-tight-end-163356408.html",
    "draft_picks": "https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-rankings-rookie-draft-pick-trade-value-chart-justin-boone-update-162543373.html",
}


def request_html(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip()


def current_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def find_best_table(soup: BeautifulSoup, required_keywords: Iterable[str]) -> Optional[BeautifulSoup]:
    req = [kw.lower() for kw in required_keywords]
    for table in soup.select("table"):
        table_text = table.get_text(" ", strip=True).lower()
        if all(keyword in table_text for keyword in req):
            return table
    return None


def parse_html_table(table: BeautifulSoup) -> List[Dict[str, str]]:
    rows = table.select("tr")
    if not rows:
        return []

    header_cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in rows[0].select("th, td")]
    if not header_cells:
        return []

    output: List[Dict[str, str]] = []
    for row in rows[1:]:
        cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in row.select("th, td")]
        if not cells or all(not cell for cell in cells):
            continue
        record = {}
        for idx, key in enumerate(header_cells):
            record[key] = cells[idx] if idx < len(cells) else ""
        output.append(record)
    return output


def discover_latest_rankings_url() -> str:
    for seed in RANKINGS_SEED_URLS:
        try:
            page = request_html(seed)
            soup = BeautifulSoup(page, "html.parser")
            og_url = soup.find("meta", property="og:url")
            if og_url and og_url.get("content"):
                url = og_url["content"]
                if "justin-boone" in url.lower() and "fantasy-football-week-" in url.lower():
                    return url

            response = requests.get(seed, timeout=30, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
            response.raise_for_status()
            if "justin-boone" in response.url.lower() and "fantasy-football-week-" in response.url.lower():
                return response.url
        except requests.RequestException:
            continue

    for week in range(1, 25):
        query = f'"Justin Boone" "week {week}" "fantasy football rankings" site:sports.yahoo.com/fantasy'
        search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
        try:
            html = request_html(search_url)
            matches = re.findall(r'https://sports\.yahoo\.com/fantasy/article/[^\"\'\s]+justin-boone[^\"\'\s]*', html, flags=re.I)
            for candidate in matches:
                cleaned = candidate.split("&")[0]
                if "fantasy-football-week-" in cleaned.lower():
                    return cleaned
        except Exception:
            continue

    raise RuntimeError("Unable to discover current Justin Boone weekly rankings URL")


def extract_fantasypros_widget_url(article_html: str) -> str:
    matches = re.findall(r'https://partners\.fantasypros\.com/external/widget/fp-widget\.php\?[^"\'\s]+', article_html, flags=re.I)
    if not matches:
        raise RuntimeError("FantasyPros widget URL not found in article HTML")
    candidate = matches[0].replace("\\u0026", "&").replace("\\u003d", "=")
    return candidate.split("&")[0] + "&" + "&".join(part for part in candidate.split("&")[1:] if part)


def extract_fantasypros_widget_urls(article_html: str) -> List[str]:
    matches = re.findall(r'https://partners\.fantasypros\.com/external/widget/fp-widget\.php\?[^"\'\s]+', article_html, flags=re.I)
    cleaned: List[str] = []
    for match in matches:
        candidate = match.replace("\\u0026", "&").replace("\\u003d", "=")
        url = candidate.split("&")[0] + "&" + "&".join(part for part in candidate.split("&")[1:] if part)
        if url not in cleaned:
            cleaned.append(url)
    if not cleaned:
        raise RuntimeError("FantasyPros widget URL not found in article HTML")
    return cleaned


def get_fantasypros_rankings_widget_params(url: str) -> Dict[str, str]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    cleaned = {k: v[0] if isinstance(v, list) and v else "" for k, v in params.items()}
    if not cleaned:
        raise RuntimeError(f"Unable to parse FantasyPros widget params from {url}")
    return cleaned


def fetch_fantasypros_rankings_for_position(position: str, params: Dict[str, str], scoring_format: str = "HALF") -> List[Dict[str, str]]:
    api_url = "https://partners.fantasypros.com/api/v1/expert-rankings.php"
    payload = {
        "sport": params.get("sport", "NFL"),
        "year": params.get("year", "2026"),
        "week": params.get("week", "1"),
        "id": params.get("expert", params.get("id", "1663")),
        "position": position,
        "type": params.get("wtype", "ST"),
        "scoring": scoring_format,
        "callback": "FPW.rankingsCB",
    }
    response = requests.get(api_url, params=payload, timeout=30, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        return []

    match = re.search(r'FPW\.rankingsCB\((.*)\);?\s*$', text, flags=re.S)
    if not match:
        raise RuntimeError(f'Unexpected FantasyPros response format for {position} {scoring_format}: {text[:300]}')
    data = json.loads(match.group(1))
    players = data.get("players", [])
    rows = []
    for player in players:
        rows.append({
            "player_name": player.get("player_name", ""),
            "position": position,
            "scoring_format": scoring_format,
            "week": payload.get("week", ""),
            "year": payload.get("year", ""),
            "source_position": position,
            "rank": player.get("rank", ""),
            "pos_rank": player.get("pos_rank", ""),
            "player_team_id": player.get("player_team_id", ""),
            "player_positions": player.get("player_positions", player.get("player_eligibility", "")),
            "rank_ecr": player.get("rank_ecr", ""),
            "rank_vs_ecr": player.get("rank_vs_ecr", ""),
            "published": data.get("published", ""),
            "expert_name": "Justin Boone",
            "source_name": "Justin Boone",
            "source_url": params.get("source_url", ""),
            "period_type": "week",
            "period_value": payload.get("week", ""),
            "is_latest": "true",
        })
    return rows


def add_period_metadata(rows: List[Dict[str, str]], period_type: str, period_value: str, is_latest: bool = True) -> List[Dict[str, str]]:
    for row in rows:
        row["period_type"] = period_type
        row["period_value"] = period_value
        row["is_latest"] = "true" if is_latest else "false"
    return rows


def flatten_rankings_rows(position_rows: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    flattened: List[Dict[str, str]] = []
    for position, rows in position_rows.items():
        for row in rows:
            flattened.append({
                **row,
                "position": position,
                "source_position": position,
                "source_name": row.get("source_name", f"justin_boone_rankings_{position.lower()}"),
            })
    return flattened


def scrape_rankings() -> None:
    rankings_url = discover_latest_rankings_url()
    article_html = request_html(rankings_url)
    widget_urls = extract_fantasypros_widget_urls(article_html)

    position_rows: Dict[str, List[Dict[str, str]]] = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": [],
        "DST": [],
        "K": [],
    }
    flex_lookup: Dict[str, Dict[str, str]] = {"HALF": {}, "PPR": {}}
    combined_rows: List[Dict[str, str]] = []

    for widget_url in widget_urls:
        widget_params = get_fantasypros_rankings_widget_params(widget_url)
        widget_params["source_url"] = rankings_url
        scoring_format = widget_params.get("scoring", "HALF").upper()

        for position in ["QB", "RB", "WR", "TE", "FLX", "K", "DST"]:
            if position == "FLX":
                rows = fetch_fantasypros_rankings_for_position("FLX", widget_params, scoring_format=scoring_format)
                for row in rows:
                    flex_lookup.setdefault(scoring_format, {})[row.get("player_name", "")] = row.get("rank", "")
                combined_rows.extend(rows)
                continue

            if position in {"QB", "K", "DST"} and scoring_format == "PPR":
                continue
            if position in {"RB", "WR", "TE"} and scoring_format in {"HALF", "PPR"}:
                pass
            elif position not in {"QB", "K", "DST"}:
                continue

            rows = fetch_fantasypros_rankings_for_position(position, widget_params, scoring_format=scoring_format)
            position_rows.setdefault(position, []).extend(rows)
            combined_rows.extend(rows)

    for scoring, lookup in flex_lookup.items():
        for position in ["RB", "WR", "TE"]:
            for row in position_rows.get(position, []):
                if row.get("scoring_format", "HALF").upper() == scoring:
                    row["flex_rank"] = lookup.get(row.get("player_name", ""), "")

    for position, rows in position_rows.items():
        if not rows:
            continue
        write_csv(
            rows,
            DATA_DIR / f"justin_boone_rankings_{position.lower()}.csv",
            rankings_url,
            f"justin_boone_rankings_{position.lower()}",
            "weekly_rankings",
        )

    flattened_rows = flatten_rankings_rows(position_rows)
    write_csv(
        flattened_rows,
        DATA_DIR / "justin_boone_rankings_flattened.csv",
        rankings_url,
        "justin_boone_rankings_flattened",
        "weekly_rankings",
    )

    write_csv(
        combined_rows,
        DATA_DIR / "justin_boone_rankings_latest.csv",
        rankings_url,
        "justin_boone_rankings",
        "weekly_rankings",
    )


def discover_trade_value_url(position_key: str) -> str:
    direct = TRADE_VALUE_URLS.get(position_key)
    if direct:
        try:
            response = requests.get(direct, timeout=30, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
            response.raise_for_status()
            if "sports.yahoo.com/fantasy/article/" in response.url:
                return response.url
        except requests.RequestException:
            pass

    query = f'"Justin Boone" "{position_key.upper()}" "trade value charts" site:sports.yahoo.com/fantasy'
    search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
    html = request_html(search_url)
    matches = re.findall(r'https://sports\.yahoo\.com/fantasy/article/[^\"\'\s]+', html, flags=re.I)
    for candidate in matches:
        c = candidate.split("&")[0]
        if "trade-value-charts" in c.lower() and position_key.lower() in c.lower():
            return c

    raise RuntimeError(f"Unable to discover current URL for {position_key} trade value chart")


def discover_dynasty_url(position_key: str) -> str:
    direct = DYNASTY_URLS.get(position_key)
    if direct:
        try:
            response = requests.get(direct, timeout=30, headers={"User-Agent": USER_AGENT}, allow_redirects=True)
            response.raise_for_status()
            if "sports.yahoo.com/fantasy/article/" in response.url:
                return response.url
        except requests.RequestException:
            pass

    query = f'"Justin Boone" "{position_key.upper()}" "dynasty" "trade value" site:sports.yahoo.com/fantasy'
    search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
    html = request_html(search_url)
    matches = re.findall(r'https://sports\.yahoo\.com/fantasy/article/[^\"\'\s]+', html, flags=re.I)
    for candidate in matches:
        c = candidate.split("&")[0]
        if ("trade-value-charts" in c.lower() or "trade-value-chart" in c.lower()) and (
            position_key.lower() in c.lower() or "dynasty" in c.lower()
        ):
            return c

    raise RuntimeError(f"Unable to discover current URL for {position_key} dynasty chart")


def fetch_table_rows_from_url(url: str, required_keywords: Iterable[str]) -> List[Dict[str, str]]:
    html = request_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    required = [kw.lower() for kw in required_keywords]
    for table in soup.select('table'):
        text = table.get_text(' ', strip=True).lower()
        if all(keyword in text for keyword in required):
            return parse_html_table(table)
    # fallback: accept any table that clearly contains player/rank/value data or pick/value data, even if the
    # exact column names vary between articles and chart formats.
    for table in soup.select('table'):
        text = table.get_text(' ', strip=True).lower()
        if (
            ('player' in text and (
                'rank' in text or 'rk' in text or 'ppr' in text or 'value' in text
                or 'half ppr' in text or '1qb' in text or '1rb' in text or '1wr' in text or '1te' in text
            ))
            or ('pick' in text and ('1qb' in text or '2qb' in text or 'early 1st' in text or 'value' in text))
        ):
            return parse_html_table(table)
    raise RuntimeError(f'Could not find matching table for {url}')


def write_csv(rows: List[Dict[str, str]], output_path: Path, source_url: str, source_name: str, category: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    base_fieldnames = [
        "expert_name",
        "player_name",
        "player_positions",
        "player_team_id",
        "pos_rank",
        "position",
        "published",
        "rank",
        "rank_ecr",
        "rank_vs_ecr",
        "scoring_format",
        "source_name",
        "source_position",
        "source_url",
        "week",
        "year",
        "period_type",
        "period_value",
        "is_latest",
        "flex_rank",
        "scraped_at",
        "category",
    ]
    ordered = []
    seen = set()
    for key in base_fieldnames + sorted({k for row in rows for k in row.keys()}):
        if key not in seen:
            ordered.append(key)
            seen.add(key)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "scraped_at": current_timestamp(), "source_url": source_url, "source_name": source_name, "category": category})


def scrape_trade_values() -> None:
    for key in ['qb', 'rb', 'wr', 'te']:
        url = discover_trade_value_url(key)
        rows = fetch_table_rows_from_url(url, ['player', key])
        rows = add_period_metadata(rows, 'week', datetime.utcnow().strftime('%Y-W%U').replace('-W0', '-W'))
        write_csv(rows, DATA_DIR / f'justin_boone_trade_value_{key}.csv', url, f'justin_boone_trade_value_{key}', 'trade_value')


def scrape_dynasty_values() -> None:
    for key in ["qb", "rb", "wr", "te", "draft_picks"]:
        url = discover_dynasty_url(key)
        rows = fetch_table_rows_from_url(url, ["player", key] if key != "draft_picks" else ["pick", "player"])
        rows = add_period_metadata(rows, 'month', datetime.utcnow().strftime('%Y-%m'), is_latest=True)
        write_csv(rows, DATA_DIR / f"justin_boone_dynasty_{key}.csv", url, f"justin_boone_dynasty_{key}", "dynasty_trade_value")


def run_all() -> None:
    scrape_rankings()
    scrape_trade_values()
    scrape_dynasty_values()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Justin Boone fantasy football content.")
    parser.add_argument("--once", action="store_true", help="Run once and exit.")
    args = parser.parse_args()

    if args.once:
        run_all()
        return

    schedule.every(6).hours.do(scrape_rankings)
    schedule.every(12).hours.do(scrape_trade_values)
    schedule.every(30).days.do(scrape_dynasty_values)

    print("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
