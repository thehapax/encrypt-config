import logging
import os
import configparser
import ccxt
import json
from ccxt_exchange import CcxtExchange
import pandas as pd

from datetime import datetime, timedelta, timezone

"""
    Temporary informal unit test for ccxt exchange
    
    Note: 
    Ccxt Exchange time is 13 digit unix time based on milliseconds for timestamp. 
    Divide by 1000 to convert to 10 digit timestamp in python

    Need to Hard code fees fro Cointiger, not avail through API call. 
    Cointiger is 0.15% for taker and 0.08% for maker
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

def get_fees(cx):
    # may not exist for some exchanges, check method_list
    method_list = list(cx.method_list)
    # log.info(f"Available Methods from ccxt for this exchange: {list(method_list)}")

    # calculate Fees (Todo incomplete)
    fees = None
    if 'fetchTradingFees' in method_list:
        fees = cx.fetch_trading_fees()
        log.info(f'Fetch Trading Fees: {fees}')
    if fees is None:
        log.info(f'Fees from exchange API is none, switching to manual fee')
    return fees


def calc_trade_amt(percent, price_df, asset, free_bal, min_bal):
    if asset in free_bal:
        amt_free = free_bal[asset]
        log.info(f"{bid_symbol} : {amt_free}")
        if amt_free > 0:
            amt_avail = amt_free - (amt_free * min_bal)
            buy_amt = amt_avail * percent
            buy_price = price_df['price'][0]  # take the lowest asking price for market buy
            return buy_amt, buy_price
        else:
            return 0,0
    else:
        return 0,0


if __name__ == '__main__':

    #symbol = 'BTC/USDT'
    #symbol = 'BTS/BTC'
    symbol = 'BTS/ETH'
    bitshares_symbol = 'BTS/OPEN.ETH'

    bid_symbol = symbol.split('/')[0]
    ask_symbol = symbol.split('/')[1]
    log.info(f'Price({ask_symbol}), Vol is Amount ({bid_symbol})  on cointiger exchange')

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

    """
    test buy and sell on cex exchanges
    """
    free_bal = cx.free_balance
    log.info(f"All Available Free Balance: {free_bal}")

    min_bal_percentage = 0.10  # do not use 10% of free balance, keep at least 10% around.

    # test buy 5% of free balance
    buy_amt, buy_price = calc_trade_amt(0.05, asks, bid_symbol, free_bal, min_bal_percentage)
    log.info(f"Buy Amount: {buy_amt}, Buy Price: {buy_price}")

    log.info(f"Creating Market Buy Order: {bid_symbol}, Amt: {buy_amt}, Price:{buy_price}")
    # uncomment to execute test buy order
    # if buy_amt > 0:
    #    buy_id = cx.create_buy_order(symbol, buy_amt, buy_price)
    #    fetched_order = cx.fetch_order(buy_id)
    #    log.info(f'fetched buy order: {fetched_order}')

    # test sell 5% of free balance
    sell_amt, sell_price = calc_trade_amt(0.05, bids, ask_symbol, free_bal, min_bal_percentage)
    log.info(f"Creating Market Sell Order: {ask_symbol}, Amt: {sell_amt}, Price:{sell_price}")
    # if sell_amt > 0:
    #    sell_id = cx.create_sell_order(symbol, sell_amt, sell_price)
    #    forder = cx.fetch_order(buy_id)
    #    log.info(f'fetched sell order: {forder}')

    # synthetic test for 'ETH' asset, amt = 0.1, percent = 0.05
    sell_amt = 0.1* 0.05
    sell_price = bids['price'][0]
    log.info(f'sythetic: {ask_symbol}, sell amt {sell_amt}, sell_price {sell_price}')
    # end synthetic

    my_trades = cx.fetch_my_trades(symbol)
    log.info(f"Fetch my trades {symbol}: Trades:\n{my_trades}")

    open_orders = cx.fetch_open_orders(symbol=symbol)
    log.info(f"Fetch Open Orders: {symbol}:\n{open_orders}")

    # Time management
    orderbook_ts = asks['timestamp'][0]
    log.info(f'Order book Timestamp {orderbook_ts}')
    time_frame = 10  # how far back should we look in time. 10 minutes
    now_ts = datetime.now(timezone.utc)
    dt = now_ts - timedelta(minutes=time_frame)
    since_ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
    log.info(f'Now Timestamp {int(now_ts.replace(tzinfo=timezone.utc).timestamp())},'
             f'Time 10 minutes ago: {since_ts}')

    # keep checking status of order
    while True:
        if 'fetchMyTrades' in cx.method_list:
            log.info(f'fetch my trades: {cx.fetch_my_trades(symbol)}')
        if 'fetchOpenOrders' in cx.method_list:
            log.info(f'fetch open orders: {cx.fetch_open_orders(symbol)}')
        if 'fetchClosedOrders' in cx.method_list:
            log.info(f'fetch closed orders: {cx.fetch_closed_orders(symbol, since_ts)}')

    # todo:
    #   cx.cancel_order(order_id)
    #   all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
    #   log.info(f"Fetching All closed Orders for {symbol} since {since} to {to} : {all_orders}")
