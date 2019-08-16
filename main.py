from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import logging, os
import binascii
import base64

from getpass import getpass
from configparser import ConfigParser, NoOptionError
import ccxt

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def gen_key(passwd):
    try:
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(passwd)
        return base64.urlsafe_b64encode(digest.finalize())
    except Exception as e:
        log.info("Gen_key Exception: %s ", e)


def encrypt_file(input_passwd, my_config):
    try:
        my_password = bytes(input_passwd, encoding='utf-8')
        log.info(my_password)

        if (len(my_password)>1):
            key = gen_key(my_password)
            log.info("Key: %s ", binascii.hexlify(bytearray(key)))

            cipher_suite = Fernet(key)
            cipher_text = cipher_suite.encrypt(my_config)
            return cipher_text
    except Exception as e:
        log.info("Encrypt_file Exception: %s",  e)


def decrypt_file(input_passwd, cipher_text):
    try:
        my_password = bytes(input_passwd, encoding='utf-8')
        key = gen_key(my_password)
        cipher_suite = Fernet(key)
        plain_text = cipher_suite.decrypt(cipher_text).decode('utf-8')
        return plain_text
    except Exception as e:
        log.info("Decrypt_file Exception: %s", e)


def test_encrypt(input_passwd, config_filename):
    # get real api keys from subdir for testing
    config_dir = os.path.join(os.getcwd(), 'safe')
    # temporary, need to fix
    filepath = os.path.join(config_dir, config_filename)

    with open(filepath, 'rb') as config_file:
        file_content = config_file.read()
        cipher_text = encrypt_file(input_passwd, file_content)
        log.info("Cipher: %s", binascii.hexlify(bytearray(cipher_text)))

    enc_filename = "enc_"+config_filename
    with open(enc_filename, 'wb') as enc_file:
        enc_file.write(cipher_text)

    return cipher_text


def test_decrypt(input_passwd, config_filename):
    with open(config_filename, 'rb') as enc_file:
        content = enc_file.read()
        plain_text = decrypt_file(input_passwd, content)
        if plain_text is None:
            log.info("Plain text unable to decrypt, error")
    return plain_text


def get_exchange_config(content):
    try:
        parser = ConfigParser()
        parser.read_string(content)
        return parser
    except Exception as e:
        log.error(e)
        pass


def get_exchange(parser):
    # only accept API keys for these ccxt exchanges
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

    parser = get_exchange_config(plain_text)
    ccxt_ex = get_exchange(parser)

#    log.info(ccxt_ex.fetch_free_balance())  # test activity of ccxt exchange

