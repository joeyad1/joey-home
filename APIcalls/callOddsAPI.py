import json
import requests
import os

"""
Script to used to call Odds API and save as json
the-odds-api.com for betting odds
odds api documenation: https://the-odds-api.com/liveapi/guides/v4/#overview
"""



print("Calling OddsAPI")
siteURL = "https://api.the-odds-api.com"
YOUR_API_KEY = "9f498ad8e7e06c52cdead0aac4a5733f"
apiKey = YOUR_API_KEY
sports = requests.get(siteURL + "/v4/sports?apiKey=" + YOUR_API_KEY)
oddsDictFP = "/Users/joey/Documents/github/joey-home/APIcalls/oddsDicts/"
if not os.path.isdir(oddsDictFP):
    os.mkdir(oddsDictFP)
with open(oddsDictFP + "/sports.json","w") as filePath:
    json.dump(sports, filePath)

#The sport key obtained from calling the /sports endpoint. 
#{upcoming} is always valid, returning any live games as well as the next 8 upcoming games across all sports
sport = "nfl"
regions = "us,us2"
markets = "h2h"
games = requests.get(siteURL+"/v4/sports/"+sport+"/odds/?apiKey="+apiKey+"&regions="+regions+"&markets="+markets)
games = games.json()


print("Done Loading Odds API calls. Saved as .json in ./APIcalls/oddsDicts/")



