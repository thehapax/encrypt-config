import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from static_ob import l2
from ccxt_exchange_test import get_test_l2ob

from bitshares import BitShares
from bitshares.market import Market
import time

def plot_orderbook(l2):
    # get order book and visualize quickly with matplotlib.
    plt.style.use('ggplot')
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out
    ob_depth = 10

    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    bid_df['timestamp'] = l2['timestamp']
    bid_df['type'] = 'bid'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    ask_df['timestamp'] = l2['timestamp']
    ask_df['type'] = 'ask'

    ob_df = pd.concat([ask_df.head(ob_depth), bid_df.head(ob_depth)])
    ob_df.sort_values('price', inplace=True, ascending=False)
    print(tabulate(ob_df, headers="keys"))

    ob_df['colors'] = 'g'
    ob_df.loc[ob_df.type=='ask', 'colors'] = 'r'

    # for use with python 3.6.8
    price = ob_df.price.to_numpy()
    vol = ob_df.vol.to_numpy()
    #plt.bar(price, vol, color=ob_df.colors)

    # use python 3.7, error with python 3.6.8
    # plt.bar(ob_df.price, ob_df.vol, color=ob_df.colors)
    # plt.show()
    return ob_df


if __name__ == '__main__':
    # CEX orderbook from cointiger

    #symbol = 'BTC/USDT'
    #symbol = 'BTC/BitCNY', 'ETH/BitCNY', 'BTS/ETH'
    symbol = 'BTS/BTC'

#    l2_ob = get_test_l2ob(symbol)
#    ob_df = plot_orderbook(l2_ob)

    # bitshares DEX
    bs = BitShares()
    bs.wallet.unlock("hellobot123")
    print(bs.wallet.getPublicKeys(current=True))

    # bitshares order engine.  get_market_orders (or use pyBitshares direct)
    bs_symbol = "BTS:OPEN.BTC"
    #bs_symbol = "OPEN.BTC:BTS"

    bs_market = Market(bs_symbol)
    print(bs_market.ticker())

    print("================")

    # {'bids': [0.003679 USD/BTS (1.9103 USD|519.29602 BTS)
    # get bitshares order book for current market
    bs_orderbook = bs_market.orderbook(limit=5)
    # print("Bitshares Order book for ")
    print(bs_orderbook)

    print("=====================")

    price_vol = list()
    for i in range(len(bs_orderbook['asks'])):
        #price = bs_orderbook['asks'][i]['price']
        price = bs_orderbook['asks'][i].get('price')
        print(price)
        invert_price = 1/price
        vol = bs_orderbook['asks'][i]['quote']  # is this the actual volume?
        price_vol.append([price, invert_price, vol['amount']])

    ask_df = pd.DataFrame(price_vol)
    ask_df.columns = ['price', 'invert', 'vol']
    ask_df['timestamp'] = int(time.time())
    ask_df['type'] = 'ask'

    price_vol = list()
    for j in range(len(bs_orderbook['bids'])):
        price = bs_orderbook['bids'][j]['price']
        invert_price = 1/price
        vol = bs_orderbook['bids'][j]['quote']  # is this the actual volume?
        price_vol.append([price, invert_price, vol['amount']])

    bid_df = pd.DataFrame(price_vol)
    bid_df.columns = ['price', 'invert', 'vol']
    bid_df['timestamp'] = int(time.time())
    bid_df['type'] = 'bid'

    bts_df = pd.concat([ask_df, bid_df])
    print(bts_df)


#    ob_df = plot_orderbook(l2) # static orderbook for testing
# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
# https://stackoverflow.com/questions/13187778/convert-pandas-dataframe-to-numpy-array
# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.plot.bar.html

