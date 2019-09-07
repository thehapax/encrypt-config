import matplotlib.pyplot as plt
from matplotlib import interactive

import multiprocessing as mp
from multiprocessing import freeze_support

import pandas as pd
from tabulate import tabulate
from ccxt_exchange_test import get_test_l2ob, read_dict, get_ccxt_module

from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance
from bitshares.market import Market
from bitshares.price import Price
from bitshares.amount import Amount

import time
import logging

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def setup_bitshares_market(bts_symbol):
    bitshares_instance = BitShares(
        "wss://losangeles.us.api.bitshares.org/ws",
        nobroadcast=True  # <<--- set this to False when you want to fire!
    )
    set_shared_bitshares_instance(bitshares_instance)
    bts_market = Market(
        bts_symbol,
        bitshares_instance=bitshares_instance
    )
    return bts_market


#plot_style = 'horizontal'
plot_style = 'vertical'

def plot_h(plt, price, vol, bwidth, colors, align):
    plt.barh(price, vol, bwidth, color=colors, align=align)

def plot_v(plt, price, vol, bwidth, colors, align):
    plt.bar(price, vol, bwidth, color=colors, align=align)


def plot_orderbook(ob_df, invert: bool, barwidth: float):
    # get order book and visualize quickly with matplotlib.
    plt.style.use('ggplot')
    bwidth = barwidth
    if bwidth is None:
        bwidth = 0.1

    ob_df['colors'] = 'g'
    ob_df.loc[ob_df.type == 'asks', 'colors'] = 'r'

    # for use with python 3.6.8
    price = ob_df.price.to_numpy()
    vol = ob_df.vol.to_numpy()
    invert_price = ob_df.invert.to_numpy()  # use if needed

    plot_price = price
    if invert is True:
        plot_price = invert_price

    if plot_style is 'horizontal':
        plot_h(plt, plot_price, vol, bwidth, ob_df.colors, 'center')
    else:
        plot_v(plt, plot_price, vol, bwidth, ob_df.colors, 'center')

    # use below if python 3.7, error with python 3.6.8
    # plt.bar(ob_df.price, ob_df.vol, color=ob_df.colors)
    return plt


def get_cex_data(l2, depth: int):
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out

    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    bid_df['invert'] = 1/bid_df['price']
    bid_df['timestamp'] = l2['timestamp']
    bid_df['type'] = 'bids'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    ask_df['invert'] = 1/ask_df['price']
    ask_df['timestamp'] = l2['timestamp']
    ask_df['type'] = 'asks'

    ob_df = pd.concat([ask_df.head(depth), bid_df.head(depth)])
    ob_df.sort_values('price', inplace=True, ascending=False)
#   print("------- cex data --------")
#   print(tabulate(ob_df, headers="keys"))
    return ob_df


def get_bts_orderbook_df(ob, type, vol2: bool):
    price_vol = list()
    if vol2:
        for i in range(len(ob[type])):
            price = ob[type][i]['price']
            invert_price = 1/price
            vol = ob[type][i]['quote']
            vol2 = ob[type][i]['base']  # is this the actual volume?
            price_vol.append([price, vol['amount'], vol2['amount'], invert_price])

        df = pd.DataFrame(price_vol)
        df.columns = ['price', 'vol', 'vol_base', 'invert']
    else:
        for i in range(len(ob[type])):
            price = ob[type][i]['price']
            invert_price = 1/price
            vol = ob[type][i]['quote']
            price_vol.append([price, vol['amount'], invert_price])
        df = pd.DataFrame(price_vol)
        df.columns = ['price', 'vol', 'invert']

    df['timestamp'] = int(time.time())
    df['type'] = type
    return df


def get_bts_ob_data(bts_market, depth: int):
    vol2 = False
    # get bitshares order book for current market
    bts_orderbook = bts_market.orderbook(limit=depth)
    ask_df = get_bts_orderbook_df(bts_orderbook, 'asks', vol2)
    bid_df = get_bts_orderbook_df(bts_orderbook, 'bids', vol2)
    bts_df = pd.concat([ask_df, bid_df])
    bts_df.sort_values('price', inplace=True, ascending=False)
#    print(tabulate(bts_df, headers="keys")) # print bts orderbook
#    bts_df.to_csv("static-bts-ob.csv")
    return bts_df


def plot_df(df, title: str, symbol: str, invert: bool, bar_width: float):
    plt = plot_orderbook(df, invert=invert, barwidth=bar_width)
    plt.title(title + ":"+ symbol)
    plt.ylabel('volume')
    plt.xlabel('price')


def calculate_arb_opp(cex_df, bts_df):  # calculate arbitrage opportunity
    log.info("Calculate Arbitrage Opportunity")
    # look at lowest ask and highest bid
    # if dex ask price is > cex ask,  take cex ask and sell on dex. (account for fees)
    # assumes spread on cex is narrower than dex
    # bids? if cex bid > dex bid, take cex bid and list bid on dex. (+ fees)
    cex_ask = float(cex_df[cex_df['type'] == 'asks'].price)
    dex_ask = float(bts_df[bts_df['type'] == 'asks'].price)

    cex_bid = float(cex_df[cex_df['type'] == 'bids'].price)
    dex_bid = float(bts_df[bts_df['type'] == 'bids'].price)

    if dex_ask > cex_ask:
        log.info("take cex ask, make on dex")
        # buy on cex, sell on dex at same price - fees
        print("cex ask: ", cex_ask, "bts ask: ", dex_ask)

    if cex_bid > dex_bid:
        log.info("take cex bid and list bid on dex")
        print("cex bid: ", cex_bid, "dex bid: ", dex_bid)
    # add fees! calculation


def get_dynamic_data(ccxt_ex, symbol: str, bts_market, depth: int):
    """ get dynamic data"""
    l2_ob = ccxt_ex.fetch_l2_order_book(symbol=symbol, limit=None)
    cex_df = get_cex_data(l2_ob, depth=depth) # dynamic data
    bts_df = get_bts_ob_data(bts_market, depth=depth) # dynamic data
    
    print("----- dynamic cex df ------")
    print(cex_df)
    print("----- dynamic bts df------")
    print(bts_df)



if __name__ == '__main__':
    freeze_support() # needed for multiprocessing

    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    bts_symbol = "OPEN.BTC/USD"
    depth = 5

    bts_market = setup_bitshares_market(bts_symbol)
    ccxt_ex = get_ccxt_module()

    # authenticate once: hold connection open for repolling cex continously

    get_dynamic_data(ccxt_ex, symbol, bts_market,  depth)


    # continously poll every 3 seconds or whatever rate limit
    # to monitor for best opportunities
    # can matplot lib update continously?
    # use multiprocess module?



# symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'
# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

