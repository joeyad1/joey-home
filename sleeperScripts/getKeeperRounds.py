import json

print("Getting Roster")
print("Loading Sleeper json files")
sleeperDictFP = "/Users/joey/Documents/github/joey-home/APIcalls/sleeperDicts/"
userName = "joeyad"
userID = "439870479407247360"
with open(sleeperDictFP + userName + "/userInfo.json") as filePath:
          userInfo = json.load(filePath)
with open(sleeperDictFP + userName + "/allLeagues.json") as filePath:
          allLeagues = json.load(filePath)
with open(sleeperDictFP + "/sleeperNFLState.json") as filePath:
          state = json.load(filePath)
with open(sleeperDictFP + "/players.json") as filePath:
          players = json.load(filePath)

numLeagues = len(allLeagues)
leagueID = []
leagueName = []
roster = {}
ownerId = []
ownerName = []
draft = []
teamRosters = {}
for leagueIdx in range(numLeagues):
    leagueNameMsk = allLeagues[leagueIdx]['name']
    #Load sleeper leagues and matchups
    leagueName.append(leagueNameMsk.replace(" ", "_"))
    if leagueName[leagueIdx] == 'The_Lamb': #Skip over new league
        continue
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/draftInfo.json") as filePath:
        draftInfo = json.load(filePath)
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/draftPicks2023.json") as filePath:
         draftPicks = json.load(filePath)
    #draft.append(draftPicks[0])    
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/draftPlayerIdx2023.txt") as filePath:
        draftPlayerIdx = filePath.read()
        draftPlayerIdx = draftPlayerIdx.split("\n")
    #print(draftPlayerIdx)
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/rosters.json") as filePath:
        rosters = json.load(filePath)
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/usersInfo.json") as filePath:
        usersInfo = json.load(filePath)
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/userInfoIdx.txt") as filePath:
        userIdx = filePath.read()
        userIdx = userIdx.split("\n")
    numTeams = len(rosters)
    teamRosters[leagueName[leagueIdx]] = {}
    for teamIdx in range(numTeams):
        ownerId = rosters[teamIdx]['owner_id']
        idx = userIdx.index(ownerId)
        ownerName = usersInfo[idx]['display_name']
        teamRosters[leagueName[leagueIdx]][ownerName] = {}
        rosterMsk = []
        rosterMsk.append(rosters[teamIdx]["players"])
        rosterMsk = rosterMsk[0]
        numPlayers = len(rosterMsk)
        lastNameMsk = []
        firstNameMsk = []
        positionMsk = []
        keeperRndMsk = []
        for playerIdx in range(numPlayers):
            playerId = rosterMsk[playerIdx]
            lastNameMsk.append(players[playerId]["last_name"])
            firstNameMsk.append(players[playerId]["first_name"])
            positionMsk.append(players[playerId]["position"])
            try:
                idx = draftPlayerIdx.index(playerId)
                keeperRndMsk.append(draftPicks[idx]['round'] - 1)
            except:
                keeperRndMsk.append(16)


        teamRosters[leagueName[leagueIdx]][ownerName]['lastName'] = lastNameMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['firstName'] = firstNameMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['position'] = positionMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['keeperRounds'] = keeperRndMsk
        with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/keeperRounds.json","w") as filePath:
            json.dump(teamRosters, filePath)




    









