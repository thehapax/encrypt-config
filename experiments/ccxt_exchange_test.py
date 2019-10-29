import logging
import os
import configparser
import ccxt
import json
from ccxt_exchange import CcxtExchange
import time
import pandas as pd

from datetime import datetime, timedelta, timezone

"""
    Temporary informal unit test for ccxt exchange
    Note: 
    Exchange time is 13 digit unix time based on milliseconds for timestamp. 
    Divide by 1000 to convert to timestamp in python
"""

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# update this to reflect your config file
config_file = "../safe/secrets_test.ini"

def get_exchange_config():
    try:
        config_dir = os.path.dirname(__file__)
        parser = configparser.ConfigParser()
        parser.read(os.path.join(config_dir, config_file))
        exch_ids = parser.sections()
        sec = {section_name: dict(parser.items(section_name)) for section_name in exch_ids}
        return sec
    except Exception as e:
        log.error(e)
        pass


def get_exchange(config_sections):
    # need to fix below in order to check for for acceptable exchanges and parameters
    # for now, get 0th exchange
    exch_name = list(config_sections)[0]
    apikey = config_sections[exch_name]['api_key']
    secret = config_sections[exch_name]['secret']
    log.info(f"API Key:  {apikey}")

    # coin tiger requires an API key, even if only for ticker data
    ccxt_ex = getattr(ccxt, exch_name)({
        "apiKey": apikey,
        "secret": secret,
        'timeout': 30000,
        'enableRateLimit': True,
        'verbose': False,
        'precision': {'price':8,
                      'amount':8,}
    })
    return ccxt_ex


def get_ccxt_module():
    config_sections = get_exchange_config()
    ccxt_ex = get_exchange(config_sections)
    return ccxt_ex


def write_dict(l2_ob, file_name):
    with open(file_name, 'w') as f:
        s = f.write(json.dumps(l2_ob))


def read_dict(file_name):
    with open(file_name, 'r') as f:
        static_ob = json.loads(f.read())
    return static_ob


def test_rw_ob(l2_ob, file_name):
    """
    Test Reading and writing orderbook to file
    :param l2_ob:
    :return:
    """
    # write order book to file.
    # read order book from file
    if file_name is None:
        file_name = 'cex_ob.txt'
    write_dict(l2_ob, file_name)
    static_ob = read_dict(file_name)
    log.info(static_ob)


def test_print_orderbooks(symbol, cx):
    log.info(f"Fetch Ticker for {symbol} : {ccxt_ex.fetch_ticker(symbol)}\n")
    log.info(f"Fetching L2 Order Book: {cx.fetch_l2_order_book(symbol)}\n")
    log.info(f"Fetching Order Book: {cx.fetch_order_book(symbol)}\n")


def get_cex_data(l2, depth: int):
    # let ob stand for orderbook, ob_depth is the order book depth we want to map out

    bids = l2['bids']
    bid_df = pd.DataFrame(bids)
    bid_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    bid_df['timestamp'] = int(l2['timestamp']/1000)
    bid_df['type'] = 'bids'

    ask = l2['asks']
    ask_df = pd.DataFrame(ask)
    ask_df.columns = ['price', 'vol']
    # bring down to second level precision not millisecond
    ask_df['timestamp'] = int(l2['timestamp']/1000)
    ask_df['type'] = 'asks'

    return ask_df.head(depth), bid_df.head(depth)



if __name__ == '__main__':

    #symbol = 'BTC/USDT'
    #symbol = 'BTS/BTC'
    symbol = 'BTS/ETH'
    bitshares_symbol = 'BTS/OPEN.ETH'

    bid_symbol = symbol.split('/')[0]
    ask_symbol = symbol.split('/')[1]
    print(f'bid_symbol: {bid_symbol}, ask_symbol: {ask_symbol}')

    config_sections = get_exchange_config()
    log.info(config_sections)
    ccxt_ex = get_exchange(config_sections)
    cx = CcxtExchange(exchange=ccxt_ex)

    log.info(f'symbol: {symbol}')
#   test_print_orderbooks(symbol, cx)

    l2_ob = ccxt_ex.fetch_l2_order_book(symbol)
    asks, bids = get_cex_data(l2_ob, depth=2)
    log.info(f'Asks:\n {asks}')
    log.info(f'Bids:\n {bids}')

    bid_free = 0
    ask_free = 0

    log.info(f"All Available Free Balance: {cx.free_balance}")
    free_bal = cx.free_balance

    try:
        if bid_symbol in free_bal:
            bid_free = free_bal[bid_symbol]
            log.info(f"{bid_symbol} : {bid_free}")
        if ask_symbol in free_bal:
            ask_free = free_bal[ask_symbol]
            log.info(f"{ask_symbol} : {ask_free}")
    except exception as e:
        log.error(f"error on bid or ask asset balance: {e}")


    log.info(f'Price({ask_symbol}), Vol is Amount ({bid_symbol})  on cointiger exchange')

    """
    test buy and sell on cex exchanges
    """
    # test buy 5% of free balance
    if bid_free > 0:
        buy_amt = bid_free * 0.05
        buy_price = asks['price'][0]  # take the lowest asking price for market buy
        log.info(f"Buy Amount: {buy_amt}, Buy Price: {buy_price}")

    # calculate Fees (Todo incomplete)
    # may not exist for some exchanges, check method_list
    method_list = list(cx.method_list)
    # log.info(f"Available Methods from ccxt for this exchange: {list(method_list)}")

    fees = None
    if 'fetchTradingFees' in method_list:
        fees = cx.fetch_trading_fees()
        log.info(f'Fetch Trading Fees: {fees}')
    if fees is None:
        log.info(f'Fees from exchange API is none, switching to manual fee')

    log.info(f"Creating Market Buy Order: {symbol}, Amt: {buy_amt}, Price:{buy_price}")
    # uncomment to execute test buy order
#    order_id = cx.create_buy_order(symbol, buy_amt, buy_price)
#    fetched_order = cx.fetch_order(order_id)
#    log.info(f'fetched order: {fetched_order}')

    my_trades = cx.fetch_my_trades(symbol)
    log.info(f"Fetch my trades {symbol}: Trades:\n{my_trades}")

    open_orders = cx.fetch_open_orders(symbol=symbol)
    log.info(f"Fetch Open Orders: {symbol}:\n{open_orders}")

    # Time management
    orderbook_ts = asks['timestamp'][0]
    log.info(f'Order book Timestamp {orderbook_ts}')
    time_frame = 5  # how far back should we look in time.
    now_ts = datetime.now(timezone.utc)
    dt = now_ts - timedelta(minutes=time_frame)
    since_ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
    log.info(f'Now Timestamp {now_ts.replace(tzinfo=timezone.utc).timestamp()},'
             f'Time 15 minutes ago: {since_ts}')


    # keep checking status of order
    while True:
        if 'fetchMyTrades' in method_list:
            log.info(f'fetch my trades: {cx.fetch_my_trades(symbol)}')
        if 'fetchOpenOrders' in method_list:
            log.info(f'fetch open orders: {cx.fetch_open_orders(symbol)}')
        if 'fetchClosedOrders' in method_list:
            log.info(f'fetch closed orders: {cx.fetch_closed_orders(symbol, since_ts)}')


    # todo:
    #    def get_all_closed_orders_since_to(self, symbol, since, to):
    #    cx.create_sell_order(symbol, sell_amt, sell_price)
    #    cx.cancel_order(order_id)

"""
        all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
        log.info(f"Fetching All closed Orders for {symbol} since {since} to {to} \n")
        log.info(all_orders)
"""
