import requests
import os
import json

def list_all_sports(api_key):
    url = "https://api.the-odds-api.com/v4/sports"
    params = {"apiKey": api_key.strip()}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        sports = response.json()
        print("Available sports:")
        for sport in sports:
            print(f"- {sport['key']}: {sport['title']}")
        return sports
    else:
        print(f"Failed to fetch sports: {response.status_code} {response.text}")
        return []

def try_nfl_markets(api_key, sport_key="americanfootball_nfl"):
    common_markets = ["h2h", "spreads", "totals", "outrights", "player_props"]
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    for market in common_markets:
        params = {
            "apiKey": api_key.strip(),
            "regions": "us,us2",
            "markets": market
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f"Market '{market}' is valid for {sport_key}.")
        else:
            print(f"Market '{market}' is NOT valid for {sport_key}: {response.status_code} {response.text}")

if __name__ == "__main__":
    api_key_path = os.path.expanduser("~/Documents/FantasyFootball/oddsApiKey.txt")
    with open(api_key_path) as f:
        api_key = f.read()
    print("\n--- Listing all sports ---")
    list_all_sports(api_key)
    print("\n--- Trying common NFL markets ---")
    try_nfl_markets(api_key)