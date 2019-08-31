import matplotlib.pyplot as plt
from matplotlib import interactive

import pandas as pd
from tabulate import tabulate
from ccxt_exchange_test import get_test_l2ob
from static_ob import l2
from bitshares.market import Market
import time


def plot_orderbook(ob_df, invert: bool):
    # get order book and visualize quickly with matplotlib.
    plt.style.use('ggplot')
    bar_width = 100

    ob_df['colors'] = 'g'
    ob_df.loc[ob_df.type == 'asks', 'colors'] = 'r'

    # for use with python 3.6.8
    price = ob_df.price.to_numpy()
    vol = ob_df.vol.to_numpy()
    invert_price = ob_df.invert.to_numpy()  # use if needed

    if invert is True:
        plt.bar(invert_price, vol, color=ob_df.colors, width=bar_width)
    else:
        plt.bar(price, vol, color=ob_df.colors, width=bar_width)

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
    print(tabulate(ob_df, headers="keys"))
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


def get_bts_ob_data(bs_symbol, depth: int):
    bs_market = Market(bs_symbol)
    # get bitshares order book for current market
    bs_orderbook = bs_market.orderbook(limit=depth)
    ask_df = get_bts_orderbook_df(bs_orderbook, 'asks')
    bid_df = get_bts_orderbook_df(bs_orderbook, 'bids')
    bts_df = pd.concat([ask_df, bid_df])
    bts_df.sort_values('price', inplace=True, ascending=False)
    print(tabulate(bts_df, headers="keys"))
    return bts_df


def plot_df(df, title: str, symbol: str, invert: bool):
    plt = plot_orderbook(df, invert=invert)
    plt.title(title + ":"+ symbol)
    plt.ylabel('volume')
    plt.xlabel('price')

if __name__ == '__main__':
    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    #symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'

    #symbol = 'BTS/BTC'
    l2_ob = get_test_l2ob(symbol)
    cex_df = get_cex_data(l2_ob, depth=3)
    #cex_df = get_cex_data(l2) # static data
    plt.figure(1)
    plot_df(cex_df, title="cex cointiger", symbol=symbol, invert=False)

    # bitshares order engine.  get_market_orders (or use pyBitshares direct)
    #bs_symbol = "BTS/OPEN.BTC"  # keep same order as cex exchange.
    bs_symbol = "OPEN.BTC/USD"
    bts_df = get_bts_ob_data(bs_symbol, depth=3)
    plt.figure(2)
    plot_df(bts_df, title="bitshares dex", symbol=bs_symbol, invert=False)

    plt.show()
    input()


# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

