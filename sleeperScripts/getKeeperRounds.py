import json

print("Getting Roster")
print("Loading Sleeper json files")
sleeperDictFP = "/Users/joead/Documents/joey-home/APIcalls/sleeperDicts/"
sleeperUserNameFile = open("/Users/joead/Documents/FantasyFootball/sleeperUserName.txt")
userName = sleeperUserNameFile.read()
sleeperUserIdFile = open("/Users/joead/Documents/FantasyFootball/sleeperUserId.txt")
user_id = sleeperUserIdFile.read()
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
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/draftPicks2024.json") as filePath:
         draftPicks = json.load(filePath)
    #draft.append(draftPicks[0])    
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/draftPlayerIdx2024.txt") as filePath:
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
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/keeperRounds.txt","w") as filePath:
        filePath.write(f"{'owner,name,position,keeper round'}\n")
        for teamIdx in range(numTeams):
            ownerId = rosters[teamIdx]['owner_id']
            idx = userIdx.index(ownerId)
            ownerName = usersInfo[idx]['display_name']
            teamRosters[leagueName[leagueIdx]][ownerName] = {}
            rosterMsk = []
            rosterMsk.append(rosters[teamIdx]["players"])
            rosterMsk = rosterMsk[0]
            numPlayers = len(rosterMsk)
            lastName = []
            firstName = []
            position = []
            keeperRnd = []
            for playerIdx in range(numPlayers):
                playerId = rosterMsk[playerIdx]
                lastNameMsk = players[playerId]["last_name"]
                firstNameMsk = players[playerId]["first_name"]
                positionMsk = players[playerId]["position"]
                lastName.append(lastNameMsk)
                firstName.append(firstNameMsk)
                position.append(positionMsk)                
                try:
                    idx = draftPlayerIdx.index(playerId)
                    keeperRndMsk = draftPicks[idx]['round'] - 1
                    keeperRnd.append(keeperRndMsk)
                except:
                    keeperRndMsk = 16
                    keeperRnd.append(16)
                filePath.write(f"{ownerName + ',' + firstNameMsk + ' ' + lastNameMsk + ',' + positionMsk + ',' + str(keeperRndMsk)}\n")

        teamRosters[leagueName[leagueIdx]][ownerName]['lastName'] = lastNameMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['firstName'] = firstNameMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['position'] = positionMsk
        teamRosters[leagueName[leagueIdx]][ownerName]['keeperRounds'] = keeperRndMsk
    with open(sleeperDictFP + userName + "/" + leagueName[leagueIdx] + "/keeperRounds.json","w") as filePath:
            json.dump(teamRosters, filePath)




    









