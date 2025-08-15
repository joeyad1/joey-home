import csv
import os

def get_unique_player_names(csv_files):
    player_names = set()
    for file in csv_files:
        if not os.path.exists(file):
            continue
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] != '' and row[0].lower() != 'column1':
                    player_names.add(row[0].strip())
    return sorted(player_names)

def build_player_matrix(csv_files, output_path):
    # Map: file index to column in output
    # 0: receiving yards, 1: receiving tds, 2: rushing yards, 3: rushing tds, 4: passing yards, 5: passing tds, 6: yards per rec
    stat_map = {
        0: 2,  # receiving yards
        1: 3,  # receiving tds
        2: 4,  # rushing yards
        3: 5,  # rushing tds
        4: 6,  # passing yards
        5: 7,  # passing tds
        6: 8,  # yards per rec
        # 1: position (handled separately)
    }
    player_names = get_unique_player_names(csv_files)
    # Initialize matrix: player name, position, 6 stat columns, yards per rec
    matrix = {name: [name, '', '', '', '', '', '', '', ''] for name in player_names}
    # Add position from positionList.csv (assume last file in csv_files)
    position_file = [f for f in csv_files if 'positionList.csv' in f]
    position_map = {}
    if position_file:
        with open(position_file[0], newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2 and row[0] and row[1]:
                    position_map[row[0].strip()] = row[1].strip()
    for name in matrix:
        if name in position_map:
            matrix[name][1] = position_map[name]

    for idx, file in enumerate(csv_files):
        if not os.path.exists(file):
            print(f"File not found: {file}")
            continue
        if 'positionList.csv' in file:
            continue  # handled separately
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] != '' and row[0].lower() != 'column1':
                    name = row[0].strip()
                    value = row[1].strip() if len(row) > 1 else 0
                    matrix[name][stat_map[idx]] = value

    # Calculate average yards_per_rec (excluding 0s and blanks)
    yards_per_rec_values = [
        float(row[8]) for row in matrix.values()
        if row[8] and row[8] != '0' and row[8] != 0
    ]
    avg_yards_per_rec = sum(yards_per_rec_values) / len(yards_per_rec_values) if yards_per_rec_values else 0

    # Calculate 9th column: Receiving Yards (col 2) / Yards Per Rec (col 8)
    for row in matrix.values():
        try:
            receiving_yards = float(row[2]) if row[2] else 0
            yards_per_rec = float(row[8]) if row[8] else 0
            if yards_per_rec == 0:
                yards_per_rec = avg_yards_per_rec
            ratio = receiving_yards / yards_per_rec if yards_per_rec != 0 else ''
        except ValueError:
            ratio = 0
        row.append(ratio)
        # Calculate 10th column: Fantasy Points
        # Formula: .1 * (col3 + col5) + 6 * (col4 + col6) + .04*col7 + 4*col8 + .5*col10
        try:
            col3 = float(row[2]) if row[2] else 0  # Receiving Yards
            col4 = float(row[3]) if row[3] else 0  # Receiving TDs
            col5 = float(row[4]) if row[4] else 0  # Rushing Yards
            col6 = float(row[5]) if row[5] else 0  # Rushing TDs
            col7 = float(row[6]) if row[6] else 0  # Passing Yards
            col8 = float(row[7]) if row[7] else 0  # Passing TDs
            col10 = float(row[9]) if len(row) > 9 and row[9] else 0  # 10th column (Receiving Yards / Yards Per Rec)
            fantasy_points = (
                0.1 * (col3 + col5)
                + 6 * (col4 + col6)
                + 0.04 * col7
                + 4 * col8
                + 0.5 * col10
            )
        except ValueError:
            fantasy_points = 0
        row.append(fantasy_points)

    # Sort matrix by Fantasy Points (column 11, index 10) in descending order
    matrix = dict(sorted(matrix.items(), key=lambda item: float(item[1][10]) if item[1][10] != '' else 0, reverse=True))

    # Write output
    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Player Name', 'Position', 'Receiving Yards', 'Receiving TDs', 'Rushing Yards', 'Rushing TDs',
                'Passing Yards', 'Passing TDs', 'Yards Per Rec', 'Rec', 'Fantasy Points'
            ])
            for row in matrix.values():
                writer.writerow(row)
        print(f"Wrote output to {output_path}")
    except Exception as e:
        print(f"Failed to write output: {e}")

# Example usage:
base = "c:/Users/joead/Documents/joey-home/vegas_fantasy/"
csv_files = [
    base + 'RegularSeasonReceivingYards.csv',
    base + 'RegularSeasonReceivingTDs.csv',
    base + 'RegularSeasonRushingYards.csv',
    base + 'RegularSeasonRushingTDs.csv',
    base + 'RegularSeasonPassingYards.csv',
    base + 'RegularSeasonPassingTDs.csv',
    base + 'yardsPerRec.csv',
    base + 'positionList.csv'
]
build_player_matrix(csv_files, base + 'player_matrix.csv')





