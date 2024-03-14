import json

"""
Title
"""
print("Running Weekly Projections")
print("Loading Sleeper json files")
sleeperDictFP = "/Users/joey/Documents/github/joey-home/APIcalls/sleeperDicts/"
userName = "joeyad"
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
for x in range(numLeagues):
    leagueName = allLeagues[x]['name']
    #Load sleeper leagues and matchups
    leagueName = leagueName.replace(" ", "_")
    with open(sleeperDictFP + userName + "/" + leagueName + "/draftInfo.json") as filePath:
          draftInfo = json.load(filePath)
    with open(sleeperDictFP + userName + "/" + leagueName + "/draftPicks.json") as filePath:
          draftPicks = json.load(filePath)    
    with open(sleeperDictFP + userName + "/" + leagueName + "/leagueInfo.json") as filePath:
          leagueInfo = json.load(filePath)
    with open(sleeperDictFP + userName + "/" + leagueName + "/rosters.json") as filePath:
          rosters = json.load(filePath)
    week = str(state['week'])
    with open(sleeperDictFP + userName + "/" + leagueName + "/matchup_week" + week + ".json") as filePath:
          matchup = json.load(filePath)  

print("Done Loading json files")  
         