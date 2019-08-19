from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import logging, os
import binascii
import base64

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
    # temporary, need to fix above, just for testing.
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
