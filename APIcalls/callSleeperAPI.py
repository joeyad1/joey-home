import json
import requests
import os

"""
Script to use call Sleeper API and save as json
Sleeper API documentation: https://docs.sleeper.com/#introduction
"""

def getLeagueAllYears(leagueInfo):
    sleeperURL = "https://api.sleeper.app/v1/"
    allYears = {}
    allYears['Year'] = []
    allYears['seasonId'] = []
    allYears['draftId'] = []
    yearMsk = []
    seasonIdMsk = []
    prevSeasonIdMsk =[]
    draftIdMsk = []
    lastSeasonFlg = 0
    yearMsk = leagueInfo['season']
    allYears['Year'].append(yearMsk)
    seasonIdMsk = leagueInfo['league_id']
    allYears['seasonId'].append(seasonIdMsk)
    draftIdMsk = leagueInfo['draft_id']
    allYears['draftId'].append(draftIdMsk)

    prevSeasonIdMsk = leagueInfo['previous_league_id']
    if not prevSeasonIdMsk:
        lastSeasonFlg = 1
    while lastSeasonFlg < 1:
        seasonIdMsk = leagueInfo['previous_league_id']
        if not seasonIdMsk:
            break
        else:
            leagueInfo = requests.get(sleeperURL + "league/" + seasonIdMsk)
            leagueInfo = leagueInfo.json()
            if not leagueInfo:
                break
            else:
                yearMsk = leagueInfo['season']
                allYears['Year'].append(yearMsk)
                seasonIdMsk = leagueInfo['league_id']
                allYears['seasonId'].append(seasonIdMsk)
                draftIdMsk = leagueInfo['draft_id']
                allYears['draftId'].append(draftIdMsk)
    return allYears



print("Calling SleeperAPI")
#user ID for joeyad 1/14/24
#user_id = "joeyad"
user_id = "439870479407247360"
sleeperURL = "https://api.sleeper.app/v1/"
sleeperDictFP = "/Users/joey/Documents/github/joey-home/APIcalls/sleeperDicts/"
if not os.path.isdir(sleeperDictFP):
    os.mkdir(sleeperDictFP)

players = requests.get(sleeperURL + "players/nfl")
players = players.json()
with open(sleeperDictFP + "/players.json","w") as filePath:
    json.dump(players, filePath)

sleeperUser = requests.get(sleeperURL + "user/" + user_id)
sleeperUser = sleeperUser.json()
userName = sleeperUser['username']
if not os.path.isdir(sleeperDictFP + userName):
    os.mkdir(sleeperDictFP + userName)
with open(sleeperDictFP + userName + "/userInfo.json","w") as filePath:
    json.dump(sleeperUser, filePath)
state = requests.get(sleeperURL + "state/nfl")
state = state.json()
with open(sleeperDictFP + "sleeperNFLState.json","w") as filePath:
    json.dump(state, filePath)
allLeagues = requests.get(sleeperURL + "/user/" + user_id + "/leagues/nfl/" + state['season'])
allLeagues = allLeagues.json()
with open(sleeperDictFP + userName + "/allLeagues.json","w") as filePath:
    json.dump(allLeagues, filePath)
numLeagues = len(allLeagues)
leagueID = []
for x in range(numLeagues):
    leagueID = allLeagues[x]['league_id']
    #Load sleeper leagues and matchups
    leagueInfo = requests.get(sleeperURL + "league/" + leagueID)
    leagueInfo = leagueInfo.json()
    leagueName = leagueInfo['name'].replace(" ", "_")
    if not os.path.isdir(sleeperDictFP + "/" + userName + "/" + leagueName):
        os.mkdir(sleeperDictFP + "/" + userName + "/" + leagueName)
    with open(sleeperDictFP + userName + "/" + leagueName + "/leagueInfo.json","w") as filePath:
        json.dump(leagueInfo, filePath)
    rosters = requests.get(sleeperURL + "league/" + leagueID + "/rosters")
    with open(sleeperDictFP + userName + "/" + leagueName + "/rosters.json","w") as filePath:
        json.dump(rosters.json(), filePath)
    week = str(state['week'])
    #week = "14" #temporary override
    matchups = requests.get(sleeperURL + "league/" + leagueID + "/matchups/" + week)
    with open(sleeperDictFP + userName + "/" + leagueName + "/matchup_week" + week + ".json","w") as filePath:
        json.dump(matchups.json(), filePath)
    usersInfo = requests.get(sleeperURL + "league/" + leagueID + "/users")
    usersInfo = usersInfo.json()
    numUsers = len(usersInfo)
    with open(sleeperDictFP + userName + "/" + leagueName + "/userInfoIdx.txt","w") as filePath:
        for userIdx in range(numUsers):
            filePath.write(f"{usersInfo[userIdx]['user_id']}\n")
    with open(sleeperDictFP + userName + "/" + leagueName + "/usersInfo.json","w") as filePath:
        json.dump(usersInfo, filePath)
    draftInfo = requests.get(sleeperURL + "league/" + leagueID + "/drafts")
    draftInfo = draftInfo.json()
    with open(sleeperDictFP + userName + "/" + leagueName + "/draftInfo.json","w") as filePath:
        json.dump(draftInfo, filePath)
    allYears = getLeagueAllYears(leagueInfo)
    with open(sleeperDictFP + userName + "/" + leagueName + "/leagueIdHistory.json","w") as filePath:
        json.dump(allYears, filePath)
    numYears = len(allYears['Year'])
    for yearIdx in range(numYears):
        draftPicks = requests.get(sleeperURL + "draft/" + allYears['draftId'][yearIdx] + "/picks")
        draftPicks = draftPicks.json()
        with open(sleeperDictFP + userName + "/" + leagueName + "/draftPicks" + allYears['Year'][yearIdx] + ".json","w") as filePath:
            json.dump(draftPicks, filePath)   
        numDraftPicks = len(draftPicks)
        with open(sleeperDictFP + userName + "/" + leagueName + "/draftPlayerIdx" + allYears['Year'][yearIdx] + ".txt","w") as filePath:
            for pickIdx in range(numDraftPicks):
                filePath.write(f"{draftPicks[pickIdx]['player_id']}\n")


print("Done Loading Sleeper API calls. Saved as .json in ./APIcalls/sleeperDicts/")