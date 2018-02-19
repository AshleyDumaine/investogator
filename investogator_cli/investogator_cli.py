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


def get_all_etf_categories():
    page = requests.get("http://etfdb.com/etfdb-categories/")
    if page.status_code != 200:
        logger.debug("ETFdb is returning status code {0}".format(
            page.status_code))
        return None
    soup = BeautifulSoup(page.text, 'html.parser')
    # TODO: finish implementing this once I figure out how to get the
    # etfdb-category links


# This allows you to get ranked ETFs depending on which category you're
# interested in (e.g. tech, large cap growth, etc)
# TODO: make it possible to pick multiple categories
# TODO: figure out how to not have to make this dict...
cat_dict = {
        # there is no 1
        "large-cap-blend": 2,
        "large-cap-growth": 3,
        "financials": 4,
        "small-cap-blend": 5,
        "leveraged": 6,
        "japan": 7,
        "energy": 8,
        "emerging-markets": 9,
        # there is no 10
        "large-cap-value": 11,
        "leveraged-commodities": 12,
        "inverse": 13,
        "latin-america": 14,
        "technology": 15,
        "china": 16,
        "foreign-large-cap": 17,
        "mid-cap-blend": 18,
        "precious-metals": 19,
        "commodities": 20,
        "real-estate": 21,
        "consumer-discretionary": 22,
        "government-bonds": 23,
        "utilities": 24,
        "asia-pacific": 25,
        "consumer-staples": 26,
        "small-cap-growth": 27,
        "europe": 28,
        "health-biotech": 29,
        "metals": 30,
        "small-cap-value": 31,
        "leveraged-real-estate": 32,
        "mid-cap-value": 33,
        "oil-gas": 34,
        "mortgage-backed-securities": 35,
        "mid-cap-growth": 36,
        "currency": 37,
        "inflation-protected-bonds": 38,
        "agricultural-commodities": 39,
        "total-bond-market": 40,
        "communications": 41,
        "all-cap": 42,
        "diversified-portfolio": 43,
        "global": 44
}


@cli.command("get-ranked-etfs")
@click.argument('category', nargs=1, type=click.Choice(cat_dict.keys()))
@click.option('--limit', default=25)
def get_ranked_etfs(category, limit):
    # Not quite sure of a good way to get the category ID for now aside from
    # just going into the inspector on each category's page so we have a dict
    # to hold the mappings for now
    etf_symbol_list = get_all_etfs(cat_dict[category], limit)
    get_etf_rank_list(etf_symbol_list)


# We want good ranks to be high numbers (5 max) so we need to convert some
# rankings
sus_rank_dict = {
        "HIGH": 5,
        "ABOVE AVERAGE": 4,
        "AVERAGE": 3,
        "BELOW AVERAGE": 2,
        "LOW": 1,
        "NO RATING": 0
}

zacks_rank_dict = {
        "1 - Strong Buy": 5,
        "2 - Buy": 4,
        "3 - Hold": 3,
        "4 - Sell": 2,
        "5 - Strong Sell": 1
}


def get_etf_rank_list(etf_symbol_list):

    ranked_etfs = []
    if len(etf_symbol_list) == 0:
        print("No symbols found.")
        return

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


def get_all_etfs(category, limit):
    etf_symbol_list = []
    page = requests.get((
            "http://etfdb.com/data_set/?tm=1725&"
            "cond={%22by_category%22:" + str(category) + "}&"
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
    page = requests.get(
        "http://etfs.morningstar.com/etfq/esg-etf?&t=ARCX:" +
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
