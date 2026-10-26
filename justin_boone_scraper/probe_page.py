import requests
from bs4 import BeautifulSoup

urls = [
    'https://sports.yahoo.com/fantasy/article/fantasy-football-week-7-rankings-from-justin-boone-163325767.html',
    'https://sports.yahoo.com/fantasy/article/week-6-fantasy-football-rankings-from-justin-boone-164604693.html',
    'https://sports.yahoo.com/fantasy/article/2026-trade-value-charts--justin-boones-fantasy-football-quarterback-breakdown-for-week-7-150025496.html',
]

for u in urls:
    print('URL', u)
    r = requests.get(u, timeout=30, headers={'User-Agent':'Mozilla/5.0'})
    print('status', r.status_code)
    print('final', r.url)
    print(r.text[:1800])
    print('\n---\n')
