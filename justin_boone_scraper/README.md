# Justin Boone fantasy scraper

This project scrapes Justin Boone's Yahoo fantasy football content and stores the table data into CSV files in the `data/` directory.

## Included sources

- Weekly rankings (latest canonical Yahoo article, with redirect handling)
- Weekly trade value charts (QB, RB, WR, TE)
- Dynasty trade value charts (QB, RB, WR, TE, draft picks)

## Run once

```bash
python scraper.py --once
```

## Run continuously

```bash
python scraper.py
```

The scheduler uses this cadence:

- Weekly rankings: every 6 hours
- Weekly trade values: every 12 hours
- Dynasty trade values: every 30 days

## Output files

The script writes CSV files under `data/` named like:

- `justin_boone_rankings_latest.csv`
- `justin_boone_trade_value_qb.csv`
- `justin_boone_trade_value_rb.csv`
- `justin_boone_trade_value_wr.csv`
- `justin_boone_trade_value_te.csv`
- `justin_boone_dynasty_qb.csv`
- `justin_boone_dynasty_rb.csv`
- `justin_boone_dynasty_wr.csv`
- `justin_boone_dynasty_te.csv`
- `justin_boone_dynasty_draft_picks.csv`

## Why this is future-proof

The weekly rankings page has a random 9-digit suffix. The scraper keeps a list of known seed URLs and follows redirects to the current canonical Yahoo article, then stores that resolved URL for future runs. If a new week changes the canonical article, the next scrape automatically picks up the new article without hardcoding a new random suffix.

Trade value and dynasty URLs are discovered via Yahoo search fallback if the direct URL pattern changes.
