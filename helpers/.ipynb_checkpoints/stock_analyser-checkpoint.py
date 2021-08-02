from datahandler import *
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as fplt
import plotly.graph_objects as go
from plotly import colors as plotly_colors

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
        
        if close < avg or close < open_ : # if red candle or below Average Line, Discard
            return False
        
        diff = min(abs(low - avg), (abs(high - avg)), abs(open_ - avg), abs(close - avg))
        if diff <= limit:
            self.rising[symbol] = stocks.iloc[-mv//2:-1,-1].mean() < avg  # whether the moving average is Upward or Downward according to last 44 days moving averages
            return {symbol : round(diff,2)}

        return False
    
    
    def BollingerBands(self,df, mv:int = 44):
        '''
        Calculate the Upper and Lower Bollinger Bands Given on a Moving Average Line
        args:
            df: Stocks Data
            mv: Moving Average Line value
        '''
        ticker = df.sort_index(ascending=False)

        sma = ticker['CLOSE'].rolling(window = mv).mean()
        std = ticker['CLOSE'].rolling(window = mv).std(0)

        upper_bb = sma + std * 2
        lower_bb = sma - std * 2

        ticker['Upper Bollinger'] = upper_bb
        ticker['Lower Bollinger'] = lower_bb

        return ticker.sort_index(ascending=True)
    
    
    def Ichimoku_Cloud(self,df):
        '''
        Get the values of Lines for Ichimoku Cloud
        args:
            df: Dataframe
        '''
        d = df.sort_index(ascending=False)

        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
        period9_high = d['HIGH'].rolling(window=9).max()
        period9_low = d['LOW'].rolling(window=9).min()
        tenkan_sen = (period9_high + period9_low) / 2


        # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
        period26_high = d['HIGH'].rolling(window=26).max()
        period26_low = d['LOW'].rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
        period52_high = d['HIGH'].rolling(window=52).max()
        period52_low = d['LOW'].rolling(window=52).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

        # The most current closing price plotted 22 time periods behind (optional)
        chikou_span = d['CLOSE'].shift(-26) # Given at Trading View.

        d['blue_line'] = tenkan_sen
        d['red_line'] = kijun_sen
        d['cloud_green_line_a'] = senkou_span_a
        d['cloud_red_line_b'] = senkou_span_b
        d['lagging_line'] = chikou_span
        return d.sort_index(ascending=True)
    
    
    def _is_ichi(self,df, index:str = 'nifty_50'):
        '''
        Get All available IchiMoku available stocks
        args:
            index: Index to Open From
        '''
        count  = 0
        current = df.iloc[0,:]
        if current['cloud_green_line_a'] < current['LOW'] and current['cloud_red_line_b'] < current['LOW']: # Cloud Below
            count += 1
        if df.loc[26,'lagging_line'] > df.loc[26,'HIGH']: # Lagging Line
            count += 1
        if df.loc[1,'blue_line'] <= df.loc[1,'red_line'].min() and current['blue_line'] >= current['red_line']: # Cross Over
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