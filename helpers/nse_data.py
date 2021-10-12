from os import X_OK
from .investing import Investing, pd, current_date
import requests
from datetime import date

In = Investing()


class NSEData:
    '''
    Class to open NSE data
    '''
    def __init__(self):
        '''
        '''
        self.baseurl = "https://www.nseindia.com/"
        self.requests = requests

        self.headers = {"user-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36", "accept-encoding": "gzip, deflate, br",
              "accept-language": "en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7",
              "sec-ch-ua-platform": "Linux", "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"'}
        

        self.session = self.requests.Session()
        self.request = self.session.get(self.baseurl, headers=self.headers, timeout=5)
        self.cookies = dict(self.request.cookies)

        self.to = current_date.strftime("%d-%m-%Y") # For getting historical data
        self.from_ = current_date.replace(year = current_date.year-2).strftime("%d-%m-%Y") # for getting historical data
        
    
    def get_live_nse_data(self, url:str):
        '''
        Get Live market data available on NSE website as PDF
        args:
           url: corresponding url
        '''
        response = self.session.get(url, headers=self.headers, timeout=1, cookies=self.cookies)
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
        
        df = pd.DataFrame(self.get_live_nse_data(url).json()['data'])
        df['absolute_change'] = df['pChange'].apply(lambda x: abs(x))
        df['Index'] = df['symbol'].apply(lambda x: In.get_index(x))
        df.sort_values('absolute_change',ascending=False, inplace=True)
        return df.iloc[:show_n,[1,9,3,4,5,6,-1]]


    def get_2_years_data(self, symbol:str):
        '''
        Get Historical Data for each equity for the past 24 months
        args:
            symbol: Listed name of the stock on NSE
        '''
        url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={self.from_}&to={self.to}"
        result = self.get_live_nse_data(url = url)
        return pd.DataFrame(result.json()['data'])