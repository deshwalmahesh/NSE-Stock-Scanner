def investing_quantity(self, name, budget:float, risk:float, risk_to_reward_ratio:float=2, leverage:float = 1, entry:float=None, stop_loss:float=None, Low:str = 'LOW', High:str = 'HIGH', delta:float = 0.001, plot_candle:bool = False):
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
        
    return {'Buying Price':round(entry,2),'Stop-Loss %': stop_loss_perc,'Target %':profit_perc,'Quantity':quantity,'Stop-Loss Price':stop_loss,'Trigger Price':target,'investment_required':investment,
            'Risk Per Share':round(diff,2),'Profit Per Share':round(profit,2),'Max loss on this config':round(quantity*diff,2),
            'Max Gain on this config': round(quantity*profit,2), 'Index':self.get_index(name, 'all'),}



def intraday_quantity(self, name, position:str, budget:float, risk:float, entry:float, stop_loss:float, expected_target:float, risk_to_reward_ratio:float=2, leverage:float = 5):
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
