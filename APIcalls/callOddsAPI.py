import json
import requests
import os

"""
Script to used to call Odds API and save as json
the-odds-api.com for betting odds
odds api documenation: https://the-odds-api.com/liveapi/guides/v4/#overview
"""


# The sport key obtained from calling the /sports endpoint. 
# {upcoming} is always valid, returning any live games as well as the next 8 upcoming games across all sports

def get_available_markets(apiKey, sport):
    """
    Fetches and prints available markets for a given sport from the Odds API.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/markets"
    params = {"apiKey": apiKey.strip()}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        markets = response.json()
        print(f"Available markets for {sport}:")
        for m in markets:
            print(f"- {m}")
        return markets
    else:
        print(f"Failed to fetch markets: {response.status_code} {response.text}")
        return []


def get_nfl_player_season_totals(apiKey, sport, regions, markets):
    """
    Calls the Odds API for NFL player season total odds.
    Returns the JSON response.
    """
    print("Calling OddsAPI")
    url = "https://api.the-odds-api.com/v4/sports/" + sport + "/odds"
    oddsParams = {
        "apiKey": apiKey.strip(),
        "regions": regions,
        "markets": markets
    }
    response = requests.get(url, params=oddsParams)
    """response.raise_for_status()"""
    return response.json()

# Example usage:
oddsDictFP = "/Users/joead/Documents/joey-home/APIcalls/oddsDicts/"
if not os.path.isdir(oddsDictFP):
    os.mkdir(oddsDictFP)
oddsApiKeyFN = open("/Users/joead/Documents/FantasyFootball/oddsApiKey.txt")
apiKey = oddsApiKeyFN.read()
sport = "americanfootball_nfl"
regions = "us,us2"

# Fetch and print available markets for the sport
available_markets = get_available_markets(apiKey, sport)
# Example: use a valid market from the list above, e.g., "h2h"
if available_markets:
    markets = available_markets[0]  # Use the first available market as an example
    nfl_odds = get_nfl_player_season_totals(apiKey, sport, regions, markets)
    print(nfl_odds)
    with open(os.path.join(oddsDictFP, f"nfl_{markets}.json"), "w") as f:
        json.dump(nfl_odds, f)
    print(f"Done Loading Odds API calls. Saved as .json in ./APIcalls/oddsDicts/ (market: {markets})")
else:
    print("No available markets found for this sport.")
         