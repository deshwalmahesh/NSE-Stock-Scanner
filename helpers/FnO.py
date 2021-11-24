from dateutil.relativedelta import relativedelta, TH
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .nse_data import NSEData

NSE = NSEData()


def get_next_expiry_date(expiry_type:str = 'weekly'):
    '''
    Get Future and Options Expiry Contracts Date for the next 3 months from TODAY. 
    For Equity, it is on last Trursday of Month and for Nifty-BankNifty it is for Last Thursday of the Week UNTILL or UNLESS it is a Holiday
    args:
        expiry_type: Insert from [monthly, equity, weekly, nifty]
    '''
    today = datetime.today()
    expiry_dates = []

    if expiry_type in ('weekly', 'nifty'):
        for i in range(1,13):
            expiry_dates.append((today + relativedelta(weekday=TH(i))).date().strftime("%d-%b-%Y"))

    elif expiry_type in ('monthly', 'equity'):
        for i in range(1,13):
            x = (today + relativedelta(weekday=TH(i))).date()
            y = (today + relativedelta(weekday=TH(i+1))).date()
            if x.month != y.month :
                if x.day > y.day :
                    expiry_dates.append(x.strftime("%d-%b-%Y"))

    return expiry_dates


def analyse_open_interest(symbol, compare_with:str = 'openInterest', expiry_dates:tuple = None, top_n:int = 5, return_top_only:bool = True, plot_comparison:bool = True):
    '''
    Get the Option Chain's Open Interest for analysis. You can read more about it at: https://www.quora.com/How-do-I-read-analyse-the-option-chain-of-a-stock-to-intraday-trade-with-clarity-NSE
    args:
        symbol: NSE Symbol or any Index from the three ['NIFTY','BANKNIFTY','FINNIFTY']
        compare_with: Comapre the Puts Aginst this value. Select From ['openInterest', 'changeinOpenInterest', 'pchangeinOpenInterest','totalTradedVolume', 'totalBuyQuantity', 'totalSellQuantity']
        expiry_dates: List of Expiry dates: in format such as: '29-Nov-2021'. Run FnO.get_next_expiry_date() to get a list of next expiry dates. If None, Nearest Date is used
        top_n: How many top values, EACH of Calls and Put to return
        return_top_only: Whether to return all the current contracts or just the top-n from each CE and PE
        plot_comparison: Plot comparisons of PE and CE using a bar plot
    '''
    if symbol in ['NIFTY','BANKNIFTY','FINNIFTY']:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f'https://www.nseindia.com/api/option-chain-equities?symbol={symbol}'
        
    r = NSE.get_live_nse_data(url).json()
    data = r['records']['data']

    OI = []
    contract_type = []
    strike_price = []
    expiry = []

    for entry in data:
        if entry.get('CE'):
            OI.append(entry['CE'][compare_with])
            expiry.append(entry['CE']['expiryDate'])
            strike_price.append(entry['strikePrice'])
            contract_type.append('Calls_CE')

        if entry.get('PE'):
            OI.append(entry['PE'][compare_with])
            expiry.append(entry['PE']['expiryDate'])
            strike_price.append(entry['strikePrice'])
            contract_type.append('Puts_PE')  


    df = pd.DataFrame({'strike_price':strike_price, compare_with:OI, 'contract_type':contract_type,'expiry_date':expiry,})
    df['expiry_date'] = df['expiry_date'].apply(lambda x:datetime.strptime(x, "%d-%b-%Y").strftime("%d-%b-%Y"))
    df['strike_price'] = df['strike_price'].apply(lambda x: int(x))
 
    if not expiry_dates:
        expiry_dates = (df['expiry_date'].min(),) # Single element tuple requires ,
    else:
        expiry_dates = [datetime.strptime(x, "%d-%b-%Y").strftime("%d-%b-%Y") for x in expiry_dates]
        
    df = df[df['expiry_date'].isin(expiry_dates)]
    topn_df = pd.concat([df[df['contract_type'] == 'Calls_CE'].nlargest(top_n,compare_with),df[df['contract_type'] == 'Puts_PE'].nlargest(top_n,compare_with)])
    
    if plot_comparison:
        fig = plt.figure(figsize = (12,7))
        plt.title(f"{symbol} Strike Price vs Put/Call vs {compare_with}",pad = 13, fontweight = 'heavy')
        
        fig = sns.barplot(x="strike_price", y=compare_with, hue="contract_type", data = topn_df, palette = {'Calls_CE': 'tab:green','Puts_PE': 'tab:red'}, ci = None)
        
        for c in fig.containers:
            fig.bar_label(c, fmt='%.0f', label_type='edge', padding=5)
            fig.margins(y=0.3)
            
        fig.set_ylabel(compare_with, labelpad = 10, fontsize = 13)
        fig.set_xlabel('Strike Price (in Rupees)', labelpad = 10, fontsize = 13)
        
           
    if return_top_only:
        return topn_df
    
    return df