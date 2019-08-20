import configparser

def add_section(strategy_name, strategy, parser):
    parser.add_section(strategy_name)
    for label in strategy:
        value = input(label + ":")
        parser.set(strategy_name, label, value)
    return parser


# an idea of future format?
simple_arb = ['exchange-name', 'api-key', 'secret']
triangular_arb = ['Exchange_Name_A', 'api_key_A', 'secret-A',
                  'Exchange_Name_C', 'api_key_C', 'secret-C']

# Triangular arb : A -> B -> C

# get data from user, write config to file
parser = configparser.ConfigParser()

my_strategy = input("Name of simple-arb strategy:")
add_section(my_strategy, simple_arb, parser)

tristrategy = input("Name of Triangular Strategy:")
add_section(tristrategy, triangular_arb, parser)


# write parser to file
with open('test.ini', 'w') as writer:
    parser.write(writer)
