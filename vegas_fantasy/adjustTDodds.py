import csv

def american_to_prob(odds):
    """
    Convert American odds to implied probability.
    """
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def read_csv_as_matrix(filename):
    """
    Reads a CSV file and returns each column as a separate list variable.
    Returns: player_names, values, over_odds, under_odds
    """
    player_names = []
    tds = []
    over_odds = []
    under_odds = []
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 4:
                player_names.append(row[0])
                tds.append(row[1])
                over_odds.append(row[2])
                under_odds.append(row[3])
    return player_names, tds, over_odds, under_odds

def adjust_probabilities(over_probs, under_probs):
    """
    Adjusts the probabilities so that they sum to 1 for each player.
    Returns two lists: over_odds_prob_adj, under_odds_prob_adj
    """
    over_odds_prob_adj = []
    under_odds_prob_adj = []
    for over, under in zip(over_probs, under_probs):
        total = over + under
        if total == 0:
            over_adj = 0
            under_adj = 0
        else:
            over_adj = over / total
            under_adj = under / total
        over_odds_prob_adj.append(over_adj)
        under_odds_prob_adj.append(under_adj)
    return over_odds_prob_adj, under_odds_prob_adj

filename = 'c:/Users/joead/Documents/joey-home/vegas_fantasy/RegularSeasonRushingTDs.csv'
player_names, tds, over_odds, under_odds = read_csv_as_matrix(filename)

# Convert odds to probability
over_odds_prob = [american_to_prob(odds) for odds in over_odds]
under_odds_prob = [american_to_prob(odds) for odds in under_odds]

over_odds_prob_adj = adjust_probabilities(over_odds_prob, under_odds_prob)
under_odds_prob_adj = adjust_probabilities(over_odds_prob, under_odds_prob)