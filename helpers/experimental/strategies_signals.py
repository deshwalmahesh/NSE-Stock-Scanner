'''
These strategies only generate signal as a SCREENER so that you can you can do your work and watch the stock only at a specific time when the alert goes off. Before placing any order, 
don't forget to apply your knowledge of Price Action, market behaviour and Risk management skills.
'''

import numpy as np
import pandas as pd
from ..intraday import In


def n_candles_range_breakout(data, previous_n:int = 10, use_closing_value:bool = True,names:tuple = ('OPEN','CLOSE','LOW','HIGH')):
    '''
    If the current candle's reference {HIGH / LOW / CLOSE} is greater or less than previous N candles
    args:
        df: DataFrame for the stock
        previous_n: No of previous candles to consider
        use_closing_value: IF true, "CLOSE" will be used insted of "HIGH" / "LOW"
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
    '''
    _, Close, Low, High = names
    high_reference = Close if use_closing_value else High
    low_reference = Close if use_closing_value else Low

    df = data.copy()
    if df.iloc[0,0] > df.iloc[1,0]: # newest date first
        df.sort_index(ascending=False, inplace = True)

    if df.loc[0,high_reference] > max(df.loc[1:previous_n+1,High]) + df.loc[0,Low]* 0.001:
        return "Buy"
    
    elif df.loc[0,low_reference] < min(df.loc[1:previous_n+1,Low]) - df.loc[0,Low]* 0.0001:
        return "Sell"

    return None


def MA_crossover(data, fast_ma:int, slow_ma:int, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True,):
    '''
    Generate signals when Fast Moving average crossed Slow MA. Could be (9,20), (20,50), (20,200), (50, 200) or nay of your choice
    args:
        data: DataFrame of the stock
        fast_ma: Fast moving average window
        slow_ma: Slow moving average window
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        simple: Whether to return Simple or Exponential Moving Average
    '''
    _, Close, Low, High = names

    fast = f'{str(fast_ma)}-MA'
    slow = f'{str(slow_ma)}-MA'

    df = data.copy()
    if df.iloc[0,0] > df.iloc[1,0]: 
        df.sort_index(ascending=False, inplace = True)


    df = In.get_MA(df, fast_ma, names, simple, return_df = True)
    df = In.get_MA(df, slow_ma, names, simple, return_df = True)

    if (df.loc[0,fast] > df.loc[0,slow]) and (df.loc[1,fast] < df.loc[1,slow]):
        return "Buy"

    elif (df.loc[0,fast] < df.loc[0,slow]) and (df.loc[1,fast] > df.loc[1,slow]):
        return "Sell"
    
    return None


def MA_support_resistance(data, ma:int, gap:float, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True):
    '''
    Generate signals stock has support / resistance on the MA line. After generating Buy signal, buy once price crosses last candle's high. Reverse applies for Sell Signal
    args:
        data: DataFrame of the stock
        ma: Moving Average which will act as support / resistance
        gap: Distance allowed between MA and recent candle Low / High. It is fraction of the MA. 0.01 means that Maximum distance allowed between MA and Cande Low/High is 1% of MA
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        simple: Whether to return Simple or Exponential Moving Average
    '''
    _ma = f'{str(ma)}-MA'
    ma_200 = '200-MA'
    Open, Close, Low, High = names

    df = data.copy()
    if df.iloc[0,0] > df.iloc[1,0]:
        df.sort_index(ascending=False, inplace = True)

    df = In.get_MA(df, ma, names, simple, return_df = True)
    df = In.get_MA(df, 200, names, simple, return_df = True)

    if df.loc[0,ma_200] <= df.loc[0,_ma]:
        if df.loc[0,High] >= df.loc[0,Close] > df.loc[0,Open]:
            if (df.loc[0,Low] < df.loc[0,_ma]) or (df.loc[0,Low] - df.loc[0,_ma] < df.loc[0,_ma] * gap):
                return "Buy"

    elif df.loc[0,ma_200] >= df.loc[0,_ma]:
        if df.loc[0,High] <= df.loc[0,Close] < df.loc[0,Open]:
            if (df.loc[0,High] > df.loc[0,_ma]) or (df.loc[0,_ma] - df.loc[0,High] < df.loc[0,_ma] * gap):
                return "Sell"

    return None


def rsi_overbought_oversold(data, overbought_thresh:float, oversold_thresh:float, periods:int = 14, Close:str = 'CLOSE', ema:bool = True, include_200_ma:bool = True):
    '''
    Signal generated on RSI given once it reaches Overbought - Oversold Areas. After generating signal, Wait for PRICE - ACTION before taking any decisions. 
    So a signal generated NOW might generate Buy / Sell opportunity after some candles pass. Once a signal has been generated, just start tracking the stock
    args:
        overbought_thresh: Threshold which defines the Overbought level
        Oversold_thresh: Value which defines Oversold Level
        periods: Moving Average period to calculate the RSI
        Close: Name of the Close Column
        ema: Whether to use the Exponential Moving Average instead os Simple
        include_200_ma: Whether to use 200 MA as a reference point to be include in generating signal. Act on Buy signal only if it is above 200 MA and viceversa
    '''
    df = data.copy()
    if df.iloc[0,0] > df.iloc[1,0]:
        df.sort_index(ascending=False, inplace = True)

    df = In.get_RSI(df, periods = periods, Close = Close, ema = ema, return_df = True, signal_only = False)

    if (df.iloc[0,-1] > overbought_thresh):
        if include_200_ma:
            if df.loc[0,Close] < df.loc[0,'200-MA']:
                return "Sell"
        else: return "Sell"
            
    elif (df.iloc[0,-1] < oversold_thresh):
        if include_200_ma:
            if df.loc[0,Close] > df.loc[0,'200-MA']:
                return "Buy"
        else: return "Buy"

    return None
