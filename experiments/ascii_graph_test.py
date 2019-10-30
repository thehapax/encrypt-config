from ascii_graph import Pyasciigraph
from ascii_graph.colors import *
from ascii_graph.colordata import vcolor
from ascii_graph.colordata import hcolor
import os
import time


def graph_oneperline(test_data):
    # V color test

    # One color per line
    print('Color example:')
    pattern = [Gre, Yel, Red]
    data = vcolor(test_data, pattern)

    graph = Pyasciigraph()

    for line in graph.graph('vcolor test', data):
        print(line)
    return graph, data


def graph_thresholds(test_data):
    # H color test
    # Multicolor on one line
    print('\nMultiColor example:')

    # Color lines according to Thresholds
    thresholds = {
        51:  Gre, 100: Blu, 350: Yel, 500: Red,
    }
    data = hcolor(test_data, thresholds)

    # graph with colors, power of 1000, different graph symbol,
    # float formatting and a few tweaks
    graph = Pyasciigraph(
        line_length=120,
        min_graph_length=50,
        separator_length=4,
        multivalue=True,
        human_readable='si',
        graphsymbol='*', # comment out if you want to use solid bars
        float_format='{0:,.2f}',
        force_max_value=2000,
        )

    for line in graph.graph(label='With Thresholds', data=data):
        print(line)

    return graph, data


def dynamic_graph(graph, data, label):
    # To allow for dynamic updates, redraw
    # the chart continously every 1 second.

    os.environ['TZ'] = 'UTC'
    time.tzset()

    while True:
        os.system("clear")
        print(time.ctime())
        for line in graph.graph(label=label, data=data):
            print(line)
        time.sleep(1)


def test_vh():
    # testing float values used instead of chars for labels
    test_data = [(0.000001543, 423), (0.0005, 1234), ('line3', 531),
        ('line4', 200), ('line5', 834)]

    graph, data = graph_thresholds(test_data)
    graph, data = graph_oneperline(test_data)
    time.sleep(2)



if __name__ == '__main__':

    ob_color = {'asks': Red, 'bids': Gre, 'mirror_asks': Yel, 'mirror_bids': Blu}

    # type of data set cannot be used with hcolor or vcolor
    test = [('testval0', 600.085, Yel),
               ('testval1', 400.24, Red),
               ('testval2', [(600.234987, Red), (500, Yel)]),
               ('testval3', [(200.342, Gre), (100.222, Blu)]),
               ('testval4', -170.3492, Cya),
               ('testval5', 50, Blu),
               ('testval6', [(-300, Gre), (-230, Cya)]),
            ]

    graph = Pyasciigraph(
        line_length=120,
        min_graph_length=50,
        separator_length=4,
        multivalue=True,
        human_readable='si',
        float_format='{0:,.6f}',
    )

    dynamic_graph(graph, test, 'Dynamic Graph')

