from .datahandler import *
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as fplt
import plotly.graph_objects as go
from plotly import colors as plotly_colors
from .candlestick import *
from ta.trend import ADXIndicator

CP = CandlePattern()


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

    
    def get_index(self,symbol:str):
        '''
        Get the Index of the symbol from nifty 50,100,200,500
        args:
            symbol: Name /  ID od the company on NSE
        '''
        for index in self.indices.keys():
            if symbol in self.data[index]:
                return self.indices[index]
        return 'Other'
    

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
    
    
    def get_RSI(self, data, periods:int = 14, Close:str = 'CLOSE', ema:bool = True, return_df:bool = False):
        '''
        Calculate RSI: Relative Strength Index
        args:
            data: Pandas DataFrame
            periods: Length of Moving Window
            Close: Name of the column which contains the Closing Price
            ema: Whether to use Exponential Moving Average instead of Simple
            return_df: Whether to return the whole Dataframe. NOTE: It'll have the last value removed
        '''
        df = data.copy()
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

        return df.iloc[0,-1]
    
    
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


        high_low = data[High] - data[Low]
        high_close = np.abs(data[High] - data[Close].shift())
        low_close = np.abs(data[Low] - data[Close].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)

        ATR = true_range.rolling(window).mean()
        
        data['ATR'] = ATR
        data.sort_index(ascending=True, inplace = True)

        if return_df:
            return data

        return data.iloc[0,-1]
        

    def get_MA(self,df, window:int=14, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), simple:bool = True, return_df:bool =  True):
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
    


    def get_ADX(self,data, interval:int = 14, names:tuple = ('OPEN','CLOSE','LOW','HIGH'), return_df:bool=False, return_adx_only:bool = True):
        '''
        Get the Value of Average Directional Index 
        args
            df: DataFrame of stocks
            interval: Rolling window or the period you want to consider
            names: Column names showing ('OPEN','CLOSE','LOW','HIGH') in the same order
            return_df: Whether to return the whoe DataFrame or the Recent Value
            return_adx_only: Return only the Average value. Esle it returns all of Negative, Positive, Average
        '''
        Open, Close, Low, High = names
        df = data.copy()
        if df.iloc[0,0] > df.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order, then reverse it for calculation
            df.sort_index(ascending=False, inplace = True)

        adx = ADXIndicator(df[High], df[Low], df[Close])

        df['-DM'] = adx.adx_neg()
        df['+DM'] = adx.adx_pos()
        df['ADX'] = adx.adx()

        df.sort_index(ascending = True, inplace = True)
        if return_df:
            return df
        if return_adx_only:
            return df.iloc[0,-1]
        return df.iloc[0,-3:] # Negative, Positive, ADX


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
        
        results.append(self.get_RSI(data))
        results.append(self.Ichi_count(self.Ichimoku_Cloud(data)))

        results.append(CP.find_name(data.loc[0,Open],data.loc[0,Close],data.loc[0,Low],data.loc[0,High]))
        results.append(CP.double_candle_pattern(data))
        results.append(CP.triple_candle_pattern(data))

        results.append(self.get_ADX(data))
        return results


    def has_golden_crossover(self, data, short_mv:int = 44, long_mv:int = 200,names:tuple = ('OPEN','CLOSE','LOW','HIGH'), lookback:int = 3):
        '''
        Give all the stocks where Golden Cross over has happend Yesterday
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
        overbought = []
        oversold = []
        momentum = []
        ichi = []
        c1 = []
        c2 = []
        c3 = []
        T = []
        index = []
        ltp = []

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

            overbought.append(result[4] > 70)
            oversold.append(result[4] < 30)

            ichi.append(result[5])

            c1.append(result[6])
            c2.append(result[7])
            c3.append(result[8])

            momentum.append(result[9])

            index.append(self.get_index(name))

        df = pd.DataFrame({'Date':T,'Name':names,'LTP':ltp,'Index':index,'Over 20-SMA':over_20, 'Over 50-SMA':over_50,'Over 100-SMA':over_100,'Over 200-SMA':over_200,
         'Overbought':overbought, 'Oversold':oversold,'Momentum ADX':momentum ,'Ichi Count':ichi, '1 Candle':c1,'2 Candles':c2,'3 Candles':c3})
        
        self.recent_info[nifty] = df
        return df

                     
    
    def plot_candlesticks(self,df, names = ('DATE','OPEN','CLOSE','LOW','HIGH'), mv:list = [44,100,200]):
        '''
        Plot a candlestick on a given dataframe
        args:
            df: DataFrame
            names: Tuple of column names showing ('DATE','OPEN','CLOSE','LOW','HIGH')
            mv: Moving Averages
        '''
        stocks = df.copy()
        Date, Open, Close, Low, High = names
        colors = sample(self.colors,len(mv))
        stocks.sort_index(ascending=False, inplace = True)  # Without reverse, recent rolling mean will be either NaN or equal to the exact value
    

        candle = go.Figure(data = [go.Candlestick(x = stocks[Date], name = 'Trade',
                                                       open = stocks[Open], 
                                                       high = stocks[High], 
                                                       low = stocks[Low], 
                                                       close = stocks[Close]),])
        for i in range(len(mv)):
            stocks[f'{str(mv[i])}-SMA'] = stocks[Close].rolling(mv[i], min_periods = 1).mean()
            candle.add_trace(go.Scatter(name=f'{str(mv[i])} MA',x=stocks[Date], y=stocks[f'{str(mv[i])}-SMA'], 
                                             line=dict(color=colors[i], width=1.1)))

        candle.update_xaxes(
            title_text = 'Date',
            rangeslider_visible = True,
            rangeselector = dict(
                buttons = list([
                    dict(count = 1, label = '1M', step = 'month', stepmode = 'backward'),
                    dict(count = 6, label = '6M', step = 'month', stepmode = 'backward'),
                    dict(count = 1, label = 'YTD', step = 'year', stepmode = 'todate'),
                    dict(count = 1, label = '1Y', step = 'year', stepmode = 'backward'),
                    dict(step = 'all')])))

        candle.update_layout(autosize = False, width = 1400, height = 600,
                             title = {'text': f"{stocks['SYMBOL'][0]} | {self.all_stocks[stocks['SYMBOL'][0]]}",'y':0.97,'x':0.5,
                                      'xanchor': 'center','yanchor': 'top'},
                             margin=dict(l=30,r=30,b=30,t=30,pad=2),
                             paper_bgcolor="lightsteelblue",)

        candle.update_yaxes(title_text = 'Price in Rupees', tickprefix = u"\u20B9" ) # Rupee symbol
        candle.show()