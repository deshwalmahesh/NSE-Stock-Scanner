import warnings
import requests
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


class KiteZerodha():
    '''
    Class to connect with Kite platform using your credentials
    All thanks to: https://marketsetup.in/posts/zerodha-login/
    '''
    def __init__(self, secret_file_path:None = None, user_id:str = None, password:str = None, two_factor_pin:str = None, data_path = './data.json'):
        '''
        args:
            secret_file_path: PAth to the file which has your user_id, password and 2 factor Authentication code
            user_id: User id
            password: Password
            two_factor_pin: Two factor pin you have
            data_path: Path of Json file where all the data is stored
        '''
        assert not (not user_id) or (secret_file_path), "Either enter user_id and other fields OR enter the file path where those credentials are stored"

        if secret_file_path:
            with open(secret_file_path) as f:
                kite_creds = json.load(f)

            self.user_id = kite_creds['user_id'].upper()
            self.password = kite_creds['password']
            self.two_factor_pin = kite_creds['two_factor_pin']
        
        else:
            self.user_id = user_id.upper()
            self.password = password
            self.two_factor_pin = str(two_factor_pin)

        with open(data_path) as f:
            self.data = json.load(f)

        
        self.data_day_limit = {60:400, 30:200, 15:200, 5:100, 3:100, 4:100, 2:60}

        self.name_code_mapping = {'HAVELLS':2513665,"MCDOWELL-N":2674433,"HINDPETRO":359937,"BHARTIARTL":2714625,"RBLBANK":4708097,"JINDALSTEL":1723649,"GRASIM":315393,"RAMCOCEM":523009}

        self.kite_basic_urls = {"base_url":"https://kite.zerodha.com/",'login_url' : "https://kite.zerodha.com/api/login","two_factor_url":"https://kite.zerodha.com/api/twofa",
            "positions":"https://kite.zerodha.com/oms/portfolio/positions","holdings":'https://kite.zerodha.com/oms/portfolio/holdings',"margins":"https://kite.zerodha.com/oms/user/margins",
            "marketwatch":"https://kite.zerodha.com/api/marketwatch","orders":"https://kite.zerodha.com/oms/orders","marketoverview":"https://kite.zerodha.com/api/market-overview",
            "profile":"https://kite.zerodha.com/oms/user/profile/full"}

        self.session = requests.Session()
        self._login()

        
    def _login(self):
        '''
        Login to your account
        return: A Session object
        '''
        login_url = self.kite_basic_urls['login_url']
        two_factor_url = self.kite_basic_urls["two_factor_url"]
        
        response = self.session.post(login_url, data = {"user_id":self.user_id , "password":self.password})
        response = self.session.post(two_factor_url, data = {"user_id": self.user_id, "request_id": response.json()['data']["request_id"], "twofa_value": self.two_factor_pin})

        if response.status_code == 200:
            print("Logged in Successfully")
        else:
            assert False, "Some problem in your login. Check Credentials or file"
        
        enc_token = self.session.cookies['enctoken']
        
        headers = {}
        headers['authorization'] = "enctoken {}".format(enc_token)
        self.session.headers.update(headers)


    def check_basic_info(self, kind:str):
        '''
        Check the basic things like holdings, positions etc
        args:
            kind: What do you want to get and check
        return:
            A dictonary with the information required object with 
        '''
        keys = list(self.kite_basic_urls.keys())[3:]
        if kind not in self.kite_basic_urls.keys():
            assert False, f"Enter values from one of {keys}"
        
        response = self.session.get(self.kite_basic_urls[kind])
        return response.json()

    
    def get_historical_minutes_data(self, name:str, code:int = None, interval:int = 5, starting_from_date:str = None, no_days_back:int = 7, get_latest_only:bool = False):
        '''
        Get minute by minute historical data
        args:
            name: Name of the stock. According to NSE Website and the data we have
            code: Code for the stock
            interval: Which interval data in minutes you want to get
            no_days_back: Data to gather for Number of days in past starting from the "from_date"
            starting_from_date: Enter the date from which you want to have the data to be gether in the format "01/01/2022". If None, current day will be taken as starting day
            get_latest_only: Whether to get the current Day's data only
        '''
        no_days_back = 0 if get_latest_only else no_days_back

        assert interval in [2,3,4,5,10,15,30,60], "Please input interval data within minutes from one of the: [2,3,4,5,10,15,30, 60]"
        assert name in self.data['all_stocks'], "Enter a valid stock name. Check NSE website for code"
        assert name in self.name_code_mapping, "Name and it's code has not been updated. Help me help you update all 1600 names and code. Please find the code and Update the file or raise an issue / feature request for specific stock"
        
        limit = self.data_day_limit[interval]
        assert no_days_back <= limit, f"Can not get past {no_days_back} days data when interval is {interval}. Max allowed days are {limit} from 'starting_from_date'. Either increase interval or decrease no_days_back"
    
        code = self.name_code_mapping[name] if not code else code
        today = datetime.today()
        if not starting_from_date:
            from_date = today
        else:
            from_date = datetime.strptime(starting_from_date, '%d/%m/%Y')
        
    
        to_date = from_date - timedelta(days = no_days_back)
        to_date = to_date.strftime("%Y-%m-%d")
        from_date = from_date.strftime("%Y-%m-%d")

        url = f"https://kite.zerodha.com/oms/instruments/historical/{code}/{interval}minute?user_id={self.user_id}&oi=1&from={to_date}&to={from_date}"
        
        try:
            data = self.session.get(url).json()['data']['candles']
            df = pd.DataFrame(data)
            df.rename(columns = {0:"DATE",1:"OPEN",2:"HIGH",3:"LOW",4:"CLOSE",5:"VOLUME",6:'UNKNOWN'},inplace = True)
            df["DATE"] = pd.to_datetime(df["DATE"])
            df['52W H'] = np.nan
            df['52W L'] = np.nan
            df['SYMBOL'] = name
            return df.loc[:,["DATE","OPEN","HIGH","LOW","CLOSE","52W H","52W L","SYMBOL"]].sort_index(ascending = False).reset_index(drop = True)

        except Exception as e:
            print('Error in fetching Data. Check proper parameters:\n',e)


    def download_intraday_data(self, name:str, interval:int, path:str = './intraday_data', overwrite:bool = False):
        '''
        Download Minutes Data starting from NOW to the last available date to which the specific candle can be downloaded.
        No functionality is given for MultiProcessing due to the fact that Zerodha might block access when huge no of requests are fired
        args:
            name: Name of the stock
            path: Path of the directory where you want to download the data
            interval: Which interval data in minutes you want to get
            overwrite: Whether to download from scratch or append to the existing data
        '''
        full_path = f'{path}/minutes_{str(interval)}/{name}.csv'

        no_days_back = self.data_day_limit[interval] -1 
        df = self.get_historical_minutes_data(name, interval, None, no_days_back)
        df.to_csv(full_path, index = None)



        

   
