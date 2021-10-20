import pandas as pd
import requests
from datetime import date
from bs4 import BeautifulSoup
import json

current_date = date.today()

class NSEData:
    '''
    Class to open NSE data
    '''
    def __init__(self):
        '''
        '''
        self.baseurl = "https://www.nseindia.com/"

        self.headers = {"user-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36", "accept-encoding": "gzip, deflate, br",
              "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7",
              "sec-ch-ua-platform": "Linux", "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"'}

        self.session = requests.Session()
        request = self.session.get(self.baseurl, headers=self.headers)
        self.cookies = dict(request.cookies)
        

        self.to = current_date.strftime("%d-%m-%Y") # For getting historical data
        self.from_ = current_date.replace(year = current_date.year-2).strftime("%d-%m-%Y") # for getting historical data
        
    
    def get_live_nse_data(self, url:str):
        '''
        Get Live market data available on NSE website as PDF
        args:
           url: corresponding url
        '''
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)
        return response
    

    def current_indices_status(self,show_n:int=5):
        '''
        Get current status of all the available indices. It could be pre, dyring or post market. Will tell how much each index or sector moved as other details
        args:
            show_n: Show top N sorted by ABSOLUTE % change Values such that -3.2 will be shown first than 2.3
        '''
        df = pd.DataFrame(self.get_live_nse_data("https://www.nseindia.com/api/allIndices").json()['data'])
        df['absolute_change'] = df['percentChange'].apply(lambda x: abs(x))
        df.sort_values('absolute_change',ascending=False, inplace=True)
        return df.iloc[:show_n,[1,5,0,4]]
    
    
    def open_nse_index(self,index_name:str,show_n:int=10):
        '''
        Open the current index. DataFrame with all the members of the index and theit respective Open, High, Low, Percentange chnge etc etc
        args:
            index_name: Name of the Index such as NIFTY 50, NIFTY Bank, NIFTY-IT etc
            show_n: Show top N sorted by ABSOLUTE % change Values such that -3.2 will be shown first than 2.3
        '''
        index_name = index_name.replace(' ','%20')
        index_name = index_name.replace(':','%3A')
        index_name = index_name.replace('/','%2F')
        index_name = index_name.replace('&','%26')

        url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name}"

        resp = self.get_live_nse_data(url)
        
        df = pd.DataFrame(resp.json()['data'])
        df['absolute_change'] = df['pChange'].apply(lambda x: abs(x))
        # df['Index'] = df['symbol'].apply(lambda x: In.get_index(x))
        df.sort_values('absolute_change',ascending=False, inplace=True)
        df.drop(0,inplace = True) # Drop the index name
        return df.iloc[:show_n,[1,9,3,4,5,6,-1]]


    def fifty_days_data(self, symbol:str):
        '''
        Get Historical Data for each equity for the past 50 trading days
        args:
            symbol: Listed name of the stock on NSE
        '''
        url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={self.from_}&to={self.to}"
        result = self.get_live_nse_data(url = url)
        df = pd.DataFrame(result.json()['data'])
        df.columns = df.columns.map({'CH_SYMBOL':'SYMBOL',"CH_TRADE_HIGH_PRICE":"HIGH","CH_TRADE_LOW_PRICE":"LOW","CH_OPENING_PRICE":"OPEN","CH_CLOSING_PRICE":"CLOSE",
                "CH_TIMESTAMP":"DATE","CH_52WEEK_LOW_PRICE":"52W L","CH_52WEEK_HIGH_PRICE":"52W H"})

        df = df.loc[:,["DATE","OPEN","HIGH","LOW","CLOSE","52W H","52W L","SYMBOL"]] # to match previous API's Columns and structure
        return df
    
    
def get_mmi(raw = False):
    '''
    All credits to https://www.tickertape.in/market-mood-index. Please refer to the link
    args:
        raw: Whether to return the raw json of data for MMI
    '''
    url = "https://www.tickertape.in/market-mood-index"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "lxml")


    script = soup.find_all('script' ,{"id":"__NEXT_DATA__"})[0]
    values = json.loads(script.string)['props']['pageProps']['nowData']
    current = values['currentValue']
    last_day = values['lastDay']['indicator']
    last_week = values['lastWeek']['indicator']
    last_month = values['lastMonth']['indicator']
    
    if raw:
        return values
    
    if current < 30:
        print('Boom!!! You might want to Buy for Investment purpose. Market is in Extreme Fear')
        
    elif 30 < current < 50:
        print('Market is in Fear Zone. You might want it to go to Extreme Fear to start buying')
        
    elif 50 < current < 80:
        print('Market is in Greed zone! You might want to book profits. Keep yourself from taking new positions')
    
    elif current > 80:
        print("WARNING!!! You might want to book profits. Do not take fresh positions for Investment purpose now. Market is Extremely Greedy")