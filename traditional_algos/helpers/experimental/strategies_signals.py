from logging import warn
import numpy as np
import pandas as pd
from ..intraday import In
from ..FnO import analyse_option_chain


warn('''WARNING: These strategies ONLY generate SIGNALS as a SCREENER so that you can you can do some other work work until the alert goes off. It does not mean that you have to Buy or Sell or execute order. 
It only means that you should start watching your stock from now on and in coming candles, you might or might not get a trade.
Before placing any order, don't forget to apply your knowledge of Price Action, market behaviour and Risk management skills.''')


def n_candles_range_breakout(data, previous_n:int = 10, use_closing_value:bool = True,names:tuple = ('OPEN','CLOSE','LOW','HIGH'), num_of_std:float = 1):
    '''
    If the current candle's reference {HIGH / LOW / CLOSE} is greater or less than previous N candles
    args:
        df: DataFrame for the stock
        previous_n: No of previous candles to consider
        use_closing_value: IF true, "CLOSE" will be used insted of "HIGH" / "LOW"
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        no_of_std: Number of Standard Deviations to count as Range breakout to be significant
    '''
    _, Close, Low, High = names
    high_reference = Close if use_closing_value else High
    low_reference = Close if use_closing_value else Low

    df = data.copy()
    
    high_mean, high_std = df.loc[1:previous_n+1,High].mean(), df.loc[1:previous_n+1,High].std()
    low_mean, low_std = df.loc[1:previous_n+1,Low].mean(), df.loc[1:previous_n+1,Low].std()

    if df.loc[0,high_reference] > high_mean + (num_of_std * high_std):
        return "Buy"
    
    if df.loc[0,low_reference] < low_mean - (num_of_std * low_std):
        return "Sell"

    return None


def MA_crossover(data, fast_ma:int = 50, slow_ma:int = 200, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True,):
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


def MA_support_resistance(data, ma:int = 50, gap:float = 0.005, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True):
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

            if df.loc[0,Close] > df.loc[0, _ma]:
                if (df.loc[0,Low] < df.loc[0,_ma]) or (df.loc[0,Low] - df.loc[0,_ma] < df.loc[0,_ma] * gap):
                    return "Buy"

    elif df.loc[0,ma_200] >= df.loc[0,_ma]:
        if df.loc[0,Low] <= df.loc[0,Close] < df.loc[0,Open]:

            if df.loc[0,Close] < df.loc[0, _ma]:
                if (df.loc[0,High] > df.loc[0,_ma]) or (df.loc[0,_ma] - df.loc[0,High] < df.loc[0,_ma] * gap):
                    return "Sell"

    return None


def rsi_overbought_oversold(data, overbought_thresh:float = 70, oversold_thresh:float = 30, periods:int = 14, Close:str = 'CLOSE', ema:bool = True, include_200_ma:bool = False):
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


def bollinger_bands(data, moving_average:int = 20, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), include_rsi_divergence:bool = False, include_200_ma: bool = False):
    '''
    Create an alert when Prices closes above the upper band or below the lower band. Aftert the alert, watch the Price Action for around 8-10 candles. 
    args:
        data: DataFrame of the stock
        moving_average: Length / Period of Middle Band Line or Moving Average Line to consider as base line
        include_rsi_divergence: Whether to compute the RSI Divergence along with the BollingerBands Strategy
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        include_200_ma: Whether to consider the 200 Moving Average as the reference line. Look for Buy signals above it and Sell signals below it
    '''
    Open, Close, Low, High = names
    df = data.copy()

    if include_rsi_divergence and "RSI" not in df.columns:
        warn("No RSI column found. RSI will be calculated based on default settings")
        df = In.get_RSI(df, Close = Close, return_df = True)

    df = In.get_BollingerBands(df, mv = moving_average, Close = Close)
    df = In.get_MA(df, 200, names, return_df = True)

    if df.loc[0,Close] > df.loc[0, "Upper Band"]:
        if include_200_ma:
                if df.loc[0,Close] < df.loc[0,'200-MA']:
                    return "Sell"
        return "Sell"

    elif df.loc[0,Close] < df.loc[0, "Lower Band"]:
        if include_200_ma:
                if df.loc[0,Close] > df.loc[0,'200-MA']:
                    return "Buy"
        return "Buy"
    
    return None


def rsi_divergence(data, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), upper_threshold:float = 70, lower_threshold: float = 30, lookback_period:int  = 10, include_200_ma: bool = False):
    '''
    Calculate RSI divergence. Sell signal is when the RSI has already crossed Upper threshold and Closing Price is increasing but RSI is decreasing. 
    Opposite is true for buying. Apply it with Price Action such as Candle Patterns or Support - Resistance Zones
    args:
        data: DataFrame of the stock
        names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        upper_threshold: Consider the stock as Overbought only when the RSI crosses above this threshold
        upper_threshold: Consider the stock as Oversold only when the RSI crosses below this threshold
        lookback_period: No of candles to look back fro mthe current candle to calculate divergence
        include_200_ma: Whether to consider the 200 Moving Average as the reference line. Look for Buy signals above it and Sell signals below it
    '''
    Open, Close, Low, High = names

    df = data.copy()
    if df.iloc[0,0] > df.iloc[1,0]:
        df.sort_index(ascending=False, inplace = True)

    if "RSI" not in df.columns:
        warn("Data found without prior calculated 'RSI'. Getting RSI using defaults")
        df = In.get_RSI(df, Close = Close, return_df = True)
    
    max_rsi = df.loc[:lookback_period,'RSI'].max()
    min_rsi = df.loc[:lookback_period,'RSI'].min()

    if max_rsi > upper_threshold:
        id_ = df.loc[:lookback_period,'RSI'].idxmax()
        max_rsi_close = df.loc[id_, Close]

        if (df.loc[0,"RSI"] < max_rsi) and (df.loc[0,Close] > max_rsi_close):
            if include_200_ma:
                if df.loc[0,Close] < df.loc[0,'200-MA']:
                    return "Sell"
            return "Sell"

    elif min_rsi < lower_threshold:
        id_ = df.loc[:lookback_period,'RSI'].idxmin()
        min_rsi_close = df.loc[id_, Close]

        if (df.loc[0,"RSI"] > min_rsi) and (df.loc[0,Close] < min_rsi_close):
            if include_200_ma:
                if df.loc[0,Close] > df.loc[0,'200-MA']:
                    return "Buy"
            return "Buy"
    
    return None


def option_chain_SR(data, name, gap_reference:float = 0.0075, col_names:tuple = ('OPEN','CLOSE','LOW','HIGH')):
    '''
    Look if a stock's High / Low price has reached around the highest Calls or Puts Open Interest. Look at the Price Action to see if it reverses fro mthe position
    args:
        data: DataFrame of the stock
        name: Name of the scrip / stock / index
        col_names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
        gap_reference: 0.03 means that when the gap between S-R and High / Low is within the 0.03% of the recent Close, then only consider it
    '''
    assert name in In.data['f&o'], f"{name} not listed in Futures and Options"
    Open, Close, Low, High = col_names

    df = data.copy()

    df_option = analyse_option_chain(name, compare_with = 'openInterest', plot = False)
    resistance_index = df_option[df_option['contract_type'] == 'Calls_CE']["openInterest"].idxmax()
    support_index = df_option[df_option['contract_type'] == 'Puts_PE']["openInterest"].idxmax()
    support, resistance = df_option.loc[support_index, "strike_price"], df_option.loc[resistance_index, "strike_price"]
    support, resistance

    closing = df.loc[0,Close]
    if (0 <= resistance - df.loc[0,High] <= closing * gap_reference):
        return "Sell"

    elif (0 <= df.loc[0,Low] - support <= closing * gap_reference):
        return "Buy"

    return None



    




    
