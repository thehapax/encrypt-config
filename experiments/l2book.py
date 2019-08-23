import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

from static_ob import l2
from ccxt_exchange_test import get_test_l2ob

def plot_orderbook(l2):
    # get order book and visualize quickly with matplotlib.
    plt.style.use('ggplot')
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out
    ob_depth = 20

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
    return ob_df

if __name__ == '__main__':

    symbol = 'BTC/USDT'
    log.info("symbol: {} ".format(symbol))
    l2_ob = get_test_l2ob(symbol)

    ob_df = plot_orderbook(l2)
#   ob_df = plot_orderbook(l2_ob)

    ob_df['colors'] = 'g'
    ob_df.loc[ob_df.type=='ask', 'colors'] = 'r'
    plt.bar(ob_df.price, ob_df.vol, color=ob_df.colors)
    plt.show()



#asks = ob_df[ob_df['type'].str.contains("ask", na=False)]
#print(asks)

#ob_df.plot(x='price', y='vol', kind='bar')
#plt.show()

# Useful https://robertmitchellv.com/blog-bar-chart-annotations-pandas-mpl.html
