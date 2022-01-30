from .datahandler import *
import plotly.graph_objects as go
import plotly.io as pio
from .candlestick import *
from ta.trend import ADXIndicator, macd_diff, cci
from ta.volatility import average_true_range
from .nse_data import NSEData
from .plotting import Plots
import numpy as np

CP = CandlePattern()
NSE = NSEData()
PLT = Plots()

pio.renderers.default = 'colab' 


class AnalyseStocks(DataHandler):
    def __init__(self, check_fresh = True):
        '''
        args:
            path: Path where all the stock files are saved
        '''
        super().__init__(check_fresh = check_fresh)
        self.registered_stocks = self.read_data()['registered_stocks']
        self.colors = self.read_data()['colors']
        self.rising = {}
        self.recent_info = {}
        self.indices = {'nifty_50': 'Nifty 50','nifty_100':'Nifty 100','nifty_200':'Nifty 200','nifty_500':'Nifty 500'}

    
    def get_index(self,symbol:str, category:str='nifty'):
        '''
        Get the Index of the symbol from nifty 50,100,200,500
        args:
            symbol: Name /  ID od the company on NSE
            category: Which category to return. "nifty" returns the nifty index; "all" returns a dictonary in which the stock is mentioned nifty, sectoral and thematic
        '''
        if category == 'nifty':
            for index in self.indices.keys():
                if symbol in self.data[index]:
                    return self.indices[index]
            return 'Other'
        
        else:
            result = []
            for index in self.indices.keys():
                if symbol in self.data[index]:
                    result.append(self.indices[index])
                    break
            
            for group_name in ["sectoral_indices", "thematic_indices"]:
                for sector in self.data[group_name].keys():
                    if symbol in self.data[group_name][sector]:
                        result.append(sector)
            return result


    def is_ma_eligible(self, df, limit:float, mv = 44, names:tuple = ('DATE','OPEN','CLOSE','LOW','HIGH')):
        '''
        Find the Positive Stocks which are about to rise on the Moving average line
        args:
            df: DataFrame
            limit: Limit difference between average and low/high threshold for selecting stocks
            mv: Moving Average to Consider
            names: Tuple of column names showing ('DATE','OPEN','CLOSE','LOW','HIGH')
        '''
        Date, Open, Close, Low, High = names
        Average = f'{str(mv)}-SMA'
        
        stocks = df.sort_index(ascending=False,) # Sort the values else Moving average for new values will be empty
        stocks[Average] = stocks[Close].rolling(mv, min_periods = 1).mean()
        
        last_traded = stocks.iloc[-1,:]
        low, high, open_ , close, avg, symbol = last_traded[Low],last_traded[High],last_traded[Open],last_traded[Close], last_traded[Average], last_traded['SYMBOL']
        
        if (close < avg) or (close < open_) : # if red candle or below Average Line, Discard
            return False
        
        limit = low * 0.0015 if not limit else limit # assume limit to be 5% of low
        diff = min(abs(low - avg), (abs(high - avg)), abs(open_ - avg), abs(close - avg)) # min diff between any of the 4 values
        
        if diff <= limit:
            self.rising[symbol] = stocks.iloc[-mv//2:-1,-1].mean() < avg  # whether the moving average is Upward or Downward according to last 44 days moving averages
            return {symbol : round(diff,2)}

        return False
    
    
    def get_BollingerBands(self, df, mv:int = 20, Close:str = 'CLOSE', return_df:bool = True):
        '''
        Calculate the Upper and Lower Bollinger Bands Given on a Moving Average Line
        args:
            df: Stocks Data
            mv: Moving Average Line value
            Close: Names of column which holds Closing Info
            return_df = Whether to rturn the whole df or just recent values
        '''
        ticker = df.copy()

        if ticker.iloc[0,0] > ticker.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            ticker.sort_index(ascending=False, inplace = True)

        sma = ticker[Close].rolling(window = mv).mean()
        std = ticker[Close].rolling(window = mv).std(0)

        upper_bb = sma + std * 2
        lower_bb = sma - std * 2

        ticker['Upper Bollinger'] = upper_bb
        ticker['Lower Bollinger'] = lower_bb

        ticker.sort_index(ascending=True, inplace = True)

        if return_df:
            return ticker

        return ticker.iloc[0,-2:]
    
    
    def Ichimoku_Cloud(self,df, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), return_df:bool = True):
        '''
        Get the values of Lines for Ichimoku Cloud
        args:
            df: Dataframe
            nameS: Names of Columns containing these Attributes
            return_df = Whether to rturn the whole df or just recent values
        '''
        Open, Close, Low, High = names
        d = df.copy()
        if d.iloc[0,0] > d.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)


        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
        period9_high = d[High].rolling(window=9).max()
        period9_low = d[Low].rolling(window=9).min()
        tenkan_sen = (period9_high + period9_low) / 2


        # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
        period26_high = d[High].rolling(window=26).max()
        period26_low = d[Low].rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
        period52_high = d[High].rolling(window=52).max()
        period52_low = d[Low].rolling(window=52).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

        # The most current closing price plotted 22 time periods behind (optional)
        chikou_span = d[Close].shift(-26) # Given at Trading View.

        d['blue_line'] = tenkan_sen
        d['red_line'] = kijun_sen
        d['cloud_green_line_a'] = senkou_span_a
        d['cloud_red_line_b'] = senkou_span_b
        d['lagging_line'] = chikou_span

        d.sort_index(ascending=True, inplace = True)

        if return_df:
            return d

        return d.iloc[0,-1]
    
    
    def Ichi_count(self, data, names = ('LOW', 'HIGH', 'cloud_green_line_a','cloud_red_line_b','lagging_line','blue_line','red_line')):
        '''
        Get The Count of how many Ichimoku Conditions this certain Data Holds. Conditions being:
            1. If recentccandle is ABOVE Cloud, +1
            2. if Lagging Line above price, +1
            3. If Blue line has crossed red recentlu;, Yesterday +1
        args:
            data: Pandas DataFrame
            names: Names of Columns which hold info about these in order : ('LOW', 'HIGH', 'cloud_green_line_a','cloud_red_line_b','lagging_line','blue_line','red_line')
        '''
        count  = 0

        if isinstance(data, pd.DataFrame):
            LOW, HIGH, cloud_green_line_a, cloud_red_line_b,lagging_line,blue_line,red_line = names
            df = data.copy()
            if df.iloc[0,0] < df.iloc[1,0]: # if the first Date entry [0,0] is < previous data entry [1,0] then it is in ascending order, then reverse it for calculation
                df.sort_index(ascending=True, inplace = True)

            current = df.iloc[0,:]
            if current[cloud_green_line_a] < current[LOW] and current[cloud_red_line_b] < current[LOW]: # Cloud Below
                count += 1
            if df.loc[26,lagging_line] > df.loc[26,HIGH]: # Lagging Line
                count += 1
            if df.loc[1,blue_line] <= df.loc[1,red_line].min() and current[blue_line] >= current[red_line]: # Cross Over
                count += 1
        
        return count
    
    
    def update_eligible(self, limit:float):
        '''
        Save all Eligible stocks for the current week
        args:
            limit: Distance between MA line and the Min(open,close,low,high)
        '''
        self.eligible = {}
        for key in self.registered_stocks:
            result = self.is_ma_eligible(self.open_downloaded_stock(key), limit = limit)
            if result:
                self.eligible.update(result)
        return self.eligible
    
    
    def get_RSI(self, data, periods:int = 14, Close:str = 'CLOSE', ema:bool = True, return_df:bool = False, signal_only:bool = False):
        '''
        Calculate RSI: Relative Strength Index
        args:
            data: Pandas DataFrame
            periods: Length of Moving Window
            Close: Name of the column which contains the Closing Price
            ema: Whether to use Exponential Moving Average instead of Simple
            return_df: Whether to return the whole Dataframe. NOTE: It'll have the last value removed
            signal_only: Whether to return absolute value or Buy / Sell Signal
        '''
        df = data.copy()
        df = self.get_MA(df,200, return_df = True)

        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        close_delta = df['CLOSE'].diff()

        # Make two series: one for lower closes and one for higher closes
        up = close_delta.clip(lower=0)
        down = -1 * close_delta.clip(upper=0)

        if ema: # Use exponential moving average
            ma_up = up.ewm(com = periods - 1, min_periods = periods).mean()
            ma_down = down.ewm(com = periods - 1, min_periods = periods).mean()

        else: # Use simple moving average
            ma_up = up.rolling(window = periods,).mean()
            ma_down = down.rolling(window = periods,).mean()

        rsi = ma_up / ma_down
        rsi = 100 - (100/(1 + rsi))
        df['RSI'] = rsi
        df.sort_index(ascending=True, inplace = True)

        if return_df:
            return df
        
        if signal_only:
            if (df.iloc[0,-1] > 80) or ((df.iloc[0,-1] < 70) and (df.iloc[1,-1] > 70)):# Coming up from above
                signal = "Sell"
            
            elif (df.iloc[0,-1] > 30) and (df.iloc[1,-1] < 30) and (df.loc[0,Close] > df.loc[0,'200-MA']): # Cutting RSI from below but still over 200 MA
                signal = "Buy"

            else: signal = "No Signal"
        
            return signal

        return df.iloc[0,-1] # return Recent RSI value
    
    
    def get_ATR(self, df, window:int=14, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), return_df:bool = False):
        '''
        Get the Average True Range. Concept of Volatility
        args:
            df: Pandas Data Frame
            window: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            return_df: Whether to return the whole Df or the latest value
        '''
        Open, Close, Low, High = names
        data = df.copy()
        if data.iloc[0,0] > data.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            data.sort_index(ascending=False, inplace = True)

        
        data['ATR'] = average_true_range(data[High],data[Low],data[Close])
        data.sort_index(ascending=True, inplace = True)

        if return_df:
            return data

        return data.iloc[0,-1]
        

    def get_MA(self,df, window:int=44, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True, return_df:bool =  True):
        '''
        Get Simple Moving Average
        args:
            df: DataFrame of stocks
            window: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            simple: Whether to return Simple or Exponential Moving Average
            return_df: Whether to return DF or the most recent values
        '''
        Open, Close, Low, High = names
        data = df.copy()
        if data.iloc[0,0] > data.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            data.sort_index(ascending=False, inplace = True)

        Average = f'{str(window)}-MA'
        if simple:
            data[Average]  = data[Close].rolling(window, min_periods = 1).mean()
        else:
            data[Average] = data[Close].ewm(span = window, adjust = False, min_periods = 1).mean()

        data.sort_index(ascending=True, inplace = True)

        if return_df:
            return data
        return data.iloc[0,-1]

    
    def get_CCI(self, data, window:int = 20, names:tuple = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), return_df:bool=False, signal_only:bool = True):
        '''
        Get the CCI (Commodity Channel Index). If it crosses below -100, buy and if it crosses above +100, Sell
        args
            df: DataFrame of stocks
            window: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            return_df: Whether to return the whoe DataFrame or the Recent Value
            generate signal: Whether to generate the CCI Buy or Sell Signal only instead of value
        '''
        Open, Close, Low, High, Date = names
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        df['CCI'] = cci(df[High],df[Low],df[Close], window = window)
        
        if return_df:
            df.sort_index(ascending = True, inplace = True)
            return df
        
        if signal_only:
            if df.iloc[-2,-1] < -100 and df.iloc[-1,-1] > -100: # if recent is above -100 and the previous was below -100; means it has cut -100 from the below 
                signal = 'Buy'
            
            elif df.iloc[-2,-1] > 100 and df.iloc[-1,-1] < 100:  # if recent is below +100 and the previous was above +100; means it has cut +100 from the above
                signal = "Sell"
            
            else: signal = "No Signal"
            
            return signal
        
        return round(df.iloc[-1,-1],2) # Return the absolute value


    def get_ADX(self,data, window:int = 14, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), return_df:bool=False, return_adx_only:bool = True):
        '''
        Get the Value of Average Directional Index 
        args
            df: DataFrame of stocks
            window: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            return_df: Whether to return the whoe DataFrame or the Recent Value
            return_adx_only: Return only the Average value. Esle it returns all of Negative, Positive, Average
        '''
        Open, Close, Low, High = names
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        adx = ADXIndicator(df[High], df[Low], df[Close], window = window)

        df['-DM'] = adx.adx_neg()
        df['+DM'] = adx.adx_pos()
        df['ADX'] = adx.adx()

        df.sort_index(ascending = True, inplace = True)
        if return_df:
            return df

        if return_adx_only:
            return df.iloc[0,-1]

        return df.iloc[0,-3:].values # Negative, Positive, ADX


    def Stochastic(self, data, k_period:int = 14, d_period:int = 3, smooth_k = 3, names:tuple = ('OPEN','CLOSE','LOW','HIGH'),return_df:bool=False, signal_only:bool = False):
        '''
        Implementation of the Stochastic Oscillator. Returns the Fast and Slow lines values or the whole DataFrame
        args:
            data: Pandas Dataframe of the stock
            k_period: Period for the %K /Fast / Blue line
            d_period: Period for the %D / Slow /Red / Signal Line
            smooth_k: Smoothening the Fast line value. With increase/ decrease in number, it becomes the Fast or Slow Stochastic
            names: Names of the columns which contains the corresponding values
            return_df: Whether to return the DataFrame or the Values
            signal_only: Whether to return the signal only
        out:
            Returns either the Array containing (fast_line,slow_line) values or the entire DataFrame
        '''
        OPEN, CLOSE, LOW, HIGH = names
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        # Adds a "n_high" column with max value of previous 14 periods
        df['n_high'] = df[HIGH].rolling(k_period).max()

        # Adds an "n_low" column with min value of previous 14 periods
        df['n_low'] = df[LOW].rolling(k_period).min()

        # Uses the min/max values to calculate the %k (as a percentage)
        df['Blue Line'] = (df[CLOSE] - df['n_low']) * 100 / (df['n_high'] - df['n_low']) # %K or so called Fast Line

        if smooth_k > 1: # Smoothen the Fast, Blue line
            df['Blue Line'] = df['Blue Line'].rolling(smooth_k).mean()
        
        # Uses the %k to calculates a SMA over the past 3 values of %k
        df['Red Line'] = df['Blue Line'].rolling(d_period).mean() # %D of so called Slow Line

        df.drop(['n_high','n_low'],inplace=True,axis=1)

        df.sort_index(ascending = True, inplace = True)

        if signal_only:
            if ((df.loc[0,'Red Line'] - df.loc[0,'Blue Line']) > 0) and ((df.loc[1,'Red Line'] - df.loc[1,'Blue Line']) < 0) and (df.loc[1,'Blue Line'] < 20):
                signal = 'Buy'
            
            if ((df.loc[0,'Red Line'] - df.loc[0,'Blue Line']) < 0) and ((df.loc[1,'Red Line'] - df.loc[1,'Blue Line']) > 0) and (df.loc[1,'Blue Line'] > 80):
                signal = 'Sell'

            else: signal =  'No Signal'
        
            return signal

        if return_df:
            return df

        return df.iloc[0,-2:].values # Return the Recent Values
    

    def _recent_info(self, stock , mvs = [20,50,100,200], names:tuple = ('OPEN','CLOSE','LOW','HIGH')):
        '''
        Get recent info about the data having it's Moving Averages Values, Candle Patterns, RSI, ATR, Bollinger etc
        args:
            stock: DataFrame of stock or the Name
            interval: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            return_df: Whether to return the whoe DataFrame or the Recent Value
        '''
        Open, Close, Low, High = names
        results = []

        if isinstance(stock, str):
            data = self.open_downloaded_stock(stock)
        else:
            data = stock.copy()
        
        data.sort_index(ascending=False, inplace = True)
        for mv in mvs:
            results.append(self.get_MA(data, window = mv, return_df = False))
        
        results.append(self.get_RSI(data, signal_only= True))
        results.append(self.Ichi_count(self.Ichimoku_Cloud(data)))

        results.append(CP.find_name(data.loc[0,Open],data.loc[0,Close],data.loc[0,Low],data.loc[0,High]))
        results.append(CP.double_candle_pattern(data))
        results.append(CP.triple_candle_pattern(data))

        results.append(self.get_ADX(data))
        return results


    def has_golden_crossover(self, data, short_mv:int = 44, long_mv:int = 200,names:tuple = ('OPEN','CLOSE','LOW','HIGH'), lookback:int = 3):
        '''
        Give all the stocks where Golden Cross over has happened Yesterday
        args:
            df: DataFrame of Stock
            short_mv: Short Period Moving Average Days
            long_mv: Long Period Moving Average
            names: Names of columns which have thesew respective values
            lookback: Loockback day. 3 means compare MV values of today vs the day before yesterday
        '''
        if data.shape[0] < long_mv:
            return False

        Open, Close, Low, High = names
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        df['short']  = df[Close].rolling(short_mv, min_periods = 1).mean()
        df['long'] = df[Close].rolling(long_mv, min_periods = 1).mean()
        # return df

        last_short = df.iloc[-lookback,-2]
        current_short = df.iloc[-1,-2]
        last_long = df.iloc[-lookback,-1]
        current_long = df.iloc[-1,-1]

        return (last_short <= last_long) and (current_short > current_long)


    def near_52(self, df, names:tuple = ('LOW','HIGH','52W L', '52W H'), threshold:float = 0.05):
        '''
        Get if Stock is Near 52 Week High or low. If near low, chances are that it'll keep on getting lower and vice versa. if high or low within 5% of 52 Week high or Low
        args:
            df: DataFrame of stock
            names: column names which holds the following info in order
            threshold: Fraction of the 52W high. if 0.05, it means that difference between current high/low and 52W high/low must be within 5% of 52 Week number
         '''
        Low, High, _52wl, _52wh = names
        if abs(df.loc[0,High] - df.loc[0,_52wh]) <= df.loc[0,_52wh] * threshold: # Near 52 W H means Rising:
            return 'Rising High'
        elif abs(df.loc[0, Low] - df.loc[0,_52wl]) <= df.loc[0,_52wl] * threshold: # Near 52 W Low means Falling
            return 'Falling Low'
        return 'Undeterministic'

    
    def macd_signal(self, data, close:str = 'CLOSE'):
        '''
        Get the MACD signal if there is a Buy or Sell signal. Buy signal is when MACD (Blue) line cuts the Signal (Red) from the downside. Vice Versa for Sell signal
        args:
            df: DataFrame of Stock
            close: Names of column which has Closing Valuess
        '''
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

    #     macd_blue_line = macd(df['CLOSE'])
    #     signal_red_line = macd_signal(df['CLOSE'])
        diff = macd_diff(df[close])

        if (diff.iloc[-2] < 0) and (diff.iloc[-1] > 0):
            signal = 'Buy'
        elif (diff.iloc[-2] > 0) and diff.iloc[-1] < 0:
            signal = 'Sell'
        else: signal = 'No Signal'
        return signal


    def get_Pivot_Points(self, data, names:list = ['OPEN','CLOSE','HIGH', 'LOW','DATE'], cpr:bool = True, num_days_back:int = 5, plot:bool = False):
        '''
        Get 'Traditional Daily' Pivot Pointswith 3 support and 3 Resistance. Also it gives Central Pivot Line, Lower Boundary and Upper Boundary
        args:
            data: DataFrame of the stock
            names: Names of columns containing the values
            cpr: Whether to add Central Pivot Range ( CPL, UB and LB )
            num_days_back: How many past days you want to analyse
            plot: Whether to plot the S-R lines etc. Without candles

        out:
            Dictonary of 'num_days_back' data  consisting 9 data points. 7 data points including 1 Pivot and 3 S-R each + 2 Upper and Lower Pivot Boundries
        '''
        df = data.copy()
    
        if df.iloc[0,0] < df.iloc[1,0]: # If data is in reverse order, sort again because We want the dat for recent
            df.sort_index(ascending=False, inplace = True)
    
        pivots = {}
        
        for index in df.index[:num_days_back]:
            open , close, high , low, DATE = df.loc[index, names].values

            if index == 0:
                DATE = df.loc[0, names[-1]] + timedelta(days=1)
            else:
                DATE = df.loc[index-1, names[-1]]

            piv = round((high + low + close) / 3, 2)
            r1 = round((2 * piv) - low, 2)
            r2 = round(piv + (high  - low),2)
            r3 = round(r1 + (high  - low),2)
            s1 = round((2 * piv) - high,2)
            s2 = round(piv - ( high  - low),2)
            s3 = round(s1 - (high - low),2)

            result = {'Pivot':piv,'S-1':s1,'R-1':r1,'S-2':s2,'R-2':r2,'S-3':s3,'R-3':r3}

            if cpr:
                result['LB'] = round((high + low) / 2, 2)
                result['UB'] = round(2 * result['Pivot'] - result['LB'], 2)

            pivots[DATE] = result
        
        if plot:
            PLT.pivot_plot(pivots,name = df.iloc[-1,-1])
        
        return pivots


    def get_recent_info(self, nifty:int=200, custom_list:tuple = None, col_names:tuple = ('DATE','OPEN','CLOSE','LOW','HIGH'), **kwargs):
        '''
        Get Recent Info for all of the stocks and sort them accordingaly
        args:
            nifty: Nifty Index to check
            custom_list: Names of Stocks which you want to analyse
        '''
        nif = self.data[f"nifty_{nifty}"]
        if not custom_list:
            for key in self.recent_info.keys():
                if nifty == key:
                    return self.recent_info[nifty]
                elif nifty < key:
                    return self.recent_info[key][self.recent_info[key]['Index'] == f'Nifty {nifty}']
        else:
            nif = custom_list

        DATE, Open, Close, Low, High = col_names
        names = []
        over_20 = []
        over_50 = []
        over_100 = []
        over_200 = []
        momentum = []
        ichi = []
        c1 = []
        c2 = []
        c3 = []
        T = []
        index = []
        ltp = []
        macd_signal = []
        cci_signal = []
        rsi_signal = []

        for name in nif:
            df  = self.open_downloaded_stock(name)

            LTP = df.loc[0,Close] # last Trading PRice
            ltp.append(LTP)

            T.append(df.loc[0,DATE])
            names.append(name)

            result = self._recent_info(name, **kwargs)

            over_20.append(LTP > result[0])
            over_50.append(LTP > result[1])
            over_100.append(LTP > result[2])
            over_200.append(LTP > result[3])

            ichi.append(result[5])

            c1.append(result[6])
            c2.append(result[7])
            c3.append(result[8])

            momentum.append(result[9])

            index.append(self.get_index(name))

            rsi_signal.append(result[4])
            macd_signal.append(self.macd_signal(df))
            cci_signal.append(self.get_CCI(df, signal_only=True))

        df = pd.DataFrame({'Date':T,'Name':names,'LTP':ltp,'Index':index,"CCI Signal":cci_signal,'RSI Signal':rsi_signal, "MACD Signal":macd_signal,
        'Over 20-SMA':over_20, 'Over 50-SMA':over_50,'Over 100-SMA':over_100,'Over 200-SMA':over_200,
         'Momentum ADX':momentum ,'Ichi Count':ichi, '1 Candle':c1,'2 Candles':c2,'3 Candles':c3})
        
        self.recent_info[nifty] = df
        return df


    def tight_consolidation_stocks(self, stocks:str = 'nifty_200', diff:float = 0.01, min_count:int = 5, lookback_period:int = 7, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), force_live:bool = False):
        '''
        Get all the stocks in tight consolidation. There are certain conditions for consolidation:
        1. Stock has to be above 50 days Moving Average
        2. There has to be a minimum of "min_count" candles in that zone
        3. Closing or Opening has to be within "diff" percentage of the recent Opening / Closing Price
        
        args:
            stocks: Nifty Stocks. Choose from [nifty_50, nifty_100. nifty_200, nifty_500, all_stocks]
            diff: % difference to be eligible for comparison. 0.01 means 1% of the current closing or Opening price. High value will give too many false stocks and low will give too less      
            min_touches: Minimum number of candle touches within that zone. High number means that more reliable breakout
            lookback_period: No of days to lookback. Too huge will give many false names and small value will give too less names
            names: Names of columns which contains the values for that stock
            force_live: Whether to force download the live market. Market is updated after 11:30 PM, force_live gets the date of past 50 days after 3:30
        returns:
                Dictonary containing {stock_name:no of candles}
        '''
        OPEN, CLOSE, LOW, HIGH = names
        result = {}
        
        for name in self.data[stocks]:
            if not force_live:
                df = self.open_downloaded_stock(name)
            else:
                df = NSE.fifty_days_data(name)

            df = self.get_MA(df,window = 50,names = names)
            df = self.get_MA(df,window = 200,names = names)

            closing = df.loc[0,CLOSE]
            compare = max(df.loc[0,OPEN], closing)

            if (closing > df.loc[0,'50-MA']) and (df.loc[0,'50-MA'] > df.loc[0,'200-MA']):
                
                count = 1
                for index in df.index[1:lookback_period]:
                    if compare - (compare * diff) < max(df.loc[index,OPEN],df.loc[index,CLOSE]) < compare + (compare * diff):
                        count += 1

                if count >= min_count:
                    result[name] = count
                    
        return dict(sorted(result.items(), key = lambda x: x[1], reverse= True))