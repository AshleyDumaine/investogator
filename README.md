Investogator
============

## Purpose
I made this when I wanted to get into investing in ETFs, but wasn't sure which ones were safe to pick
for each category (technology, large cap growth, health/biotech, etc). My dad (who's big on investing)
pointed me to a few sources for getting reviews on ETFs, but these didn't have a free API to query.
Thus, I ended up leveraging BeautifulSoup to get the data I wanted so I wouldn't have to spend hours
checking dozens of ETF symbols across multiple sites.

## What sites does it check?
#### For ratings:
- https://www.zacks.com 
- http://www.morningstar.com

#### For sustainability:
- http://etfs.morningstar.com

## How is the overall rating calculated?
Each of the ratings is on a 1-5 scale with 5 being a strong buy / high sustainability and 1 being a strong 
sell / low sustainability. These numbers are added together for a total out of 15. If data for a rating is
missing, that rating is equal to a 0 instead of assuming a rating.

## Limitations
Right now it's not possible to pick multiple different categories to check the ETF symbols for. Only one
category is expected (e.g. `investogator get-ranked-etfs technology --limit=80`)
