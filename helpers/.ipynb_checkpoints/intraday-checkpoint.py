from helpers.investing import *
from datetime import date, datetime, timedelta
import calendar
from .nse_data import NSEData, requests
from bs4 import BeautifulSoup

In = Investing()
NSE = NSEData()
present = date.today()


class IntraDay():
    '''
    Class for Intraday Screening of stocks
    '''
    
    def whole_number_strategy(self,nifty:int=50, min_val:int=100, max_val:int=5000, return_list = False, print_results:bool = True):
        '''
        If Open == High or Low for a stock around 9:30, go long if Open == Low else go high only after 9:30 on 15 minutes candle
        args:
            nifty: Index to choose from File
            min_val: Minimum value to consider
            return_list: Whether to return list or Dictonary
            max_val: Maximum value of stock price to consider
            print_results: Whether to print the results or not
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
                stock = In.open_downloaded_stock(name)
                atr = round(In.get_ATR(stock),2)
                
                minus = low - open_ if open_ == high else high - open_ # current change that has already been done
                minus = abs(round(minus,2))

                change_perc = str(round((minus/open_)*100, 2))+'%'

                remaining_move = round((minus - atr) / atr,2)
                
                lis.append(name)
                result['Long'].append((name,minus,atr,change_perc, remaining_move, In.get_index(name))) if open_ == low else result['Short'].append((name,minus,atr,change_perc,remaining_move,In.get_index(name)))
        
        if print_results:
            for key in result.keys():
                print(key,":\n","Name - Change - ATR - Change% - Remaining Move - Index:\n")
                for r in sorted(result[key],key=lambda x: x[-2]):
                    print(r,'\n')
            return None
                
        if return_list:
            return lis

        return result


    def NR_strategy(self,name, range_:int = 7):
        '''
        If Current "DAILY" candle has the lowest Range ( High - Low) from the previous "N" candles, go SHORT on next ( 8th candle) if it breaks the low or go LONG if it breaks the high
        args:
            name: name of the stock
            range_: Range to consider for previous days
        '''
        df = In.open_downloaded_stock(name)

        min_range = int(df.loc[0,'HIGH']  - df.loc[0,'LOW']) # Assume the smallest range is for current day
        for index in df.index[1:range_]:
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
    
    
    def prob_by_percent_change(self, symbol:str = None, index:int = 200, time_period:int = 60, change_percent:float = 0.1, sort_by:str = 'Long Probability', top_k:int = 5):
        '''
        Probability of a stock for acheiving "change %" for High / Low if you buy it at market price on the opening bell. Analysed on historical data of "time_period" days 
        It simply calculates that in the past "n" number of days, how mant times a stock achieved "x%" Long (Buy) or Short (Sell) if bought or sold on opening bell
        args:
            time_period: Period of time to look back for analysis. Time in days
            symbol: Symbol of the stock listed on NSe if index is not provided
            index: Nifty Index
            change_percent: How much percent you want to look at. Any positive floating value is acceptable. 1 means 1 %, 10 means 10 %
            sort_by: Sort the values by Long ot Short Probability  
            top_k: How many top values to return
        '''
        assert not (symbol and index), "Provide either 'symbol' or 'index'; not both"
        res = {}
        data = In.data[f'nifty_{index}'] if not symbol else [symbol]
        for name in data:
            df = In.open_downloaded_stock(name)
            high = 0
            low = 0
            for index in df.index[:time_period]:
                if abs(df.loc[index,'OPEN'] - df.loc[index,'HIGH']) >= df.loc[index,'OPEN']* (change_percent / 10):
                    high += 1
                if abs(df.loc[index,'OPEN'] - df.loc[index,'LOW']) >= df.loc[index,'OPEN']* (change_percent / 10):
                    low += 1
            res[name] = {"Long Probability":round(high/time_period,2), "Short Probability":round(low/time_period,2),} #"Index": In.get_index(name)}

        return dict(sorted(res.items(), key=lambda item: item[1][sort_by],reverse = True)[:top_k])


    
    def ATR_strategy(self, index:str, possible_reversal:bool = False):
        '''
        Based on the ATR of the given stock, check how much the data has moved already and how much space to enter in the stock is still remaining.
        If there is no space or the stock has crossed it's ATR, the stock might go in the opposite direction now
        args:
            index: Any name from the DataHandler.data['all_indices_names'].values . Such as NIFTY 50, NIFTY METAL, NIFTY MNC etc
            possible_reversal: Whether to sort the data by possible reversal or remaining move. Possible reversal means it has reached it's ATR in either side and might reverse
        returns: A Dataframe of Possible % of moves remaining. A negative % means there is still a move and a Positive % means that it has either reversed or might reverse
        '''
        
        df = NSE.open_nse_index(index, show_n=500)
        atrs = {}
        for name in df['symbol']:
            try:
                atrs[name] = In.get_ATR(In.open_downloaded_stock(name))
            except:
                atrs[name] = np.nan

        df['ATR'] = atrs.values()
        df.dropna(inplace=True)
        
        
        df['remaining move %'] = df.apply(lambda row: round((max(abs(row['open'] - row['dayHigh']), abs(row['open'] - row['dayLow'])) - row['ATR']) / row['ATR'],2),axis=1)
        
        if possible_reversal:
            df.sort_values('remaining move %', ascending=False, inplace=True)
        else:
            df.sort_values('remaining move %', ascending=True, inplace=True)
            
        return df

    
class MarketSentiment:
    '''
    Get the market sentiment based on TICK, TRIN etc
    '''
    def check_fresh_data(self):
        '''
        Get fresh updated data scraped from the website https://www.traderscockpit.com/?pageView=live-nse-advance-decline-ratio-chart
        '''
        page = requests.get('https://www.traderscockpit.com/?pageView=live-nse-advance-decline-ratio-chart')
        soup = BeautifulSoup(page.content, "lxml")
        latest_updated_on = soup.find("span", {"class": "hm-time"})
        divs = soup.find_all("div", {"class": "col-sm-6"})
        return divs, latest_updated_on
    
    
    def get_TRIN(self, divs):
        '''
        Get the TRIN or so called Arm's Index of the market at any given point of time. Gives the market sentiment along with TICK. TRIN < 1 is Bullishh and  TRIN > 1 is bearish.
        Values below 0.5 or greater than 3 shows Overbought and Oversold zone respectively. Check: https://www.investopedia.com/terms/a/arms.asp
        args:
            divs: Div elements scraped from website
        returns:
             dictonary of volume in Millions of shares for inclining or declining stocks along with the TRIN value
        '''
        self.volume_up = float(divs[4].text[1:-1])
        self.volume_down = float(divs[5].text[1:-1])
        
        self.trin = float(divs[3].find('h4').text.split(' ')[-1].split(':')[-1][:-1])
        return {'Volume Up':self.volume_up, 'Volume Down': self.volume_down, 'TRIN': self.trin}
    
    
    def get_TICK(self, divs):
        '''
        Get the TICK data for live market. TICK is the difference between the gaining stocks and losing stocks at any point in time. Show nmarket sentiment and health along with TRIN.           Buy/ Long Position if TRIN is > 0; sell/short otherwise
        args:
            divs: BeautifulSoup object of all the div elements.
        returns: Dictonary showing stocks which are up/ down corresponding to LAST tick traded value along with the differene betwwn no of stocks and no of stocks down
        '''
        self.stock_up = int(divs[1].text.split(' ')[-1][:-1])
        self.stock_down = int(divs[2].text.split(' ')[-1][:-1])

        self.tick = self.stock_up - self.stock_down
        return {'Up':self.stock_up, "Down":self.stock_down, 'TICK':self.tick}
    
    
    def get_high_low(self, divs):
        '''
        Get no of stocks trading at 52 Week high or 52 week low at any given point of time
        args:
            divs: BeautifulSoup object of all the div elements
        returns: Dictonary of no of stocks trading at high and low
        '''  
        high = int(divs[7].find('p').text.split(' ')[-1])
        low = int(divs[8].find('p').text.split(' ')[-1])

        return {'52W High':high, "52W Low":low}

    
    def get_live_sentiment(self):
        '''
        Get the live sentiment of market based on TICK and TRIN
        '''
        result = {}
        divs, latest_updated_on = self.check_fresh_data()
        
        result['Latest Updated on'] =  latest_updated_on.text[7:]
        result.update(self.get_TICK(divs))
        result.update(self.get_TRIN(divs))
        result.update(self.get_high_low(divs))
        return result