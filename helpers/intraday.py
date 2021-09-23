from helpers.investing import *
from datetime import date, datetime, timedelta
import calendar
from .nse_data import NSEData

In = Investing()
NSE = NSEData()
present = date.today()

class IntraDay():
    '''
    Class for Intraday Screening of stocks
    '''
    
    def whole_number_strategy(self,nifty:int=50, min_val:int=100, max_val:int=5000, return_list = False):
        '''
        If Open == High or Low for a stock around 9:30, go long if Open == Low else go high only after 9:30 on 15 minutes candle
        args:
            nifty: Index to choose from File
            min_val: Minimum value to consider
            return_list: Whether to return list or Dictonary
            max_val: Maximum value of stock price to consider
        returns:
            Dictonary of tuples {"Long":[(name, Open, nifty Index), ...], "Short":[(name, Open, nifty Index), ...]}
        '''
        lis = []
        result = {'Long':[], 'Short':[]}
        
        url = f"https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20{nifty}"
        df = pd.DataFrame(NSE.get_live_nse_data(url).json()['data'])

        df['Equal'] = df.apply(lambda row: True if (row['open'] == row['dayHigh'] or row['open'] == row['dayLow']) else False, axis=1)
        df = df.loc[df["Equal"] == True,:]
        df['Whole'] = df['open'].apply(lambda x:x.is_integer())
        df = df.loc[df['Whole'] == True,:]

        for index in df.index:
            open_ = df.loc[index,'open']
            
            if min_val < open_ < max_val: # if open is Greater than Max or less than Minimum value then don't consider
                high =  df.loc[index,'dayHigh']
                low =  df.loc[index,'dayLow']
                ltp = df.loc[index,'lastPrice']
                name = df.loc[index,'symbol']
                
                minus = low - open_ if open_ == high else high - open_
                change = str(round((minus/open_)*100, 2))+'%'
                
                lis.append(name)
                result['Long'].append((name,change,In.get_index(name))) if open_ == low else result['Short'].append((name,change,In.get_index(name)))
                
        if return_list:
            return lis
        return result


    def NR7_strategy(self,name):
        '''
        If Current "DAILY" candle has the lowest Range ( High - Low) from the previous 6 candles, go SHORT on next ( 8th candle) if it breaks the low or go LONG if it breaks the high
        args:
            name: name of the stock
        '''
        df = In.open_downloaded_stock(name)

        min_range = int(df.loc[0,'HIGH']  - df.loc[0,'LOW']) # Assume the smallest range is for current day
        for index in df.index[1:7]:
            if (int(df.loc[index,'HIGH']  - df.loc[index,'LOW'])) <= min_range:
                return False
        return True
    
    
    
    def common_from_diff_strategy(self,index:int=50):
        '''
        Mix Multiple Stratgies such as NR-7, Whole Num, Sectoral Analysis etc and find if there is any of the common present
        args:
            index: Nifty Index - 50,100, 200, 500
        '''
        nr = set()
        for stock in In.data[f'nifty_{index}']:
            nr.add(self.NR7_strategy(stock))

        whole = set(self.whole_number_strategy(index,return_list = True))

        # add Sector/ Theme also

        return whole.intersection(nr)