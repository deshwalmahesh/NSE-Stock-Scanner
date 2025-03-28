from .candlestick import *
from .datahandler import *
from .stock_analyser import *

CP = CandlePattern()

class Investing(AnalyseStocks):
    def __init__(self,rolling_mean:int=44,check_fresh = False):
        '''
        args:
            rolling_mean: Rolling Simple Mean to calulate
        '''
        super().__init__(check_fresh = check_fresh)
        self.rm = rolling_mean
        self._eligible = None
        self.data = self.read_data()
        self.all_ichi = None
        self.picked = None
        self._old_budget = -1
        self.diff = -1
        
        
        
    def stock_current_index_performance(self,symbol:str):
        '''
        Returnns the live index value of a symbol for all the indices Nifty, Sectoral, Thematic in which the stock exists
        args:
            symbol: Name of the Stock listed on NSE
        '''
        indices = self.get_index(symbol,'all')
        if len(indices):
            indices = [x.upper() for x in indices]
            df = NSE.current_indices_status(999)
            if len(df):
                return df[df['index'].isin(indices)]
            print(f"{symbol} does not belong in any of the Nifty, Sectoral and Thematic Indices")
      

    def _get_all_ichi(self,budget:float, index:str='nifty_500', refit = False):
        '''
        Get all Stocks who are almost perfect for Ichimoku execution
        args:
            budget: Your Budget
            index: Which Index to Search
        '''
        if self.all_ichi and  (not refit):
            return self.all_ichi
        
        all_ichi = {}
        data = self.data[index] if index else self.all_stocks
        for name in data:
            df = self.Ichimoku_Cloud(self.open_downloaded_stock(name))
            count = self.Ichi_count(df) 
            if count and df.loc[0,'HIGH'] < budget:
                all_ichi[name] = count
                
        self.all_ichi = all_ichi
        return self.all_ichi
    
    
    def highlight_falling(self, s, column:str):
        '''
        Highlight The rows where average is falling
        args:
            s: Series
            column: Column name(s)
        '''
        is_max = pd.Series(data=False, index=s.index)
        is_max[column] = s.loc[column] == True
        return ['' if is_max.any() else 'background-color: #f7a8a8' for v in is_max]
    
    
    def calculate(self, budget, custom_stocks:bool=False,High:str = 'HIGH', Close:str = 'CLOSE', delta:float = 1, nifty:str = 'nifty_200', diff = 13, show_only:bool=True, ):
        '''
        Pick Stocks based on all available and which are within your budget
        args:
            budget: Total available budget. Stocks under this budget will be considered only
            custom_stocks: Whether to calculate for your custom stocks in place of nifty or something else
            High: Column name which show High
            Close: Column Name which shows last closing price
            delta: Value above the Last Highest Traded Price
            nifty: nifty index to consider
            show_only: If you want to see formatted part only
            diff: Max Allowed Distance between Min(close,open,low,high) and High
        ''' 
        refit = True if (self._old_budget < budget or self.diff != diff) else False
        self._old_budget = budget
        self.diff = diff
        ichi = self._get_all_ichi(budget ,refit = refit)
        
        if (not self._eligible) or refit:
            self._eligible  = self.update_eligible(limit = diff)
        
        if not custom_stocks: 
            keys = set(self._eligible.keys()).intersection(set(self.data[nifty])) if nifty else list(self._eligible.keys()) 
            if not len(keys):
                warnings.warn('No matching Stocks Found. Increase Distance or Nifty Index')
                return None
        else:
            keys = custom_stocks
        
        values = []
        one_can = []
        two_can = []
        three_can = []
        atr = []
        rsi = []
        near_52 = []
        macd_signal = []
        cci_value = []
        adx = []
        
        for key in keys:
            try:
                df = self.open_downloaded_stock(key)
            except Exception as e:
                    print('Exception Opening: ',key)
                
            if (df.loc[0,High] + delta > budget) or (df.loc[0,High] < 100):
                del self._eligible[key]
                
            else:
                values.append(df.iloc[0,:])
                one_can.append(CP.find_name(df.loc[0,'OPEN'],df.loc[0,'CLOSE'],df.loc[0,'LOW'],df.loc[0,'HIGH']))
                two_can.append(CP.double_candle_pattern(df))
                three_can.append(CP.triple_candle_pattern(df))
                rsi.append(self.get_RSI(df))
                atr.append(self.get_ATR(df))
                near_52.append(self.near_52(df))
                macd_signal.append(self.macd_signal(df))
                cci_value.append(self.get_CCI(df,signal_only=False, return_df=False))
                adx.append(self.get_ADX(df))
                
                
        columns = df.columns
        df = pd.DataFrame(values,columns=columns,index = range(len(values)))
        df = df.merge(pd.DataFrame({'SYMBOL':self._eligible.keys(), 'Diff':self._eligible.values()}),on='SYMBOL')
        
        # df['Rising'] = df['SYMBOL'].apply(lambda x: self.rising[x]) # Get Rising or Falling
        df['CCI Value'] = cci_value
        df['RSI Value'] = rsi
        df['MACD Signal'] = macd_signal
        df['ADX'] = adx
        df['Direction'] = near_52
        df['Ichi'] = df['SYMBOL'].apply(lambda x: ichi[x] if ichi.get(x) else 0)
        
        df['ATR'] = atr
        
        df['Triple Candle'] = three_can
        df['Double Candle'] = two_can
        df['Recent Candle'] = one_can
        
        df['Index'] = df['SYMBOL'].apply(lambda x: self.get_index(x)) # Get Rising or Falling

        self.picked = df.sort_values('Diff',ascending = True)
        if show_only:
            return self.picked.style.apply(self.highlight_falling, column=['Rising'], axis=1) # set style
        else:
            return self.picked
        
        
    def show_full_stats(self, budget,risk, custom_stocks:bool = False, High = 'HIGH', Close = 'CLOSE', delta:float=1, diff:float = 13, nifty:str = 'nifty_500'):
        '''
        Show Extra Stats
        args:
            budget: Total available budget. Stocks under this budget will be considered only
            risk: How much risk you want to take
            High: Column name which show High
            Close: Column Name which shows last closing price
            delta: Value above the Last Highest Traded Price
            nifty: nifty index to consider
            diff: MAx Allowed Difference between Line and the Price. diff is the %  of the Recent Closing Price
            custom_stocks: Whether to override in place of Custom
        '''
        self.picked = self.calculate(budget, custom_stocks, High, Close, delta, nifty = nifty, diff = diff, show_only = False)

        
        expec_change = []
        max_risk = []
        
         
        if not isinstance(self.picked, pd.DataFrame):
            return 'No match found. Increase Budget / Diff / Risk / Nifty Index '
        
        pic = self.picked.copy()
        for index in pic.index:
            name = pic.loc[index,'SYMBOL']
            result = self.get_particulars(name,budget,risk)
            if result:
                expec_change.append(result['Target %'])
                max_risk.append(result['Max loss on this config'])
            else:
                expec_change.append(np.inf)
                max_risk.append(np.inf)

        pic['Expected Change %'] = expec_change
        pic['Max Config Risk'] = max_risk
        return pic
        
        
    def get_particulars(self, name, budget:float, risk:float, risk_to_reward_ratio:float=2, leverage:float = 1, entry:float=None, stop_loss:float=None, Low:str = 'LOW', High:str = 'HIGH', delta:float = 0.001, plot_candle:bool = False):
        '''
        Display the particulars of a trade before buying
        args:
            name: name of the particular stock
            risk: How much loss you can survive at the end of day PER TRADE. Total capacity will be No of shares * per share loss capacity
            risk_to_reward_ratio: How much profit you want to have. It is twice of loss_capacity per share for 44 Moving average
            budget : How much you have for investing purpose
            leverage: If day trading, it is mostly 4 or 5 but for long time, there is no leverage given
            Low: Column name which describes LOW of the previous trade
            High =  Column name which describes High of the previous trade
            entry: Manual Entry price price. Might be due to a support or Resistance lebvel or something else
            stop_loss: Manual stop_loss
            delta: A min amount above which you'll buy
            plot_candle: Plot the candlestick for the stock
        '''  
        budget = budget * leverage 

        df = self.open_downloaded_stock(name)
        
        if risk_to_reward_ratio > 2:
            warnings.warn(f"Don't be greedy with risk to reward ratio of {risk_to_reward_ratio}. Stick to system")

        # delta = 0.0008 if df.loc[0,High] >= 1000 else 0.0015
        buy_delta = df.loc[0,High] * delta
        sell_delta = min(df.loc[:1,Low].values) * delta

        if not entry:
            entry = df.loc[0,High] + buy_delta # Last Day MAX + Delta

        if budget < entry:
            warnings.warn(f"Budget for {name} should be a minimum of Rs. {entry}")
            return None

        if not stop_loss:
            stop_loss = min(df.loc[:1,Low].values) - sell_delta
        
        max_loss = entry - stop_loss

        stop_loss_perc = round((max_loss / entry) *100,2)
        diff = entry - stop_loss
        quantity = min(risk // diff , budget // entry)
        profit = risk_to_reward_ratio * diff
        profit_perc = round((profit/entry)*100,2)
        target = round(entry + profit,2)
        investment = entry * quantity
        
        
        if plot_candle:
            AnalyseStocks().plot_candlesticks(df)
        
        if quantity < 1:
            r = round(risk + (diff - risk), 2)
            warnings.warn(f"Risk should be atleast {r} for you to afford {name}")
            return None
            
        return {'Buying Price':round(entry,2),'Stop-Loss %': stop_loss_perc,'Target %':profit_perc,'Quantity':quantity,'Stop-Loss Price':stop_loss,'Trigger Price':target,'investment_required':investment,
                'Risk Per Share':round(diff,2),'Profit Per Share':round(profit,2),'Max loss on this config':round(quantity*diff,2),
                'Max Gain on this config': round(quantity*profit,2), 'Index':self.get_index(name, 'all'),}
    
