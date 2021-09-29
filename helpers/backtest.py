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
        self.history = {}


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

    
    def buy(self, df, index:int, account:float, name:str, DATE:str, OPEN:str):
        '''
        Buying Logic. Changes PArameters and return final account value
        args: 
            df: DataFrame to look into
            index: Current index
            DATE: Date Column
            OPEN: Name of Open Column
            account: Current account value
            name: Symbol of the stock
        '''
        self.history[name]['buy_date'].append(df.loc[index+1, DATE])
        self.history[name]['buy_price'].append(df.loc[index+1,OPEN])

        account -= df.loc[index+1,OPEN]
        self.buys += 1
        self.can_buy = False # A user can sell only if a buy has been made. So if there is a seel signal for the first trade, skip it
        return account


    def sell(self, df, index:int, account:float, name:str, DATE:str, OPEN:str):
        '''
        Selling Logic. Changes Parameters and return final account value
        args: 
            df: DataFrame to look into
            index: Current index
            DATE: Date Column
            OPEN: Name of Open Column
            account: Current account value
            name: SYMBOL of the Stock
        '''
        self.history[name]['sell_date'].append(df.loc[index+1, DATE])
        self.history[name]['sell_price'].append(df.loc[index+1,OPEN])

        self.history[name]['p&l'].append(self.history[name]['sell_price'][-1] - self.history[name]['buy_price'][-1])
        self.history[name]['hold_period'].append((self.history[name]['sell_date'][-1] - self.history[name]['buy_date'][-1]).days)

        account += df.loc[index+1,OPEN]
        self.sells += 1
        self.can_buy = True

        return account

    
    def update_final_history(self, name:str, account:int):
        '''
        Update final history per dataframe
        args:
            name: name of the stock
            account: Final account balance
        '''
        self.history[name]['Total P&L'] = round(account,2)
        self.history[name]['buys'] = self.buys # No of Buying opportunities
        self.history[name]['sells'] = self.sells # ideally No of self.buys == self.sells or self.buys = self.sells + 1


    def MACD(self,min_days:int = 365, top_n:int = 10, nifty:str = 'nifty_50', cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), window_slow:int = 26, window_fast:int = 12, window_sign:int = 9, return_df:bool = True):
        '''
        Test MACD Stratedy. Buy next day when MACD cuts Signal from below and Sell next day when MACD cuts Signal from above.
        Next: Implement strategy to add constraint to reduce frequent Buy - Buy, Buy-Sell, Sell-Sell, Sell-Buy if it happens within "n" days in a volatile market
        args:
            min_days: Minimum no of days for a stock to be present at the stock market. Stock newer than these many Trading days will be discarded
            top_n: How many self.historys to return
            nifty: Nifty Index. Select from [nifty_50, nifty_200, nifty_500, all]
            cols: Columns that contains the Open and Close price
            window_slow: Slowing line Period
            window_fast: Fast Lione Length Period
            window_sign: Signal Line Period
            
        returns: A dictonary of top-n stocks which gave highest returns
        '''
        data = In.data['all_stocks'] if nifty == 'all' else In.data[nifty]
        OPEN, CLOSE, LOW, HIGH, DATE = cols

        for name in data:
            df = In.open_downloaded_stock(name)
            if df.shape[0] >= min_days: # Most stocks are atleast 407 days old on an average
                
                self.history_init(name)
                self.history[name]['days'] = df.shape[0]
                self.buys = 0
                self.sells = 0
                account = 0 # Initial account is 0.
                self.can_buy = True
                
                df.sort_index(ascending=False, inplace = True) # Sort the dataframe
                
                df['MACD Diff'] = macd_diff(df[CLOSE], window_slow = window_slow, window_fast = window_fast, window_sign = window_sign) # Get MACD DIfference
                
                df.sort_index(ascending=False, inplace = True) # Sort Again from oldest to newest
                df.dropna(inplace=True) # Drop the oldest ones
                df.reset_index(inplace=True,drop=True)

                for index in df.index[1:-1]:
                    if (df.loc[index-1,'MACD Diff'] < 0) and (df.loc[index,'MACD Diff'] > 0) and (self.can_buy): # Buy means to decrease the account value
                        account = self.buy(df, index, account, name, DATE, OPEN)

                    elif (df.loc[index-1,'MACD Diff'] > 0) and (df.loc[index,'MACD Diff'] < 0) and ((not self.can_buy)): # Sell means to add to the account
                        account = self.sell(df, index, account, name, DATE, OPEN)
                            

                self.update_final_history(name, account)
                  
        dic = dict(sorted(self.history.items(), key = lambda x: x[1]['Total P&L'], reverse=True)[:top_n])
        if return_df:
            return pd.DataFrame(dic).T.iloc[:,[-3,-2,-1,0,1,-5,2,3,4,-4]]
        return dic


    def RSI(self,buying_thresh:float = 30, selling_thresh:float = 70, min_days:int = 365, top_n:int = 10, nifty:str = 'nifty_50', cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), window:int = 14, return_df:bool = True):
        '''
        Test RSI Stratedy. Buy next day when RSI goes below buying_threshold and sell next day when it goes above sell_threshold
        Next: Test each Independent stock where it gives best self.history on different thresholds
        args:
            buying_thresh: Threshold to call a stock oversold. When stock goes below this value, buy
            selling_thresh: Threshold to call a stock Overbought. When stock goes above this value, sell
            min_days: Minimum no of days for a stock to be present at the stock market. Stock newer than these many Trading days will be discarded
            top_n: How many self.historys to return
            nifty: Nifty Index. Select from [nifty_50, nifty_200, nifty_500, all]
            cols: Columns that contains the Open and Close price
            window: Look back period to calculate the RSI

        returns: A dictonary of top-n stocks which gave highest returns
        '''
        data = In.data['all_stocks'] if nifty == 'all' else In.data[nifty]
        OPEN, CLOSE, LOW, HIGH, DATE = cols

        for name in data:
            df = In.open_downloaded_stock(name)
            if df.shape[0] >= min_days: # Most stocks are atleast 407 days old on an average
                
                self.history_init(name)
                self.history[name]['days'] = df.shape[0]
                self.buys = 0
                self.sells = 0
                account = 0 # Initial account is 0.
                self.can_buy = True
                
                df.sort_index(ascending=False, inplace = True) # Sort the dataframe

                df = In.get_RSI(df,return_df = True)
                df.dropna(inplace = True)
                df.sort_index(ascending = False,inplace = True)
                df.reset_index(inplace = True, drop = True)

                for index in df.index[:-1]:
                    if (df.loc[index,'RSI'] < buying_thresh) and (self.can_buy):
                       account = self.buy(df, index, account, name, DATE, OPEN)

                    elif (df.loc[index,'RSI'] > selling_thresh) and (not self.can_buy): # When self.can_buy is False, sell  is active so logic makes sense
                        account = self.sell(df, index, account, name, DATE, OPEN)

                self.update_final_history(name, account)

        dic = dict(sorted(self.history.items(), key = lambda x: x[1]['Total P&L'], reverse=True)[:top_n])
        if return_df:
            return pd.DataFrame(dic).T.iloc[:,[-3,-2,-1,0,1,-5,2,3,4,-4]]
        return dic


    def CCI(self, buying_thresh:float = -100, selling_thresh:float = 100, min_days:int = 365, top_n:int = 10, nifty:str = 'nifty_50', cols = ('OPEN','CLOSE','LOW','HIGH', 'DATE'), window:int = 20, return_df:bool = True):
        '''
        Test CCI Stratedy. Buy next day when CCI comes above buying_threshold and sell next day when it goes below sell_threshold
        Next: Test each Independent stock where it gives best self.history on different thresholds
        args:
            buying_thresh: Threshold to call a stock oversold. When stock goes above this value, buy
            selling_thresh: Threshold to call a stock Overbought. When stock goes below this value, sell
            min_days: Minimum no of days for a stock to be present at the stock market. Stock newer than these many Trading days will be discarded
            top_n: How many self.historys to return
            nifty: Nifty Index. Select from [nifty_50, nifty_200, nifty_500, all]
            cols: Columns that contains the Open, close, low, high
            window: Look back period to calculate the CCI
            return_df: Whether to return the DataFrame

        returns: A dictonary of top-n stocks which gave highest returns
        '''
        data = In.data['all_stocks'] if nifty == 'all' else In.data[nifty]
        OPEN, CLOSE, LOW, HIGH, DATE = cols

        for name in data:
            df = In.open_downloaded_stock(name)
            if df.shape[0] >= min_days: # Most stocks are atleast 407 days old on an average
                
                self.history_init(name)
                self.history[name]['days'] = df.shape[0]
                self.buys = 0
                self.sells = 0
                account = 0 # Initial account is 0.
                self.can_buy = True
                
                df.sort_index(ascending=False, inplace = True) # Sort the dataframe

                df = In.get_CCI(df, window = window, names = cols, return_df = True)
            
                df.dropna(inplace = True)
                df.sort_index(ascending = False,inplace = True)
                df.reset_index(inplace = True, drop = True)

                for index in df.index[1:-1]:
                    if (df.loc[index-1,'CCI'] < buying_thresh) and (df.loc[index,'CCI'] > buying_thresh) and (self.can_buy):
                        account = self.buy(df, index, account, name, DATE, OPEN)


                    elif (df.loc[index-1,'CCI'] > selling_thresh) and (df.loc[index,'CCI'] < selling_thresh) and (not self.can_buy): # When self.can_buy is False, sell  is active so logic makes sense
                        account = self.sell(df, index, account, name, DATE, OPEN)


                self.update_final_history(name, account)


        dic = dict(sorted(self.history.items(), key = lambda x: x[1]['Total P&L'], reverse=True)[:top_n])
        if return_df:
            return pd.DataFrame(dic).T.iloc[:,[-3,-2,-1,0,1,-5,2,3,4,-4]] # Just fancy re arrangement
        return dic