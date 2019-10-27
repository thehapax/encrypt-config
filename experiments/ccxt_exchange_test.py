import logging
import os
import configparser
import ccxt
import json
from ccxt_exchange import CcxtExchange
import time

#from ccxt_engine import CcxtOrderEngine
"""
    Temporary informal unit test for ccxt exchange
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
        log.info(exch_ids)
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
    log.info(f"SECRET: {secret})")

    # coin tiger requires an API key, even if only for ticker data
    ccxt_ex = getattr(ccxt, exch_name)({
        "apiKey": apikey,
        "secret": secret,
        'timeout': 30000,
        'enableRateLimit': True,
        'verbose': False,
    })
    return ccxt_ex


def get_ccxt_module():
    config_sections = get_exchange_config()
    log.info(config_sections)
    ccxt_ex = get_exchange(config_sections)
    return ccxt_ex


def get_test_l2ob(symbol, ccxt_ex):
    l2_ob = cx.fetch_l2_order_book(symbol)
    return l2_ob


def write_dict(l2_ob, file_name):
    with open(file_name, 'w') as f:
        s = f.write(json.dumps(l2_ob))


def read_dict(file_name):
    with open(file_name, 'r') as f:
        static_ob = json.loads(f.read())
    return static_ob


def test_rw_ob(l2_ob):
    # write order book to file.
    # read order book from file
    file_name = 'cex_ob.txt'
    write_dict(l2_ob, file_name)
    static_ob = read_dict(file_name)
    print(static_ob)



if __name__ == '__main__':

    symbol = 'BTC/USDT'
    #    symbol = 'BTS/BTC'

    config_sections = get_exchange_config()
    log.info(config_sections)
    ccxt_ex = get_exchange(config_sections)
    cx = CcxtExchange(exchange=ccxt_ex)
    
    log.info(f"Available Free Balance: {cx.free_balance}\n")
    
    log.info(f"Fetch Ticker for {symbol} : {ccxt_ex.fetch_ticker(symbol)}\n")
    l2_ob = get_test_l2ob(symbol, ccxt_ex)
    l2_ob = cx.fetch_order_book(symbol)

    print("Free Balance:")
    free_bal = cx.free_balance
    bts_free = free_bal['BTS']
    print(f"BTS : {bts_free}")

    log.info(f"Fetch my trades {symbol}: Trades: {ccxt_ex.fetch_my_trades(symbol)}\n")

    print("Fetch Open Orders")
    open_orders = ccxt_ex.fetch_open_orders(symbol=symbol)

    print("ccxt method list ")
    method_list = cx.method_list
    log.info(f"Available Methods from ccxt for this exchange {method_list}")
    
    """
    test buy and sell on cex exchanges
    """

#   symbol = 'BTS'
    buy_amt = 0.0001
    buy_price = 1000000
    since = time.time()-10000
    
    #   print("Fetch trading fees") # may not exist for some exchanges, check method_list
    #   print(cx.fetch_trading_fees())

    
    # ccxt_ex.create_buy_order(symbol, buy_amt, buy_price)
    print("fetch my trades:")
    print(cx.fetch_my_trades(symbol))

    print("fetch open orders:")
    print(cx.fetch_open_orders(symbol))

    print("fetch closed orders:")
    print(cx.fetch_closed_orders(symbol, since))

    # cx.fetch_order(order_id)
    # cx.cancel_order(order_id)
    # cx.create_sell_order(symbol, sell_amt, sell_price)

    # todo:
    #    def get_all_closed_orders_since_to(self, symbol, since, to):


    
"""
    cx = CcxtExchange(exchange=ccxt_ex)
    trade_executor = CcxtOrderEngine(cx)

    log.info(f"Available Methods from ccxt for this exchange {list(cx.method_list)}\n")
    log.info(f"Available Free Balance: {cx.free_balance}\n")
    log.info(f"Fetch my trades {symbol}: Trades: {cx.fetch_my_trades(symbol)}\n")

    one_day = 24 * 60 * 60 * 1000  # in milliseconds
    since = cx.exchange.milliseconds() - one_day  # last 24 hours in milliseconds
    to = since + one_day
    log.info(since)

    log.info(f"fetch closed orders for {symbol}: {cx.fetch_closed_orders(symbol, since)}\n")

    if cx.method_list['fetchClosedOrders']:
        all_orders = cx.get_all_closed_orders_since_to(symbol, since, to)
        log.info(f"Fetching All closed Orders for {symbol} since {since} to {to} \n")
        log.info(all_orders)

    l2 = cx.fetch_l2_order_book(symbol)
    log.info(f"Fetching L2 Order Book: {cx.fetch_l2_order_book(symbol)}\n")

    log.info(f"Fetching Order Book: {cx.fetch_order_book(symbol)}\n")

"""
