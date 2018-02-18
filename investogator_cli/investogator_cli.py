import click
import json
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

@click.group()
def cli():
    pass

@cli.command("get-ratings")
@click.argument('symbol', nargs=1)
def get_ratings(symbol):
    if symbol is None:
        print("No symbol supplied!")
        return

    zacks_rating = check_zacks_rating(symbol)
    if zacks_rating is None:
        print("Can't reach Zacks at the moment.")
    else:
        print("Zacks rates {0} at {1}".format(symbol, zacks_rating))

    ms_rating = check_ms_rating(symbol)
    if ms_rating is None:
        print("Can't reach Morningstar at the moment.")
    elif ms_rating == -1:
        print("{0} doesn't seem to have a rating.".format(symbol))
    else:
        print("Morningstar rates {0} at a {1} out of 5".format(symbol, ms_rating))
    return

@cli.command("get-sustainability")
@click.argument('symbol', nargs=1)
def get_sustainability(symbol):
    if symbol is None:
        print("No symbol supplied!")
        return

    sus_rating = check_ms_sustainability(symbol)
    if sus_rating is None:
        print("Can't find the sustainability rating for {0}".format(symbol))
        return
    print("Morningstar reports {0} sustainability for {1}.".format(sus_rating, symbol))
    return

def check_zacks_rating(symbol):
    page = requests.get("https://www.zacks.com/funds/etf/" + symbol + "/profile")

    if page.status_code != 200:
        logger.debug("Zacks is returning status code {0}".format(page.status_code))
        return None

    soup = BeautifulSoup(page.text, 'html.parser')
    rating_text = soup.find(class_='zr_rankbox').getText()
    # The below line is kinda gross but it turns the rating text
    # (something like '\nZacks ETF Rank  1 - Strong Buy 1 \xa0 \xa0 \xa0 \xa0\n')
    # into '1 - Strong Buy'. Since the ratings are things like Hold, Buy, Strong
    # Sell, etc, we can't just get the second-to last item if we split the 
    # string on spaces.
    return rating_text.replace(u'\xa0', u'').strip().split("Zacks ETF Rank  ")[1][:-2]

def check_ms_rating(symbol):
    page = requests.get("http://www.morningstar.com/api/v1/security-identifier/" + symbol)

    if page.status_code != 200:
        logger.debug("Morningstar is returning status code {0}".format(page.status_code))
        return None

    return page.json()['starRating']

def check_ms_sustainability(symbol):
    page = requests.get("http://etfs.morningstar.com/etfq/esg-etf?&t=ARCX:" + symbol + "&region=usa&culture=en-US&version=RET&cur=&test=QuoteiFrame&e=eyJlbmMiOiJBMTI4R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.tSDHKSXdLz9Z-95RIt28jRBS2bycBEfA83K4AAWtpDsmwZ3eZJuOatSWRjLITgGJVDutGigpcxJx7ojDFi4SiUq93kz5skXbVz9We3sUV5xXKSDW7W5HTtV0Oh4eSYl4bjf_csXP5pexU-eAYvofcSrHtmEn_GOcQ4GJA_qzXJc.70cJ7G9sm6MH4gYA.eZUC9ESEz_SGFNEd4tF5O3eXrS6mKs8-AWDZH4r55aD1Bm0K2R-Na5bOxUmXr2XbGTrkfbi--UTrPjvwRxAWYbMIGxs12mKL1etKxdmVImSVhN2bk4WDOfV9Vnotfu0-YigkPJHAAPnnB5owMwmWOmSsm-Xxxo-kFLK5C1K3YYBYe2ruwZVxO1rJ6se-ruzjipYAmRR9vIjxaUvadr0bAOxnS8KbgFIdv5fBILs.nEgzKr6eTtw896WO8yE1mA&_=1518983228036")

    if page.status_code != 200:
        logger.debug("Morningstar is returning status code {0}".format(page.status_code))
        return None
    
    soup = BeautifulSoup(page.text, 'html.parser')
    # The rating doesn't have a unique ID or class so we have to hope the HTML doesn't change...
    rating_html = soup.find_all(class_='text-margin5 text-size14')
    
    if len(rating_html) == 0:
        return None
    
    return rating_html[0].get_text().strip().upper()
