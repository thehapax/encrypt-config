import logging
from getpass import getpass
from configparser import ConfigParser, NoOptionError

from simple_encrypt import test_encrypt, test_decrypt
import ccxt


log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def get_exchange_config(content):
    try:
        parser = ConfigParser()
        parser.read_string(content)
        return parser
    except Exception as e:
        log.error(e)
        pass

def get_exchange(parser):
    # only accept API keys for these ccxt exchanges, cross check here.
    EXCHANGES = ['cointiger', 'binance', 'bitfinex']

    exch_name = None
    for section in EXCHANGES:
            has_section = parser.has_section(section)
            log.info('{} section exists: {}'.format(section, has_section))
            if has_section:
                exch_name = section

    try:
        api_key = parser.get(exch_name, 'api_key')
        secret = parser.get(exch_name, 'secret')
        strategy = parser.get(exch_name, 'strategy')
        log.info(f"api_key: {api_key}, secret: {secret}, strategy: {strategy}")

        # coin tiger requires an API key, even if only for ticker data
        ccxt_ex = getattr(ccxt, exch_name)({
            "apiKey": api_key,
            "secret": secret,
            'timeout': 30000,
            'enableRateLimit': True,
            'verbose': False,
        })
        return ccxt_ex

    except NoOptionError as e:
        log.error(e)


if __name__ == "__main__":

    config_file = "secrets_test.ini"
    input_passwd = getpass("password: ")     # read the password from the user (without displaying it)

    test_encrypt(input_passwd, config_file) # test encrypt to file
    plain_text = test_decrypt(input_passwd, "enc_"+config_file) # test decrypt to file

    if plain_text is not None:
        parser = get_exchange_config(plain_text)
        ccxt_ex = get_exchange(parser)

#    log.info(ccxt_ex.fetch_free_balance())  # test activity of ccxt exchange

