from helpers.investing import *
from datetime import date, datetime, timedelta
import calendar

In = Investing()
present = date.today()

class IntraDay():
    '''
    Class for Intraday Screening of stocks
    '''
    
    def intraday_whole_num_strategy(self,nifty=50):
        '''
        If Open == High or Low for a stock around 9:30, go long if Open == Low else go high only after 9:30 on 15 minutes candle
        args:
            nifty: Index to choose from File
        returns:
            Dictonary of tuples {"Long":[(name, Open, nifty Index), ...], "Short":[(name, Open, nifty Index), ...]}
        '''
        df = pd.read_csv(join(expanduser('~'),'Downloads',f"MW-NIFTY-{nifty}-{present.day}-{calendar.month_abbr[present.month]}-{present.year}.csv"))

        df['Equal'] = df.apply(lambda row: True if (row['OPEN \n'] == row['HIGH \n'] or row['OPEN \n'] == row['LOW \n']) else False, axis=1)
        df = df.loc[df["Equal"] == True,:]
        df['Whole'] = df['OPEN \n'].apply(lambda x:float(x.replace(',','')).is_integer())
        df = df.loc[df['Whole'] == True,:]

        result = {'Long':[], 'Short':[]}
        for index in df.index:
            open_ = float(df.loc[index,'OPEN \n'].replace(',',''))
            high =  float(df.loc[index,'HIGH \n'].replace(',',''))
            low =  float(df.loc[index,'LOW \n'].replace(',',''))
            ltp = float(df.loc[index,'LTP \n'].replace(',',''))
            name = df.loc[index,'SYMBOL \n']

            result['Long'].append((name,open_,In.get_index(name))) if open_ == low else result['Short'].append((name,open_,In.get_index(name)))

        return result


    def NR7(self,name):
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