import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

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
    plt.clf() # clear figure
    ax1 = plt.subplot(2,1,1)
    plot_df(ax1, cex_df, title="cex cointiger", symbol=symbol, invert=False, bar_width=0.1)
    ax2 = plt.subplot(2,1,2)
    plot_df(ax2, bts_df, title="bitshares dex", symbol=bts_symbol, invert=False, bar_width=10)
    plt.tight_layout()


def get_cex_data(l2, depth: int):
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out

    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    bid_df['timestamp'] = l2['timestamp']
    bid_df['type'] = 'bids'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    ask_df['timestamp'] = l2['timestamp']
    ask_df['type'] = 'asks'

    return ask_df.head(depth), bid_df.head(depth)

#    ob_df = pd.concat([ask_df.head(depth), bid_df.head(depth)])
#    ob_df.sort_values('price', inplace=True, ascending=False)
#    return ob_df


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


def get_dynamic_data(ccxt_ex, symbol: str, bts_market, depth: int):
    """ get dynamic data"""
    l2_ob = ccxt_ex.fetch_l2_order_book(symbol=symbol, limit=None)
    ask_df, bid_df = get_cex_data(l2_ob, depth=depth)  # dynamic data
    cex_df = pd.concat([ask_df.head(depth), bid_df.head(depth)])
    cex_df.sort_values('price', inplace=True, ascending=False)

    bts_df = get_bts_ob_data(bts_market, depth=depth)  # dynamic data
    return cex_df, bts_df


def get_ordersize():
    """
    place holder for getting proposed order size based on reserves
    available on exchange.
    :return:
    """
    return 0.01


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

    cex_spread = cex_ask - cex_bid
    too_small = 10 # random number now, but how do we determine if spread too small
    # percentage of asset?

    if cex_spread < too_small:
        print("cex spread too small: ", cex_spread)
   #     return

    if dex_ask > cex_ask:
        diff = dex_ask - cex_ask
        size = get_ordersize()
        # buy on cex 10189 for 0.01 btc
        # sell on dex at 10399 for 0.01 btc.
        # where dex lowest ask is 10400

        print("profit opportunity for ask trade: ",  diff, "difference * vol =", diff*size)

        my_dex_ask = dex_ask - 0.001*dex_ask # make yours lower than lowest ask by 0.1%
        # make sure that my_dex_ask is crossing into bid? (or should it?)

        # check if my_dex_ask is not lower than highest bid
        print("buy on cex at: ", cex_ask, "sell on dex at: ", my_dex_ask )

#        log.info("take cex ask, make on dex")
        # buy on cex, sell on dex at same price - fees
#        print("cex ask: ", cex_ask, "bts ask: ", dex_ask)

    # todo below
    if cex_bid > dex_bid:
        log.info("take cex bid and list bid on dex")
        print("cex bid: ", cex_bid, "dex bid: ", dex_bid)
    # add fees! calculation


def get_cex_mirror(asks_df, bids_df, asks_bal, bids_bal):
    """
    todo 
    :param cex_df: 
    :param bts_df: 
    :return:
    """
    # normalize volue by placing [0,1] values into 'vol_scaled' column
    scaler = MinMaxScaler()
    asks_df['vol_scaled'] = scaler.fit_transform(asks_df['vol'].values.reshape(-1, 1))
    bids_df['vol_scaled'] = scaler.fit_transform(bids_df['vol'].values.reshape(-1, 1))

    asks_total = asks_df['vol_scaled'].sum()
    bids_total = bids_df['vol_scaled'].sum()

    # distribute balance across volume
    asks_dist = asks_bal/asks_total
    bids_dist = bids_bal/bids_total

    print(f"asks_total: {asks_total}, bids_total: {bids_total}")
    print(f"asks_DIST: {asks_dist}, bids_DIST: {bids_dist}")

    asks_df['vol_scaled'] = asks_df['vol_scaled'].mul(asks_dist)
    bids_df['vol_scaled'] = bids_df['vol_scaled'].mul(bids_dist)

    # remove zero row values for dex_vol
    asks_df = asks_df[asks_df['vol_scaled'] != 0]
    bids_df = bids_df[bids_df['vol_scaled'] != 0]

    # return and place orders on dex.
    return asks_df, bids_df


def single_trade_arb(cex_df, bts_df):
    cex_spread_df = cex_df[cex_df.index == 0]  # get closest bid/ask
    bts_spread_df = bts_df[bts_df.index == 0]
    calculate_arb_opp(cex_spread_df, bts_spread_df)


def get_charts():
    plt.ion()  # interactive plot
    cex_df, bts_df = get_dynamic_data(ccxt_ex, symbol, bts_market, depth)
    # single_trade_arb
    plot_exchange_pair(cex_df, bts_df)
    plt.pause(2)
    plt.draw()


if __name__ == '__main__':

    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    bts_symbol = "OPEN.BTC/USD"
    depth = 5
    bid_bal = 10000 # USDT/bitUSD
    ask_bal = 10  #  BTC

    # testing sample
    b_symbol = 'BTS/BTC'
    cex_pair = b_symbol.split('/')
    ask_symbol = cex_pair[0]
    bid_symbol = cex_pair[1]

#    bts_market = setup_bitshares_market(bts_symbol)
    ccxt_ex = get_ccxt_module()

    print("Free Balance")
    free_bal = ccxt_ex.fetch_free_balance()
    ask_free = free_bal[ask_symbol]
    bid_free = free_bal[bid_symbol]
    print(f"CEX: [{ask_symbol}] ask: {ask_free}, [{bid_symbol}] bid: {bid_free}")


    # authenticate once: hold connection open for repolling cex continously
    # poll for arb opportunities continuously on market
    #   for i in range(1, 5): # short test
    """
    
    while True:
        try:
            l2_ob = ccxt_ex.fetch_l2_order_book(symbol=symbol, limit=None)
            asks, bids = get_cex_data(l2_ob, depth=10)  # dynamic data from cex only

            # order mirroring 
            print("------- get cex mirror ------")
            # get cex modified mirror values for dex
            asks_df, bids_df = get_cex_mirror(asks, bids, ask_bal, bid_bal)

            print("------- Asks_DF DEX mirror ------")
            print(asks_df)
            print("------- Bids_DF DEX mirror ------")
            print(bids_df)

            # todo: calculate percentage offset.

            # todo: check for existing orders, if orders, remove old bts orders
            # todo #1 place the new_bts_orders on the bitshares dex

            # repeat after X time gap or other rule
            # order mirroring

        except Exception as e:
            print(e)
            break
    """


#############################

    # continously poll every 3 seconds or whatever rate limit
    # to monitor for best opportunities
    # can matplot lib update continously?
    # use multiprocess module?

# symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'
# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

