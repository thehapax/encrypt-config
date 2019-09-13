import matplotlib.pyplot as plt
from multiprocessing import freeze_support

import pandas as pd
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

def plot_h(ax, price, vol, bwidth, colors, align):
    ax.barh(price, vol, bwidth, color=colors, align=align)

def plot_v(ax, price, vol, bwidth, colors, align):
    ax.bar(price, vol, bwidth, color=colors, align=align)


def plot_orderbook(ax, ob_df, invert: bool, barwidth: float):
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
        plot_h(ax, plot_price, vol, bwidth, ob_df.colors, 'center')
    else:
        plot_v(ax, plot_price, vol, bwidth, ob_df.colors, 'center')

    # use below line if python 3.7, error with python 3.6.8
    # plt.bar(ob_df.price, ob_df.vol, color=ob_df.colors)
    return plt


def plot_df(ax1, df, title: str, symbol: str, invert: bool, bar_width: float):
    plt = plot_orderbook(ax1, df, invert=invert, barwidth=bar_width)
    plt.title(title + ":"+ symbol)
    plt.ylabel('volume')
    plt.xlabel('price')


def plot_exchange_pair(cex_df, bts_df):
    plt.cla()
    plt.figure()
    ax1 = plt.subplot(2,1,1)
    plot_df(ax1, cex_df, title="cex cointiger", symbol=symbol, invert=False, bar_width=0.3)
    ax2 = plt.subplot(2,1,2)
    plot_df(ax2, bts_df, title="bitshares dex", symbol=bts_symbol, invert=False, bar_width=10)
    plt.tight_layout()


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
    return bts_df


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
    return cex_df, bts_df


def spread_opp(bts_df, cex_df):
#   bts_spread_df = get_bts_static_ob_data(bts_df, 1)
    bts_spread_df = get_bts_ob_data(bts_df, 1)
    print("----- bts spread df ------")
    print(bts_spread_df)
    cex_spread_df = get_cex_data(cex_df, depth=1)
    print("----- cex spread df ------")
    print(cex_spread_df)
    calculate_arb_opp(cex_spread_df, bts_spread_df)


if __name__ == '__main__':
    plt.ion()

    freeze_support() # needed for multiprocessing (if needed)

    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    bts_symbol = "OPEN.BTC/USD"
    depth = 5

    bts_market = setup_bitshares_market(bts_symbol)
    ccxt_ex = get_ccxt_module()
    # authenticate once: hold connection open for repolling cex continously

    for a in range(1, 10):
        cex_df, bts_df = get_dynamic_data(ccxt_ex, symbol, bts_market,  depth)
        plot_exchange_pair(cex_df, bts_df)
        plt.pause(2)
        plt.draw()


    # continously poll every 3 seconds or whatever rate limit
    # to monitor for best opportunities
    # can matplot lib update continously?
    # use multiprocess module?



# symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'
# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

"""
pip install dash==0.42.0
pip install dash-core-components==0.47.0
pip install dash-html-components==0.16.0
pip install dash-renderer==0.23.0
pip install dash-table==3.6.0
"""
