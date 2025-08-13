import json
import csv
import os

cwd = os.getcwd()
fileName = 'FantasyPros_2024_Draft_ALL_Rankings.csv'
adpPath = cwd + '/' + fileName
adpNames = [] 

with open(adpPath, 'r') as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter=',')
    for row in csv_reader:
        adpNames.append(row['PLAYER NAME'])

i = 0
while i < len(adpNames):
    if 'Christian McCaffrey' == adpNames[i]:
        print(i+1)
    i += 1

