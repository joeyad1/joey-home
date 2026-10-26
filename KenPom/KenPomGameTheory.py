import csv
import json
import re
from pathlib import Path

WINPROB_PATH = Path(__file__).with_name('WinProbabilities.csv')
PUBLIC_PICKS_PATH = Path(__file__).with_name('publicPicks.csv')
OUT_JSON_PATH = Path(__file__).with_name('KenPomMadnessGameTheory.json')

ALIAS = {
    'iowast': 'iowastate',
    'iowastate': 'iowastate',
    'uconn': 'uconn',
    'connecticut': 'uconn',
    "stjohns": 'stjohns',
    "stjohn's": 'stjohns',
    'stjohn': 'stjohns',
    'florida': 'florida',
    'miamifl': 'miamifl',
    'northcarolina': 'northcarolina',
}


def normalize_team_name(name: str) -> str:
    key = name.strip().lower()
    key = key.replace("'", "").replace(".", "")
    key = re.sub(r"[^a-z0-9]", "", key)
    return ALIAS.get(key, key)


def load_win_probabilities(filepath):
    data = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row.get('Team', '').strip()
            if not team:
                continue
            champ_value = row.get('Champion', '').strip()
            if champ_value == '':
                continue
            try:
                champion = float(champ_value)
            except ValueError:
                continue
            norm = normalize_team_name(team)
            data[norm] = {
                'Team': team,
                'ChampionWinProbability': champion,
            }
    return data


def load_public_picks(filepath):
    data = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row.get('Team', '').strip()
            if not team:
                continue
            v = row.get('publicPicks', '').strip().strip('%')
            if v == '':
                continue
            try:
                pick_pct = float(v)
            except ValueError:
                continue
            norm = normalize_team_name(team)
            data[norm] = {
                'Team': team,
                'PickPercentage': pick_pct,
            }
    return data


def calculate_differences(win_prob, public_picks):
    teams = set(win_prob.keys()) | set(public_picks.keys())
    results = []
    for norm in teams:
        wp_entry = win_prob.get(norm, None)
        pp_entry = public_picks.get(norm, None)

        team_name = wp_entry['Team'] if wp_entry else (pp_entry['Team'] if pp_entry else norm)
        champion_prob = wp_entry['ChampionWinProbability'] if wp_entry else 0.0
        pick_pct = pp_entry['PickPercentage'] if pp_entry else 0.0
        diff = champion_prob - pick_pct

        results.append({
            'Team': team_name,
            'ChampionWinProbability': champion_prob,
            'PickPercentage': pick_pct,
            'Difference': round(diff, 4)
        })

    results.sort(key=lambda x: x['Difference'], reverse=True)
    return results


def main():
    win_prob = load_win_probabilities(WINPROB_PATH)
    public_picks = load_public_picks(PUBLIC_PICKS_PATH)

    results = calculate_differences(win_prob, public_picks)

    out_csv_path = Path(__file__).with_name('KenPomMadnessGameTheory.csv')
    with open(out_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Team', 'ChampionWinProbability', 'PickPercentage', 'Difference'])
        for row in results:
            writer.writerow([
                row['Team'],
                row['ChampionWinProbability'],
                row['PickPercentage'],
                row['Difference']
            ])

    print(f'Wrote {out_csv_path} with {len(results)} teams')


if __name__ == '__main__':
    main()
