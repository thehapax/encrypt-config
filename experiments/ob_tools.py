
def get_vwap(df, period):
    """
    @param df is the dataframe for an orderbook
    There are five steps in calculating VWAP:
    1. Calculate the Typical Price for the period. [(High + Low + Close)/3)]
    2. Multiply the Typical Price by the period Volume (Typical Price x Volume)
    3. Create a Cumulative Total of Typical Price. Cumulative(Typical Price x Volume)
    4. Create a Cumulative Total of Volume. Cumulative(Volume)
    5. Divide the Cumulative Totals.

    VWAP = Cumulative(Typical Price x Volume) / Cumulative(Volume)
    """
    log.info("Calculating VWAP for specific period")
    # calculate vwap? and/or MVWAP? (does this help anticipate enough?)

