from datetime import datetime, time
from .investing import Investing
from ta.trend import macd_diff
import pandas as pd

In = Investing()

class Backtest():
    '''
    Class to hold functions for Backtesting Strategies
    '''
    def __init__(self):
        '''
        '''
        self.strategies = {'cci':self.cci, 'macd':self.macd, 'rsi': self.rsi,'ma':self.ma, "stochastic_osc":self.stochastic_osc}


    def history_init(self, name):
        '''
        Set the history data according to the stocks in it
        '''
        self.history[name] = {}
        self.history[name]['buy_date'] = []
        self.history[name]['sell_date'] = []
        self.history[name]['buy_price'] = []
        self.history[name]['sell_price'] = []
        self.history[name]['p&l'] = []
        self.history[name]['hold_period'] = []

    
    def buy(self, name:str, date:datetime, price:float):
        '''
        Buying Logic. Changes PArameters and return final account value
        args: 
            name: Symbol of the stock
            date: date of buying
            price: Buying Price
        '''
        self.history[name]['buy_date'].append(date)
        self.history[name]['buy_price'].append(price)

        self.buys += 1
        self.can_buy = False # A user can sell only if a buy has been made. So if there is a sell signal for the first trade, skip it


    def sell(self, name:str, date:datetime, price: float):
        '''
        Selling Logic. Changes Parameters and return final account value
        args: 
            name: SYMBOL of the Stock
            date: date of selling
            price: Selling Price
        '''
        self.history[name]['sell_date'].append(date)
        self.history[name]['sell_price'].append(price)

        self.history[name]['p&l'].append(self.history[name]['sell_price'][-1] - self.history[name]['buy_price'][-1])
        self.history[name]['hold_period'].append((self.history[name]['sell_date'][-1] - self.history[name]['buy_date'][-1]).days)

        self.sells += 1
        self.can_buy = True

    
    def update_final_history(self, name:str,):
        '''
        Update final history per dataframe
        args:
            name: name of the stock
        '''
        self.history[name]['buys'] = self.buys # No of Buying opportunities
        self.history[name]['sells'] = self.sells # ideally No of self.buys == self.sells or self.buys = self.sells + 1

    
    def calculate_ROI(self, row):
        '''
        Calculate Return on Investment. (Total Profit/ Total Investment) * 100 %
        '''
        if row['sells'] == row['buys']:
            investment = sum(row['buy_price'])

        elif row['buys'] == row['sells'] + 1:
            investment = sum(row['buy_price'][:-1])
        
        return round((sum(row['p&l']) / investment) *100, 2)

        # which one is right formula ?

        # if row['sells'] == row['buys']:
        #     investment = row['buy_price']

        # elif row['buys'] == row['sells'] + 1:
        #     investment = row['buy_price'][:-1]

        # result = 0
        # for i in range(len(investment)):
        #     result += ((row['p&l'][i]) / investment[i]) * 100

        # return round(result/len(investment), 2)


    def backtest(self, strategy:str, min_days:int = 365, top_n:int = 10, stocks:str = 'nifty_50', return_df:bool = True, **kwargs):
        '''
        Test the strategies based on the given Buy and Sell Criteria
        args:
            strategy: Name of the strategy to backtest. See 'BackTest.strategies' for all available strageies 
            min_days: Minimum no of days for a stock to be present at the stock market. Stock newer than these many Trading days will be discarded
            top_n: How many top values to return. Number between 1-1886 or 'all'
            stocks: Select from [nifty_50, nifty_200, nifty_500, all] or a list of stocks to choose from such as ["INFY","SBIN"] or ["HDFC"]
            cols: Columns that contains the Open, close, low, high
            window: Look back period to calculate the CCI
            return_df: Whether to return the DataFrame

        returns: A dictonary of top-n stocks which gave highest win%
        '''
        buy_sell_logic = self.strategies[strategy]
        self.history = {}

        if isinstance(stocks,str):
            data = In.data['all_stocks'] if stocks == 'all' else In.data[stocks]
        else: data = stocks

        top_n = top_n if isinstance(top_n,int) else len(data)

    
        for name in data:
            df = In.open_downloaded_stock(name)
            if df.shape[0] >= min_days: # Most stocks are atleast 407 days old on an average
                
                self.history_init(name)
                self.history[name]['days'] = df.shape[0]
                self.buys = 0
                self.sells = 0
                self.can_buy = True
                
                df.sort_index(ascending=False, inplace = True) # Sort the dataframe

                buy_sell_logic(name, df, **kwargs) # Use buy Sell Logic
                self.update_final_history(name)


        x = pd.DataFrame(self.history).T
        x = x.loc[x['sells']>0,:] # No need for those where no sell has been made. Won't be able to produce any win%. Division by Zero error
        # x['Total P&L'] = x['p&l'].apply(lambda x: sum(x))
        x['ROI'] = x.apply(lambda row: self.calculate_ROI(row),axis=1)
        x['wins'] = x['p&l'].apply(lambda x: sum([True if i >0 else False for i in x]))
        x['losses'] = x.apply(lambda row: row['sells'] - row['wins'],axis=1)
        x['win%'] = x.apply(lambda row: round((row['wins'])/row['sells'],2),axis=1)
        

        x.sort_values(['win%','wins','ROI'],ascending=False, inplace=True) # 3 priorities of sorting in case of conflict
        return x.iloc[:top_n,[-1,-3,-2,-4,4,0,1,2,3,5,7,8,6]] # just shuffling of columns on "first thing first" basis


    def cci(self, name, df, buying_thresh:float = -100, selling_thresh:float = 100, window:int = 20, cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE')):
        '''
        Test CCI Stratedy. Buy next day when CCI comes above buying_threshold and sell next day when it goes below sell_threshold
        Next: Test each Independent stock where it gives best self.history on different thresholds
        args:
            name: Name of the stock
            df: DataFrame of that Stock
            buying_thresh: Threshold to call a stock oversold. When stock goes above this value, buy
            selling_thresh: Threshold to call a stock Overbought. When stock goes below this value, sell
            cols: Columns that contains the Open, close, low, high
            window: Look back period to calculate the CCI

        returns: A dictonary of top-n stocks which gave highest returns
        '''
        OPEN, CLOSE, LOW, HIGH, DATE = cols

        df = In.get_MA(df, window = 50, names = (OPEN, CLOSE, LOW, HIGH), return_df = True)
        df = In.get_MA(df, window = 200, names = (OPEN, CLOSE, LOW, HIGH), return_df = True)

        df = In.get_CCI(df, window = window, names = cols, return_df = True)
        
    
        df.dropna(inplace = True)
        df.sort_index(ascending = False,inplace = True)
        df.reset_index(inplace = True, drop = True)

        for index in df.index[1:-1]:
            if (df.loc[index-1,'CCI'] < buying_thresh) and (df.loc[index,'CCI'] > buying_thresh) and (self.can_buy) and \
                (df.loc[index, CLOSE] > df.loc[index,'50-MA']) and (df.loc[index,'50-MA'] > df.loc[index,'200-MA']): # whrn 50-SMA is above 200-SMA

                self.buy(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])
                

            elif (not self.can_buy):
                if ((df.loc[index-1,'CCI'] > selling_thresh) and (df.loc[index,'CCI'] < selling_thresh) or (df.loc[index,'CCI'] > 200)):
                    selling_price = df.loc[index+1,OPEN]

                    self.sell(name, date = df.loc[index+1, DATE], price = selling_price)



    def rsi(self,name, df, buying_thresh:float = 30, selling_thresh:float = 70, cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), window:int = 14,):
        '''
        Test RSI Stratedy. Buy next day when RSI comes above buying thresh from the below and sell next day when it goes above 80 comes down from above 70.
        Condition is when the stock is trading above 200-MA
        Next: Test each Independent stock where it gives best self.history on different thresholds
        args:
            name: Name of the stock
            df: DataFrame of that Stock
            buying_thresh: Threshold to call a stock oversold. When stock goes below this value, buy
            selling_thresh: Threshold to call a stock Overbought. When stock goes above this value, sell
            cols: Columns that contains the Open and Close price
            window: Look back period to calculate the RSI

        returns: A dictonary of top-n stocks which gave highest returns
        '''
        OPEN, CLOSE, LOW, HIGH, DATE = cols

        df = In.get_MA(df, window = 200, names = (OPEN, CLOSE, LOW, HIGH), return_df = True)

        df = In.get_RSI(df,return_df = True)

        df.dropna(inplace = True)
        df.sort_index(ascending = False,inplace = True)
        df.reset_index(inplace = True, drop = True)


        for index in df.index[1:-1]:
            if (df.loc[index-1,'RSI'] < buying_thresh) and (df.loc[index,'RSI'] > buying_thresh) and (self.can_buy) and \
                (df.loc[index, CLOSE] > df.loc[index,'200-MA']):

                self.buy(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])
                

            elif (not self.can_buy):
                if ((df.loc[index-1,'RSI'] > selling_thresh) and (df.loc[index,'RSI'] < selling_thresh) or (df.loc[index,'RSI'] > 80)):
                    selling_price = df.loc[index+1,OPEN]

                    self.sell(name, date = df.loc[index+1, DATE], price = selling_price)


    def macd(self,name, df, cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), window_slow:int = 26, window_fast:int = 12, window_sign:int = 9):
        '''
        Test MACD Stratedy. Buy next day when MACD cuts Signal from below and Sell next day when MACD cuts Signal from above.
        Next: Implement strategy to add constraint to reduce frequent Buy - Buy, Buy-Sell, Sell-Sell, Sell-Buy if it happens within "n" days in a volatile market
        args:
            name: Name of the stock
            df: DataFrame of that Stock
            cols: Columns that contains the Open and Close price
            window_slow: Slowing line Period
            window_fast: Fast Line Length Period
            window_sign: Signal Line Period
            
        returns: A dictonary of top-n stocks which gave highest returns
        '''
        OPEN, CLOSE, LOW, HIGH, DATE = cols
      
        df['MACD Diff'] = macd_diff(df[CLOSE], window_slow = window_slow, window_fast = window_fast, window_sign = window_sign) # Get MACD DIfference
        
        df.sort_index(ascending=False, inplace = True) # Sort Again from oldest to newest
        df.dropna(inplace=True) # Drop the oldest ones
        df.reset_index(inplace=True,drop=True)

        for index in df.index[1:-1]: # Has to consider Past and Future candle  so [1:-1] 
            if (df.loc[index-1,'MACD Diff'] < 0) and (df.loc[index,'MACD Diff'] > 0) and (self.can_buy): # Buy means to decrease the account value
                self.buy(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])

            elif (df.loc[index-1,'MACD Diff'] > 0) and (df.loc[index,'MACD Diff'] < 0) and ((not self.can_buy)): # Sell means to add to the account
                self.sell(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])
  
    
    def ma(self, name, df, cols:tuple = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), ma_type:str='simple', window:int = 44, diff:float = 0.015, r2r:float = 1.99):
        '''
        Backtest Moving Average Strategy. Buy next day when recent Candle is Green, taking support on Moving Average Line, above 200 MA, RSI less than 70
        args:
            name: Name of the stock
            df: DataFrame of that Stock
            cols: Columns that contains the Open and Close price
            ma_type: "simple" or "ema"
            window: Length of the window
            diff: Difference % between the MA line and candle. 0.01 means 1%
            r2r: Risk to Reward Ratio 1:2 means if the risk is of 1 rupee, then exit only after gaining 2rupees
        '''
        OPEN, CLOSE, LOW, HIGH, DATE = cols
        simple = True if ma_type == 'simple' else False

        df = In.get_MA(df, window = window, names = (OPEN, CLOSE, LOW, HIGH), simple = simple, return_df = True)
        df = In.get_MA(df, window = 200, names = (OPEN, CLOSE, LOW, HIGH), simple = simple, return_df = True)
        df = In.get_RSI(df, Close = CLOSE, return_df = True)

        df.sort_index(ascending=False, inplace = True) # Sort Again from oldest to newest
        df.dropna(inplace=True) # Drop the oldest ones
        df.reset_index(inplace=True,drop=True)


        for index in df.index[1:-1]: # start from second entry because we have to consider that -> stop loss is lowest of current OR current
            if (df.loc[index,CLOSE] > df.loc[index,OPEN]) and (df.loc[index,CLOSE] > df.loc[index,f"{window}-MA"]) and \
            (df.loc[index,CLOSE] > df.loc[index,"200-MA"]) and (df.loc[index,'RSI'] < 70) and \
            (min(abs(df.loc[index,OPEN] - df.loc[index,f"{window}-MA"]), abs(df.loc[index,LOW] - df.loc[index,f"{window}-MA"])) < (df.loc[index,CLOSE] * diff)):

                if (self.can_buy) and (df.loc[index+1,HIGH] > df.loc[index,HIGH]):
                    
                    buying_price = df.loc[index,HIGH]
                    self.buy(name, date = df.loc[index+1, DATE], price = buying_price)
                    stop_loss = min(df.loc[index, LOW], df.loc[index-1, LOW]) # stop loss is minimum of low of current or previous candle
                    target_price = buying_price + (r2r * (buying_price - stop_loss))

            elif (not self.can_buy):  
                if df.loc[index, HIGH] > target_price:
                     selling_price = target_price
                     
                elif df.loc[index, LOW] < stop_loss:
                    selling_price  = stop_loss

                elif df.loc[index, HIGH] > buying_price + (buying_price * 0.10): # if we get 10% on investment
                    selling_price = buying_price + (buying_price * 0.10)
                    
                else: selling_price = None

                if selling_price: # if the stock reaches either the target or hits stop loss
                    self.sell(name, date = df.loc[index, DATE], price = selling_price)


    def stochastic_osc(self,name, df, k_period:int = 14, d_period:int = 3, smooth_k = 3, buying_thresh:int = 20, selling_thresh:int =  80, cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE')):
        '''
        Test Stochastic Oscillator Strategy: Different from Stochastic RSI
        1. Buy when the fast line cuts the slow line from below in an OVERSOLD zone (below 30). Wait for both lines to go above Oversold and then buy
        2. Sell when both lines reaches Overbought region (above 70) and fast line crosses slow from above
        3. Both lines must be Over the buying threshold to buy or Below the selling_threshold to sell
        
        https://www.elearnmarkets.com/blog/stochastic-indicator/

        args:
            name: Name of the stock
            df: DataFrame of that Stock
            k_period: Period for the %K /Fast / Blue line
            d_period: Period for the %D / Slow /Red / Signal Line
            smooth_k: Smoothening the Fast line value. With increase/ decrease in number, it becomes the Fast or Slow Stochastic
            buying_thresh: Threshold for defining Oversold Zone
            selling_thresh: Value for defining Overbought Zone
            cols: Names of the columns which contains the corresponding values
            
        returns: A dictonary of top-n stocks which gave highest returns
        '''
        OPEN, CLOSE, LOW, HIGH, DATE = cols
      
        df = In.get_MA(df, window = 200, names = (OPEN, CLOSE, LOW, HIGH), return_df = True) # Buy Only Over 200-MA Closing
        df = In.Stochastic(df, k_period, d_period, smooth_k, names=(OPEN, CLOSE, LOW, HIGH), return_df=True) # Get Values of Stochastic Blue and Red Line
        df['Diff'] = df['Red Line'] - df['Blue Line']
        
        df.sort_index(ascending=False, inplace = True) # Sort Again from oldest to newest
        df.dropna(inplace=True) # Drop the oldest ones which are NaN-s
        df.reset_index(inplace=True,drop=True)

        buy_lock = False
        sell_lock = False
        for index in df.index[1:-1]: # Has to consider Past and Future candle  so [1:-1]

            # Many conditions. Blue line out but Red line inside
            # Blue and red both outside
            # Blue and red both inside
            
            if (df.loc[index-1,'Diff'] < 0) and (df.loc[index,'Diff'] > 0):
                sell_lock = False
                if (df.loc[index,'Blue Line'] < buying_thresh) and (df.loc[index,'Red Line'] < buying_thresh):
                    buy_lock = True


            elif (df.loc[index-1,'Diff'] > 0) and (df.loc[index,'Diff'] < 0):
                buy_lock = False

                if (df.loc[index,'Blue Line'] > selling_thresh) and (df.loc[index,'Red Line'] > selling_thresh):
                    sell_lock = True


            if (self.can_buy) and (buy_lock) and (df.loc[index,'Red Line'] > buying_thresh) and (df.loc[index,CLOSE] > df.loc[index,'200-MA']): # If red line crosses the buying threshold, means blue is already there
                self.buy(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])

            elif (not self.can_buy) and (sell_lock) and (df.loc[index,'Red Line'] < selling_thresh): # Sell only when both the lines are below the selling threshold
                self.sell(name, date = df.loc[index+1, DATE], price = df.loc[index+1,OPEN])
