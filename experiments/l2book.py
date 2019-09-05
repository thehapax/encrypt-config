import matplotlib.pyplot as plt
from matplotlib import interactive

import pandas as pd
from tabulate import tabulate
from ccxt_exchange_test import get_test_l2ob, read_dict
from static_ob import l2
from bitshares.market import Market
import time
import logging
import json

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

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


def get_bts_orderbook_df(ob, type):
    price_vol = list()
    for i in range(len(ob[type])):
        price = ob[type][i]['price']
        invert_price = 1/price
        vol = ob[type][i]['quote']
        vol2 = ob[type][i]['base']  # is this the actual volume?
        price_vol.append([price, vol['amount'], vol2['amount'], invert_price])

    df = pd.DataFrame(price_vol)
    df.columns = ['price', 'vol', 'vol_base', 'invert']
    df['timestamp'] = int(time.time())
    df['type'] = type
    return df


def get_bts_ob_data(bts_symbol, depth: int):
    bts_market = Market(bts_symbol)
    # get bitshares order book for current market
    bts_orderbook = bts_market.orderbook(limit=depth)
    ask_df = get_bts_orderbook_df(bts_orderbook, 'asks')
    bid_df = get_bts_orderbook_df(bts_orderbook, 'bids')
    bts_df = pd.concat([ask_df, bid_df])
    bts_df.sort_values('price', inplace=True, ascending=False)
    print(tabulate(bts_df, headers="keys"))
#    bts_df.to_csv("static-bts-ob.csv")
    return bts_df


def get_bts_static_ob_data(df, depth: int):
    print("-------- Entire Static BTS Orderbook DF ------------")
    print(tabulate(df, headers="keys"))
    ask_df = df[df['type'] == 'asks']
    bid_df = df[df['type'] == 'bids']
    ask_head = ask_df.tail(depth)
    bid_head = bid_df.head(depth)
    ask_head = ask_head.sort_values(by='price', ascending=True) # flip so smallest on top
    bid_head = bid_head.sort_values(by='price')
    complete_df = pd.concat([ask_head, bid_head])
    return complete_df


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


def get_static_plot(symbol: str, bts_symbol: str,  depth: int):
    """ get static data from file """
    file_name = 'cex_ob.txt'
    static_cex = read_dict(file_name)
    cex_df = get_cex_data(static_cex, depth=depth)  # static data
    #    cex_df = get_cex_data(l2, depth=depth) # alternative static data

    plt.subplot(2,1,1)
    plot_df(cex_df, title="cex cointiger", symbol=symbol, invert=False, bar_width=0.3)
    # bitshares order engine.  get_market_orders (or use pyBitshares direct)
    # keep same order of pair as cex exchange.

    bts_df = pd.read_csv('static_bts.csv') # static bts data
    bts_spread_df = get_bts_static_ob_data(bts_df, 1)
    print("----- bts spread df ------")
    print(bts_spread_df)
    cex_spread_df = get_cex_data(static_cex, depth=1)
    print("----- cex spread df ------")
    print(cex_spread_df)

    plt.subplot(2,1,2)
    plot_df(bts_df, title="bitshares dex", symbol=bts_symbol, invert=False, bar_width=10)

    calculate_arb_opp(cex_spread_df, bts_spread_df)
    plt.tight_layout()
    plt.show()
    input()


def get_dynamic_plot(symbol: str, bts_symbol: str, depth: int):
    """ get dynamic data"""
    l2_ob = get_test_l2ob(symbol) # dynamic data
    cex_df = get_cex_data(l2_ob, depth=depth) # dynamic data
    bts_df = get_bts_ob_data(bts_symbol, depth=depth) # dynamic data
    print("----- dynamic cex df ------")
    print(cex_df)
    print("----- dynamic bts df------")
    print(bts_df)



if __name__ == '__main__':
    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    bts_symbol = "OPEN.BTC/USD"
    depth = 5

#    get_static_plot(symbol, bts_symbol, depth)
    get_dynamic_plot(symbol, bts_symbol,  depth)

    # continously poll every 3 seconds or whatever rate limit
    # to monitor for best opportunities
    # can matplot lib update continously?
    # use multiprocess module?



# symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'
# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

