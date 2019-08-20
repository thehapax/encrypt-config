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

# only accept API keys for these ccxt exchanges, cross check here.
EXCHANGES = ['cointiger', 'binance', 'bitfinex']

def get_exchange_config(content):
    try:
        parser = ConfigParser()
        parser.read_string(content)
        return parser
    except Exception as e:
        log.error(e)
        pass

def get_by_exchange(parser):

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


def get_by_strategy_name(section_name, parser):

    try:
        api_key = parser.get(section_name, 'api_key')
        secret = parser.get(section_name, 'secret')
        exchange_name = parser.get(section_name, 'exchange_name')

        log.info(f"exchange: {exchange_name}, api_key: {api_key}, "
                 f"secret: {secret}, strategy-name: {section_name}")

        # coin tiger requires an API key, even if only for ticker data
        ccxt_ex = getattr(ccxt, exchange_name)({
            "apiKey": api_key,
            "secret": secret,
            'timeout': 30000,
            'enableRateLimit': True,
            'verbose': False,
        })
        return ccxt_ex

    except NoOptionError as e:
        log.error(e)


def test_exchange_config_one():
    config_file = "secrets_test.ini"
    input_passwd = getpass("password: ")     # read the password from the user (without displaying it)

    test_encrypt(input_passwd, config_file) # test encrypt to file
    plain_text = test_decrypt(input_passwd, "enc_"+config_file) # test decrypt to file

    if plain_text is not None:
        parser = get_exchange_config(plain_text)
        ccxt_ex = get_by_exchange(parser)
        return ccxt_ex
    else:
        return None


def test_exchange_config_two():
    config_file = "secrets_test2.ini"
    input_passwd = getpass("password: ")

    test_encrypt(input_passwd, config_file)
    plain_text = test_decrypt(input_passwd, "enc_"+config_file)

    if plain_text is not None:
        parser = get_exchange_config(plain_text)
        for section_name in parser.sections():

            if parser.get(section_name, 'strategy-type')  == 'simple':
                ccxt_ex = get_by_strategy_name(section_name, parser)
                return ccxt_ex
            elif parser.has_option(section_name, 'strategy-type') ==  'triangular':
                return None
    else:
        return None


if __name__ == "__main__":

    ccxt_ex = test_exchange_config_one()
    ccxt_ex2 = test_exchange_config_two()

#    log.info(ccxt_ex.fetch_free_balance())  # test activity of ccxt exchange

