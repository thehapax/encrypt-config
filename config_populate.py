import configparser

"""
an idea of future config file format
Simple Arb : A <-> B
Triangular arb : A -> B -> C
"""
simple_arb = ['strategy-type', 'exchange_name', 'api_key', 'secret']
triangular_arb = ['strategy-type', 'Exchange_Name_A', 'api_key_A', 'secret-A',
                  'Exchange_Name_C', 'api_key_C', 'secret-C']

def add_section(strategy_name, strategy, parser):
    parser.add_section(strategy_name)
    for label in strategy:
        value = input(label + ":")
        parser.set(strategy_name, label, value)
    return parser

# get data from user, write config to file
parser = configparser.ConfigParser()

my_strategy = input("Name of strategy:")
add_section(my_strategy, simple_arb, parser)

tristrategy = input("Name of strategy:")
add_section(tristrategy, triangular_arb, parser)

# write parser to file
with open('safe/secrets_test2.ini', 'w') as writer:
    parser.write(writer)
