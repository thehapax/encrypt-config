from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import sys
import binascii
import base64
from getpass import getpass
from configparser import ConfigParser


def gen_key(passwd):
    try:
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(passwd)
        return base64.urlsafe_b64encode(digest.finalize())
    except Exception as e:
        print("Gen_key Exception: ", e)


def encrypt_file(input_passwd, my_config):
    try:
        my_password = bytes(input_passwd, encoding='utf-8')
        print(my_password)

        if (len(my_password)>1):
            key = gen_key(my_password)
            print("Key: ", binascii.hexlify(bytearray(key)), sep=" ")

            cipher_suite = Fernet(key)
            cipher_text = cipher_suite.encrypt(my_config)
            return cipher_text
    except Exception as e:
        print("Encrypt_file Exception:", e)


def decrypt_file(input_passwd, cipher_text):
    try:
        my_password = bytes(input_passwd, encoding='utf-8')
        key = gen_key(my_password)
        cipher_suite = Fernet(key)
        plain_text = cipher_suite.decrypt(cipher_text).decode('utf-8')
        return plain_text
    except Exception as e:
        print("Decrypt_file Exception:", e)


def test_encrypt(input_passwd, config_filename):
    with open(config_filename, 'rb') as config_file:
        file_content = config_file.read()
        cipher_text = encrypt_file(input_passwd, file_content)
        print("Cipher: ", binascii.hexlify(bytearray(cipher_text)), sep=" ")

    enc_filename = "enc_"+config_filename
    with open(enc_filename, 'wb') as enc_file:
        enc_file.write(cipher_text)


def test_decrypt(input_passwd, config_filename):
    with open(config_filename, 'rb') as enc_file:
        content = enc_file.read()
        plain_text = decrypt_file(input_passwd, content)
        if plain_text is None:
            print("Plain text unable to decrypt, error")
        elif len(plain_text) > 0:
            print("Plain text ", plain_text, sep=':')


if __name__ == "__main__":
    config_filename = "secrets_orig.ini"
    input_passwd = getpass("password: ")     # read the password from the user (without displaying it)

    test_encrypt(input_passwd, config_filename)
    test_decrypt(input_passwd, "enc_"+config_filename)

