from .investing import Investing
from ta.trend import macd_diff

In = Investing()


class Backtest:
    '''
    Class to hold functions for Backtesting Strategies
    '''
    def MACD(self,min_days:int, top_n:int = 10, nifty:str = 'all', cols:tuple = ('OPEN','CLOSE'), window_slow:int = 26, window_fast:int = 12, window_sign:int = 9):
        '''
        Test MACD Stratedy. Buy next day when MACD cuts Signal from below and Sell next day when MACD cuts Signal from above.
        Next: Implement strategy to add constraint to reduce frequent Buy - Buy, Buy-Sell, Sell-Sell, Sell-Buy if it happens within "n" days in a volatile market
        args:
            min_days: Minimum no of days for a stock to be present at the stock market. Stock newer than these many Trading days will be discarded
            top_n: How many results to return
            nifty: Nifty Index. Select from [nifty_50, nifty_200, nifty_500, all]
            cols: Columns that contains the Open and Close price
            window_slow: Slowing line Period
            window_fast: Fast Lione Length Period
            window_sign: Signal Line Period
            
        returns: A dictonary of top-n stocks which gave highest returns
        '''
        result = {}
        data = In.data['all_stocks'] if nifty == 'all' else In.data[nifty]
        OPEN, CLOSE = cols

        for name in data:
            df = In.open_downloaded_stock(name)
            if df.shape[0] >= min_days: # Most stocks are atleast 407 days old on an average
                
                can_sell = False
                result[name] = {}
                result[name]['days'] = df.shape[0]
                buys = 0 # No of buy signals
                sells = 0 # No of Sell Signals
                
                df.sort_index(ascending=False, inplace = True) # Sort the dataframe
                
                df['MACD Diff'] = macd_diff(df[CLOSE], window_slow = window_slow, window_fast = window_fast, window_sign = window_sign) # Get MACD DIfference
                
                df.sort_index(ascending=False, inplace = True) # Sort Again from oldest to newest
                df.dropna(inplace=True) # Drop the oldest ones
                df.reset_index(inplace=True,drop=True)

                account = 0 # Initial account is 0. 
                for index in df.index[1:-1]:
                    if (df.loc[index,'MACD Diff'] > 0) and (df.loc[index-1,'MACD Diff'] < 0): # Buy means to decrease the account value
                        account -= df.loc[index+1,OPEN]
                        buys += 1
                        can_sell = True # A user can sell only if a buy has been made. So if there is a seel signal for the first trade, skip it

                    elif (df.loc[index,'MACD Diff'] < 0) and df.loc[index-1,'MACD Diff'] > 0: # Sell means to add to the account
                        if can_sell:
                            account += df.loc[index+1,OPEN]
                            sells += 1

                result[name]['account'] = round(account,2)
                result[name]['buys'] = buys # No of Buying opportunities
                result[name]['sells'] = sells # ideally No of Buys == Sells or Buys = Sells + 1
                
                
        return dict(sorted(result.items(), key = lambda x: x[1]['account'], reverse=True)[:top_n])