import csv
from pathlib import Path

GUIDELINES_CSV = Path(__file__).with_name('Guidelines.csv')
RAWDATA_CSV = Path(__file__).with_name('RawData.csv')


def load_guidelines(path):
    milestones = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            milestones.append({
                'Milestone': r['Milestone'].strip(),
                'AdjO Rank Threshold': float(r['AdjO Rank Threshold']),
                'AdjD Rank Threshold': float(r['AdjD Rank Threshold']),
                'AdjO Rating Minimum': float(r['AdjO Rating Minimum']),
                'AdjD Rating Maximum': float(r['AdjD Rating Maximum']),
            })
    return milestones


def load_rawdata(path):
    teams = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # support header variants
            teams.append({
                'Team': r.get('Team (Seed)', r.get('Team', '')).strip(),
                'ORtg': float(r.get('ORtg', 0)),
                'ORtg Rank': float(r.get('ORtg Rank', 0)),
                'DRtg': float(r.get('DRtg', 0)),
                'DRtg Rank': float(r.get('DRtg Rank', 0)),
            })
    return teams


def match_teams(milestone, teams):
    out = []
    for t in teams:
        if t['ORtg Rank'] <= milestone['AdjO Rank Threshold'] and \
           t['DRtg Rank'] <= milestone['AdjD Rank Threshold']:
            out.append(t)
    return out


def main():
    guidelines = load_guidelines(GUIDELINES_CSV)
    teams = load_rawdata(RAWDATA_CSV)

    # Order by the Guidelines milestone rank from weakest to strongest if not already.
    order = ['Sweet Sixteen', 'Elite Eight', 'Final Four', 'National Champion']
    ordered = [g for name in order for g in guidelines if g['Milestone'] == name]

    results = []
    for g in ordered:
        matched = match_teams(g, teams)
        matched.sort(key=lambda x: x['Team'])
        results.append((g['Milestone'], matched))

    # Export CSV summary
    out_csv = Path(__file__).with_name('KenPomMadness.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Milestone', 'TeamsCount', 'Teams'])
        for milestone, matched in results:
            team_names = [t['Team'] for t in matched]
            writer.writerow([milestone, len(team_names), '; '.join(team_names)])

    # Compute buffer teams (miss threshold by up to 5 ranks)
    buffer_json = Path(__file__).with_name('KenPomMadnessBuffer.json')
    buffer_data = []
    buffer_map = {}
    for g in ordered:
        threshold_o = g['AdjO Rank Threshold']
        threshold_d = g['AdjD Rank Threshold']
        buffer_teams = []
        for t in teams:
            in_o = t['ORtg Rank'] <= threshold_o
            in_d = t['DRtg Rank'] <= threshold_d
            in_o_buffer = t['ORtg Rank'] <= threshold_o + 5
            in_d_buffer = t['DRtg Rank'] <= threshold_d + 5
            # team is not qualified, but close within +5 range for both rank dimensions
            if not (in_o and in_d) and (in_o_buffer and in_d_buffer):
                buffer_teams.append(t['Team'])

        buffer_data.append({
            'Milestone': g['Milestone'],
            'BufferTeamsCount': len(buffer_teams),
            'BufferTeams': buffer_teams,
        })
        buffer_map[g['Milestone']] = buffer_teams

    # Export JSON summary including buffer flags
    out_json = Path(__file__).with_name('KenPomMadness.json')
    json_data = []
    for milestone, matched in results:
        qualified_names = [t['Team'] for t in matched]
        buffer_names = buffer_map.get(milestone, [])
        combined = qualified_names + [name + '*' for name in buffer_names]
        json_data.append({
            'Milestone': milestone,
            'TeamsCount': len(qualified_names),
            'Teams': combined,
        })
    with open(out_json, 'w', encoding='utf-8') as f:
        import json
        json.dump(json_data, f, indent=2)

    with open(buffer_json, 'w', encoding='utf-8') as f:
        import json
        json.dump(buffer_data, f, indent=2)

    print(f'Wrote {out_csv}, {out_json}, and {buffer_json} with {len(results)} milestones.')

    # also print detailed per milestone for easy reading
    print('\nDetailed results:')
    for milestone, matched in results:
        print('\n' + milestone)
        if not matched:
            print('  (none)')
            continue
        for t in matched:
            print(f"  - {t['Team']} (ORtg {t['ORtg']}, ORtg Rank {t['ORtg Rank']}; DRtg {t['DRtg']}, DRtg Rank {t['DRtg Rank']})")


if __name__ == '__main__':
    main()
