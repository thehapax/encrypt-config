import matplotlib.pyplot as plt
from static_ob import l2
from ccxt_exchange_test import read_dict
from l2book import get_cex_data, plot_df, calculate_arb_opp
from tabulate import tabulate
import pandas as pd


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


def get_static_plot(symbol: str, bts_symbol: str,  depth: int):
    """ get static data from file """
    file_name = 'cex_ob.txt' # static cex data
    static_cex = read_dict(file_name)
    cex_df = get_cex_data(static_cex, depth=depth)  # ccxt static data
    # cex_df = get_cex_data(l2, depth=depth) # alternative static data

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


if __name__ == '__main__':
    # CEX orderbook from cointiger
    symbol = 'BTC/USDT'
    bts_symbol = "OPEN.BTC/USD"
    depth = 5

#    l2_ob = get_test_l2ob(symbol) # static data from ccxt
    get_static_plot(symbol, bts_symbol, depth)