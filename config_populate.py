import configparser

# idea of future format?
simple_arb = ['strategy-name', 'exchange-name', 'api-key', 'secret']
triangular_arb = ['triangular-strategy', 'A-exchange-name', 'A-api-key', 'A-secret',
                  'C-exchange-name', 'C-api-key', 'C-secret']

# Triangular arb : A -> B -> C
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

parser.add_section(strategy)
parser.set(strategy, exchange_label, exchange)
parser.set(strategy, api_key_label, api_key)
parser.set(strategy, secret_label, secret)

tristrategy = input("Name of Strategy:")
exchangeA = input("exchange A: ")
api_keyA = input("api key A:")
secretA = input("secret A:")
exchangeC = input("exchange C: ")
api_keyC = input("api key C:")
secretC = input("secret C:")

parser.add_section(tristrategy)

parser.set(tristrategy, triangular_arb[1], exchangeA)
parser.set(tristrategy, triangular_arb[2], api_keyA)
parser.set(tristrategy, triangular_arb[3], secretA)

parser.set(tristrategy, triangular_arb[4], exchangeC)
parser.set(tristrategy, triangular_arb[5], api_keyC)
parser.set(tristrategy, triangular_arb[6], secretC)


# write parser to file
with open('test.ini', 'w') as writer:
    parser.write(writer)
