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
    
    def whole_number_strategy(self,nifty:int=50, filter_by:list = None, min_val:int=100, max_val:int=5000, return_list = False, print_results:bool = True, include_whole:bool = True):
        '''
        If Open == High or Low for a stock around 9:30, go long if Open == Low else go high only after 9:30 on 15 minutes candle
        args:
            nifty: Index to choose from File
            filter_by: Show only those stocks
            min_val: Minimum value to consider
            return_list: Whether to return list or Dictonary
            max_val: Maximum value of stock price to consider
            print_results: Whether to print the results or not
            include_whole: Whether to Include the XX.00 or not
        returns:
            Dictonary of tuples {"Long":[(name, Open, nifty Index), ...], "Short":[(name, Open, nifty Index), ...]}
        '''
        lis = []
        result = {'Long':[], 'Short':[]}
        
        url = f"https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20{nifty}"
        df = pd.DataFrame(NSE.get_live_nse_data(url).json()['data'])

        if filter_by:
            df = df[df['symbol'].isin(filter_by)]


        df['Equal'] = df.apply(lambda row: True if (row['open'] == row['dayHigh'] or row['open'] == row['dayLow']) else False, axis=1)
        df = df.loc[df["Equal"] == True,:]

        if include_whole:
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
    
    
    def prob_by_percent_change(self, symbol:list = None, index:int = 200, time_period:int = 60, change_percent:float = 0.1, sort_by:str = 'Long Probability', top_k:int = 5):
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
        data = In.data[f'nifty_{index}'] if not symbol else symbol
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
    
    
    def get_quantity(self, name, position:str, budget:float, risk:float, entry:float, stop_loss:float, expected_target:float, risk_to_reward_ratio:float=2, leverage:float = 5):
        '''
        Get the quantity to Buy / Sell given your Budget, Amount you are willing to risk, Your leverage etc
        args:
            name: Name of the stock
            position: Long (buy) or Short (Sell). Must be  long or short
            budget: Actual Budget you have
            leverage: Given by the bri=oker. Mostly it is 4 or 5
            risk: Maximum risk you can have on this trade
            entry: Entry Value
            expected_target: Target you are expecting. Might be a trend line or a major resistance area or Fibonachi level
            stop_loss: Max allowable price to reach in case market goes against you
            risk_to_reward_ratio: Amount you sre willing to make against the Risk. Usually 2 or 3 in intraday
        '''
        if risk > 0.03 * budget:
            print('Risk More than 3% of Capital. Don not take the trade')
            return None
        
        budget = budget * leverage
        diff = entry - stop_loss if position == 'long' else stop_loss - entry
        quantity = risk / diff 
        profit = risk_to_reward_ratio * diff
        target = entry + profit if position == 'long' else entry - profit
        
        if (target > expected_target) and position == 'long':
            print(f"Expected Target can't be reached with {risk_to_reward_ratio} Risk-to-Reward. Might not be a good Trade")
            return None
            
        if (target < expected_target) and position == 'short':
            print(f"Expected Target can't be reached with a Risk-to-Reward ratio of {risk_to_reward_ratio}. Might not be a good Trade")
            return None
        
        return {'quantity':quantity,'target':target}
    

class IntradayStockSelection():
    '''
    Class to help Intraday Stock Selection
    Read more at: https://www.kotaksecurities.com/ksweb/intraday-trading/how-to-choose-stocks-for-intraday-trading
    '''
    
    def move_range_std(self, stocks:[str,list], time_period:int, return_df:bool = True) -> tuple:
        '''
        Stocks Attributes like Average Move % per day, Range, Standard Deviation (Volatility)
        args:
            stocks: Any list of valid NSE symbols or any of the ['nifty_50','nifty_100','nifty_200','all_stocks','f&o']
            time_period: MAx Time period to consider
            return_df: whether to return a DataFrame
        returns: Tuple of Dictonaries with Median values of Move, Ranges and Standard Deviation over the period OR a DataFrame
        '''
        mov = {}
        ranges = {}
        ranges_abs = {}
        devs = {} # standard deviation or so called volatility

        data = In.data[stocks] if stocks in ['nifty_50','nifty_100','nifty_200','nifty_500','all_stocks','f&o'] else stocks

        for name in data:
            df = In.open_downloaded_stock(name)
            df = df.iloc[:time_period,:]
            df.sort_index(ascending=False,inplace = True)
            df.reset_index(inplace=True,drop=True)
            cp = []
            rng = []
            close = []
            rng_abs = []

            for index in df.index.values.tolist()[1:]:
                cp.append(abs(df.loc[index,'CLOSE'] - df.loc[index,'OPEN']) / df.loc[index,'OPEN'] ) # df.loc[index-1,'CLOSE']) # Gives Day's Move. Less Diff -> More Dojis
                rng.append(abs(df.loc[index,'HIGH'] - df.loc[index,'LOW']) / df.loc[index,'OPEN']) # mitigate gaps
                rng_abs.append(abs(df.loc[index,'HIGH'] - df.loc[index,'LOW']))

            mov[name] = np.median(cp)
            ranges[name] = np.median(rng)
            ranges_abs[name] = round(np.median(rng_abs),2)
            devs[name] = round(df['CLOSE'].std(),2)

        if return_df:
            df = pd.DataFrame([mov,ranges,ranges_abs,devs]).T

            df.rename(columns = {0:'Move % (wrt OPEN)',1:'Range % (wrt OPEN)',2:"Range (in Rupees)",3:'STD (in Rupees)'},inplace = True)
            df['Move % (wrt OPEN)'] = df['Move % (wrt OPEN)'].apply(lambda x: round(x*100, 1))
            df['Range % (wrt OPEN)'] = df['Range % (wrt OPEN)'].apply(lambda x: round(x*100, 1))
            df.sort_values(by = ['Move % (wrt OPEN)', 'Range % (wrt OPEN)'], ascending=[0,0], inplace = True)

            df['ATR (14 Days)'] = df.index.map(lambda x: round(In.get_ATR(In.open_downloaded_stock(x)),2))
            df['LTP (CLOSE in Rupees)'] = df.index.map(lambda x: round(In.open_downloaded_stock(x).loc[0,'CLOSE'],2))
            return df

        return (mov,ranges,devs)
        
        