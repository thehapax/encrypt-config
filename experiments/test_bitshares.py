from bitshares import BitShares
from bitshares.instance import set_shared_bitshares_instance
from bitshares.market import Market
import pandas as pd
import time, os

from ascii_graph import Pyasciigraph
from ascii_graph.colors import *


def setup_bitshares_market(bts_symbol):
    bitshares_instance = BitShares(
        "wss://siliconvalley.us.api.bitshares.org/ws",
#        "wss://new-york.us.api.bitshares.org/ws",
        nobroadcast=True  # <<--- set this to False when you want to fire!
    )
    set_shared_bitshares_instance(bitshares_instance)
    bts_market = Market(
        bts_symbol,
        bitshares_instance=bitshares_instance
    )
    return bts_market


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



if __name__ == '__main__':

    depth = 5
    bts_symbol = "OPEN.BTC/USD"
    bts_market = setup_bitshares_market(bts_symbol)

    ob_color = {'asks': Red, 'bids': Gre, 'mirror_asks': Yel, 'mirror_bids': Blu}
    os.environ['TZ'] = 'UTC'
    time.tzset()
    title = "Dynamic Graph: " + bts_symbol

    graph = Pyasciigraph(
        line_length=120,
        min_graph_length=50,
        separator_length=4,
        multivalue=True,
        human_readable='si',
        float_format='{0:,.6f}',
    )

    while True:
        # loop forever, keep getting latest order book and display
        bts_df = get_bts_ob_data(bts_market, depth=depth)
        df = bts_df[['price', 'vol', 'type']]

        df.loc[df['type'] == 'asks', 'type'] = ob_color['asks']
        df.loc[df['type'] == 'bids', 'type'] = ob_color['bids']
        tuple_data = [tuple(x) for x in df.values]

        os.system("clear")
        print(time.ctime())
        for line in graph.graph(label=title, data=tuple_data):
            print(line)
        print(bts_df)
        time.sleep(2)