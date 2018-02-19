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
        print("Morningstar rates {0} at a {1} out of 5".format(
            symbol, ms_rating))
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
    print("Morningstar reports {0} sustainability for {1}.".format(
        sus_rating, symbol))
    return


# TODO: Instead of just tech, generalize this to take certain cateogry
# argument(s)
@cli.command("get-ranked-tech-etfs")
@click.option('--limit', default=25)
def get_ranked_tech_etfs(limit):
    etf_symbol_list = get_all_tech_etfs(limit)

    ranked_etfs = []
    if len(etf_symbol_list) == 0:
        print("No symbols found.")
        return

    # We want good ranks to be high numbers (5 max) so we need to convert some
    # rankings
    sus_rank_dict = {
            "HIGH":5,
            "ABOVE AVERAGE":4,
            "AVERAGE":3,
            "BELOW AVERAGE":2,
            "LOW":1,
            "NO RATING":0
    }
    
    zacks_rank_dict = {
            "1 - Strong Buy":5,
            "2 - Buy":4,
            "3 - Hold":3,
            "4 - Sell":2,
            "5 - Strong Sell":1
    }
    
    for symbol in etf_symbol_list:
        # We determine the overall ranking by checking the ratings for Zacks,
        # Morningstar, and the sustainability reported by Morningstar
        # We could weight each thing by some arbitrary amount but everything
        # will be weighted the same for now
        zacks_rating = check_zacks_rating(symbol)
        ms_rating = check_ms_rating(symbol)
        ms_sus = check_ms_sustainability(symbol)

        # Set it to 0 if it's not defined, convert to number otherwise
        if len(zacks_rating) == 0:
            zacks_rating = 0
        else:
            zacks_rating = zacks_rank_dict[zacks_rating]
        
        if ms_rating is None:
            ms_rating = 0
        else:
            ms_rating = int(ms_rating)
        
        if ms_sus is None:
            ms_sus = 0
        else:
            ms_sus = sus_rank_dict[ms_sus]

        overall_rating = zacks_rating + ms_rating + ms_sus
        ranked_etfs.append((symbol, overall_rating))
    ranked_etfs.sort(key=lambda tup: tup[1], reverse=True)
    for symbol, rank in ranked_etfs:
        print("{0}: {1} / 15".format(symbol, rank))


def get_all_tech_etfs(limit):
    etf_symbol_list = []
    page = requests.get((
            "http://etfdb.com/data_set/?tm=1725&"
            "cond={%22by_category%22:15}&"
            "no_null_sort=true&"
            "count_by_id=&"
            "sort=ytd_percent_return&"
            "order=desc&"
            "limit=" + str(limit) +
            "&offset=0"))
    if page.status_code != 200:
        logger.debug("ETFdb is returning status code {0}".format(
            page.status_code))
        return etf_symbol_list
    json = page.json()['rows']
    for data in json:
        # weird combo of HTML and JSON so we have to hope the HTML doesn't
        # change...
        etf_symbol_list.append(data['symbol'].split("/")[2])
    return etf_symbol_list
    

def check_zacks_rating(symbol):
    page = requests.get("https://www.zacks.com/funds/etf/" + symbol +
            "/profile")

    if page.status_code != 200:
        logger.debug("Zacks is returning status code {0}".format(
            page.status_code))
        return None

    soup = BeautifulSoup(page.text, 'html.parser')
    rating_text = soup.find(class_='zr_rankbox').getText()
    # The below line is kinda gross but it turns the rating text (something
    # like '\nZacks ETF Rank  1 - Strong Buy 1 \xa0 \xa0 \xa0 \xa0\n')
    # into '1 - Strong Buy'. Since the ratings are things like Hold, Buy,
    # Strong Sell, etc, we can't just get the second-to last item if we split
    # the string on spaces.
    return rating_text.replace(u'\xa0', u'').strip().split(
            "Zacks ETF Rank  ")[1][:-2].strip()


def check_ms_rating(symbol):
    page = requests.get(
            "http://www.morningstar.com/api/v1/security-identifier/" + symbol)

    if page.status_code != 200:
        logger.debug("Morningstar is returning status code {0}".format(
            page.status_code))
        return None

    return page.json()['starRating']


def check_ms_sustainability(symbol):
    page = requests.get("http://etfs.morningstar.com/etfq/esg-etf?&t=ARCX:" +
            symbol + (
                "&region=usa&"
                "culture=en-US&"
                "version=RET&"
                "cur=&"
                "test=QuoteiFrame&"
                "e=eyJlbmMiOiJBMTI4R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.tSDHKSXdLz9Z-"
                "95RIt28jRBS2bycBEfA83K4AAWtpDsmwZ3eZJuOatSWRjLITgGJVDutGigpcxJ"
                "x7ojDFi4SiUq93kz5skXbVz9We3sUV5xXKSDW7W5HTtV0Oh4eSYl4bjf_csXP5"
                "pexU-eAYvofcSrHtmEn_GOcQ4GJA_qzXJc.70cJ7G9sm6MH4gYA.eZUC9ESEz_"
                "SGFNEd4tF5O3eXrS6mKs8-AWDZH4r55aD1Bm0K2R-Na5bOxUmXr2XbGTrkfbi-"
                "-UTrPjvwRxAWYbMIGxs12mKL1etKxdmVImSVhN2bk4WDOfV9Vnotfu0-YigkPJ"
                "HAAPnnB5owMwmWOmSsm-Xxxo-kFLK5C1K3YYBYe2ruwZVxO1rJ6se-ruzjipYA"
                "mRR9vIjxaUvadr0bAOxnS8KbgFIdv5fBILs.nEgzKr6eTtw896WO8yE1mA&_=1"
                "518983228036"))

    if page.status_code != 200:
        logger.debug("Morningstar is returning status code {0}".format(
            page.status_code))
        return None
    
    soup = BeautifulSoup(page.text, 'html.parser')
    # The rating doesn't have a unique ID or class so we have to hope the HTML
    # doesn't change...
    rating_html = soup.find_all(class_='text-margin5 text-size14')
    
    if len(rating_html) == 0:
        return None
    
    return rating_html[0].get_text().strip().upper()

