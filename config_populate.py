import configparser

# idea of future format?
simple_arb = ['strategy-name', 'exchange-name', 'api-key', 'secret']
triangular_arb = ['strategy-name', 'A-exchange-name', 'A-api-key', 'A-secret',
                  'B-exchange-name', 'B-api-key', 'B-secret']

####################################

# get data from user, write config to file

strategy = 'simple-arb-strategy'
exchange_label = 'exchange_name'
api_key_label = 'api_key'
secret_label = 'secret'

parser = configparser.ConfigParser()

# default
exchange = 'cointiger'
api_key = 'testf136123409824037840f0c160'
secret = 'secret_here'

strategy = input("Name of Strategy:")
exchange = input("exchange: ")
api_key = input("api key:")
secret = input("secret:")

parser.add_section(strategy)
parser.set(strategy, exchange_label, exchange)
parser.set(strategy, api_key_label, api_key)
parser.set(strategy, secret_label, secret)

# write parser to file
with open('test.ini', 'w') as writer:
    parser.write(writer)
