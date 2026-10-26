import csv

with open('c:/Users/joead/Documents/joey-home/vegas_fantasy/RegularSeasonReceivingTDs.txt', 'r') as file:
    lines = [line.strip() for line in file if line.strip()]

# Prepare columns: each is every 5th line, offset by 0, 1, 2, 3, 4
columns = [lines[i::5] for i in range(5)]
# Find the max length to pad shorter columns
max_len = max(len(col) for col in columns)
for col in columns:
    while len(col) < max_len:
        col.append('')

rows = list(zip(*columns))

with open('c:/Users/joead/Documents/joey-home/vegas_fantasy/RegularSeasonReceivingTDs.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Col1', 'Col2', 'Col3', 'Col4', 'Col5'])
    writer.writerows(rows)