from jugaad_data.nse import stock_df
from .nse_data import NSEData

from datetime import date, datetime, timedelta

import pandas as pd
import numpy as np

from os import listdir, mkdir, cpu_count
from shutil import rmtree
from os.path import join, expanduser

import json
import warnings

import random

from multiprocessing import Pool

NSE = NSEData()
workers = int(0.8*cpu_count())


drop = ['SERIES','PREV. CLOSE','VWAP','VOLUME','VALUE','NO OF TRADES', 'LTP']


class DataHandler:
    def __init__(self, data_path = './data', check_fresh = False):
        '''
        '''
        self.present = date.today()
        self.week_num = self.present.strftime("%W")
        
        self.data_path = data_path
        
        self.read_data = DataHandler.read_data # because it is static
        self.data = self.read_data()
        self.all_stocks = self.data['all_stocks']
        
        if check_fresh:
            print('Checking Fresh Data.....')
            self.__fresh()
            self.check_new_data_availability()

    
    def update_FnO(self):
        '''
        Update the newest Futures and Options Derivatives list
        '''
        r = NSE.get_live_nse_data('https://www1.nseindia.com/content/fo/fo_underlyinglist.htm')
        df = pd.read_html(r.text)[3].iloc[5:]
        self.data['f&o'] = df.iloc[:,1].values.tolist()
        self.update_data(self.data)
             

    def update_new_listings(self):
        '''
        Update new IPO or stocks as they are listed on the NSE and remove the ones which have been removed from the listings
        '''
        print('\nUpdating New Listings.....')
        old = set(self.data['registered_stocks'])
        df = pd.read_csv("https://archives.nseindia.com/content/equities/EQUITY_L.csv")
        df = df[df[' SERIES'] == 'EQ']
        new = set(df['SYMBOL'].values.tolist())

        to_update = old.union(new) - old.intersection(new)
        df = df[df['SYMBOL'].isin(to_update)]

        for index in df.index:
            try:
                self.open_live_stock_data(df.loc[index,"SYMBOL"])
                self.data['registered_stocks'].append(df.loc[index,"SYMBOL"])
                self.data['all_stocks'][df.loc[index,"SYMBOL"]] = f'{df.loc[index,"SYMBOL"]}_{df.loc[index,"NAME OF COMPANY"]}_{str(self.present)}.csv'
            except Exception as e:
                print("Error: ",df.loc[index,"SYMBOL"])
                pass

        self.update_data(self.data)

        print('\nUpdate Successful. Downloading New Files')
        rmtree(self.data_path) # Delete Data Folder so that new things can be downloaded
        mkdir(self.data_path)

        self.multiprocess_download_stocks()

    
    def update_fresh_nifty_indices(self):
        '''
        Update all the new Nifty Indices as they might have changed or altered. Good to call it once in a while
        '''
        print('Updating New Nifty, Sectoral and thematic Indices')
        success = True
        try:
            for index_name in ['Sectoral Indices','Thematic Indices']: # Update Sectoral first
                index_key = index_name.replace(' ','_').lower() # setoral_indices, thematic_indices
                self.data[index_key] = {} # Will contain names of individual sectors

                branches = self.data['all_indices_names'][index_name] # Get all the available sectors and themes
                for branch_name in branches: # get individial names: Such as Nifty IT, Nifty Auto etc
                    names = NSE.open_nse_index(branch_name, show_n=9999)['symbol'].tolist()
                    self.data[index_key][branch_name] = names

            nifties = {'nifty_50':'NIFTY 50', 'nifty_100': 'NIFTY 100', 'nifty_200':'NIFTY 200', 'nifty_500':'NIFTY500 MULTICAP 50:25:25'}
            for index_name in nifties.keys():
                valid_names = [] # Names which are in Nifty Index but not in registered

                names = NSE.open_nse_index(nifties[index_name], show_n=500)['symbol'].tolist()
                for name in names:
                    if name in self.data['registered_stocks']:
                        valid_names.append(name)
                self.data[index_name] = valid_names

        except Exception as e:
            success = False
            warnings.warn(f"ERROR Occured: {e}\nTry again later")
            
        if success:
            print('Successful!')
            self.update_data(self.data)
        

    def __fresh(self,):
        files = listdir(self.data_path)
        if not len(files):
            warnings.warn(f"No CSV data files present at {self.data_path} Downloading new data for analysis")
            self.multiprocess_download_stocks()
            
            self.update_fresh_files()
  
    
    @staticmethod
    def read_data(path = './', file = 'data.json'):
        '''
        Write the data in json file
        args:
            path: Path of the directory
            File: Json Filename
        '''
        with open(join(path,file)) as f:
            return json.load(f)


    def update_data(self, updated_data:dict, path:str = './', file:str = 'data.json'):
        '''the balkan line
        Update the data in the json file
        args:
            updated_data: Dictonary you want to update
            path: Path of the directory
            File: Json Filename
        '''
        with open(join(path,file), 'w') as f:
            json.dump(updated_data,f)

    
    def open_live_stock_data(self,name:str,):
        '''
        Open the fresh stock from the market
        args:
            name: ID of the stock given
        '''
        return stock_df(symbol=name, from_date = self.present - timedelta(days = 750), to_date = self.present, series="EQ").drop(drop,axis=1) # almost 2 years
    
    
    def open_downloaded_stock(self, name:str, resample:str = None, kind = 'daily'):
        '''
        Open the Individual stock based on it's Official Term
        args:
            name: Name / ID given to the stock. Example, Infosys is "INFY"
            resample: Resample the data to Weekly, Monthly, Yearly. Pass in ['M','W','Y']. Default: None means Daily
            kind: Kind of data file to open" could be "daily" or any of [minutes_2, minutes_3, minutes_4, minutes_5, minutes_15, minutes_30, minutes_60]
        returns: DataFrame of that stock
        '''
        if kind == 'daily':
            df = pd.read_csv(join(self.data_path,self.all_stocks[name]))
            df['DATE'] = pd.to_datetime(df['DATE'])

            if resample:
                df = self.resample_data(df,resample)
            return df
        
        else:
            file = f'./intraday_data/{kind}/{self.all_stocks[name]}'
            try:
                df = pd.read_csv(file)
                df['DATE'] = pd.to_datetime(df['DATE'])
                return df
            except:
                print(f"Unable to Open {file}. Check if there's a file in the corresponding directory")

    
    def resample_data(self, data, to:str  = 'W', names:tuple = ('OPEN','CLOSE','LOW','HIGH','DATE')):
        '''
        Resample the data from Daily to Weekly, Monthly or Yearly
        args:
            data: Dataframe of Daily data
            to: One of  ['W','M','Y']
        '''
        Open, Close, Low, High, Date = names
        data = data.resample(to,on=Date).agg({Open:'first', High:'max', Low: 'min', Close:'last'})
        return data.sort_index(ascending = False).reset_index()
    

    def download_new(self,name:str, path:str = "./data"):
        '''
        Download a New Stock Data
        args:
            name: ID / name of the Stock
            path: Path to the directory where downloaded files have to be stored
         '''
        try:
            df = self.open_live_stock_data(name)
            df['DATE'] = pd.to_datetime(df['DATE'])
            ID, NAME, _ = self.all_stocks[name].split('_')
            save = f"{path}/{ID}_{NAME}_{str(self.present)}.csv"
            df.to_csv(save,index=None)
        except Exception as e:
            print(name,'----',e)


    def multiprocess_download_stocks(self,path:str = './data'):
        '''
        Multiprocess Download stocks
        args:
            path: Path where files will be downloaded
            worker: No of workers
        '''
        stocks = self.data['registered_stocks']

        pool = Pool(workers)
        results = pool.map(self.download_new,stocks)
        pool.close()
        pool.join()
        return True


    def check_new_data_availability(self):
        '''
        Check and download new available or unfinished data
        '''
        name = random.choice(self.data['nifty_50'])
        old = self.open_downloaded_stock(name)
        new = self.open_live_stock_data(name)
        if old.iloc[0,0] < new.iloc[0,0]:
            print('New Data Available. Downloading now....')
            
            rmtree(self.data_path)
            mkdir(self.data_path)
            self.multiprocess_download_stocks()
        
        missing_list = set(self.all_stocks.keys()) - set([i.split('_')[0] for i in listdir('./data')])
        if len(missing_list):
            print('Data Count Mismatch. Downloading Missing.....',missing_list)
            self.multiprocess_download_stocks()
        
        self.update_fresh_files()
        

    def update_fresh_files(self):
        '''
        Update Downloaded Files in the data.json
        '''
        files = listdir(self.data_path)
        self.data = self.read_data()

        for file in files:
            key, name , _ = file.split('_')
            self.data['all_stocks'][key] = file

        self.update_data(self.data)

    




