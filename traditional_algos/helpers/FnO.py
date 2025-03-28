from dateutil.relativedelta import relativedelta, TH
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .nse_data import NSEData
from .plotting import Plots

NSE = NSEData()
PLT = Plots()


def get_next_expiry_date(expiry_type:str = 'monthly'):
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


def analyse_option_chain(symbol, compare_with:tuple = ('openInterest','changeinOpenInterest','totalTradedVolume','change'), expiry_dates:tuple = None, top_n:int = 10, expiry_type:str = 'monthly', plot:bool = True, fig_size = (25,10)):
    '''
    Get the Option Chain's Open Interest for analysis. You can read more about it at: https://www.quora.com/How-do-I-read-analyse-the-option-chain-of-a-stock-to-intraday-trade-with-clarity-NSE
    args:
        symbol: NSE Symbol or any Index from the three ['NIFTY','BANKNIFTY','FINNIFTY']
        compare_with: Comapre the Puts Aginst this value. Select From ['openInterest', 'changeinOpenInterest', 'pchangeinOpenInterest','totalTradedVolume', 'totalBuyQuantity', 'totalSellQuantity']
        expiry_dates: List of Expiry dates: In ORDER with format such as: '29-Nov-2021'. Run FnO.get_next_expiry_date() to get a list of next expiry dates. If None, Nearest Date is used
        top_n: How many top values, EACH of Calls and Put to return
        expiry_type: Monthly (for equity and indoces both) or Weekly (for indices only) if in case there is no expiry_dates set
        plot: Whether to plot the figure or not
        fig_sizee: Size of figure per subplot. Set according to the values you want to plot
    ''' 
    if symbol in ['NIFTY','BANKNIFTY','FINNIFTY']:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f'https://www.nseindia.com/api/option-chain-equities?symbol={symbol}'
    
    df_data = {'contract_type':[],'expiryDate': [],'strikePrice':[],'openInterest': [],'changeinOpenInterest': [],'pchangeinOpenInterest': [],'totalTradedVolume': [], 
               'totalBuyQuantity': [], 'totalSellQuantity': [], 'change':[]}
    keys = df_data.keys()
    
    r = NSE.get_live_nse_data(url).json()
    data = r['records']['data']

    for entry in data:
        if entry.get('CE'):
            [df_data[name].append(entry['CE'][name]) if name!='contract_type' else df_data['contract_type'].append('Calls_CE') for name in keys]

        if entry.get('PE'):
            [df_data[name].append(entry['PE'][name]) if name!='contract_type' else df_data['contract_type'].append('Puts_PE') for name in keys]
           

    df = pd.DataFrame(df_data)
    df.rename(columns = {'expiryDate':'expiry_date', 'strikePrice':'strike_price'},inplace = True)
    df['expiry_date'] = df['expiry_date'].apply(lambda x:datetime.strptime(x, "%d-%b-%Y").strftime("%d-%b-%Y"))
    df['strike_price'] = df['strike_price'].apply(lambda x: int(x))
    df['absChangeOI'] = df['changeinOpenInterest'].apply(lambda x: abs(x))
    df['absChange'] = df['change'].apply(lambda x: abs(x))
    
    # Get specific expiry date
    if not expiry_dates:
        recent_expiry = get_next_expiry_date()[0]
        sup_plot_text_date = recent_expiry
        expiry_dates = [recent_expiry] # Single element tuple requires ,
    else:
        recent_expiry = expiry_dates[0]
        sup_plot_text_date = 'All Available Expiries'
        expiry_dates = [datetime.strptime(x, "%d-%b-%Y").strftime("%d-%b-%Y") for x in expiry_dates]   
    df = df[df['expiry_date'].isin(expiry_dates)]
    
    if plot:
        PLT.plot_Option_chain(symbol, df, compare_with, top_n, sup_plot_text_date, fig_size=fig_size)

    return df