from jugaad_data.nse import stock_df
from nsetools import Nse

from datetime import date, datetime, timedelta

import pandas as pd
import numpy as np

from os import listdir, mkdir
from shutil import rmtree
from os.path import isfile, join, expanduser

import json
import warnings
import math
from random import sample

import requests
import random

from multiprocessing import Pool
from pathlib import Path


current_date = date.today()
drop = ['SERIES','PREV. CLOSE','VWAP','VOLUME','VALUE','NO OF TRADES', 'LTP']


class DataHandler:
    def __init__(self, data_path = './data', check_fresh = False):
        self.present = date.today()
        self.week_num = self.present.strftime("%W")
        
        self.data_path = data_path
        
        self.read_data = DataHandler.read_data # because it is static
        self.data = self.read_data()
        self.all_stocks = self.read_data()['all_stocks']
        
        if check_fresh:
            print('Checking Fresh Data.....')
            self.__fresh()
            self.check_new_data_availability()
        
         
    def __fresh(self,):
        files = listdir(self.data_path)
        if not len(files):
            warnings.warn(f"No CSV data files present at {self.data_path} Downloading new data for analysis")
            self.multiprocess_download_stocks()

        self.data = self.read_data()
        for file in files:
            key, _ , _ = file.split('_')
            self.data['all_stocks'][key] = file
        self.update_data(self.data)
        self.data = self.read_data()
        self.all_stocks = self.read_data()['all_stocks']
  
    
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
        '''
        Update the data in the json file
        args:
            updated_data: Dictonary you want to update
            path: Path of the directory
            File: Json Filename
        '''
        with open(join(path,file), 'w') as f:
            json.dump(updated_data,f)
            return True 

    
    def open_live_stock_data(self,name:str):
        '''
        Open the fresh stock from the market
        args:
            name: ID of the stock given
        '''
        drop = ['SERIES','PREV. CLOSE','VWAP','VOLUME','VALUE','NO OF TRADES', 'LTP']
        return stock_df(symbol=name, from_date = self.present - timedelta(days = 600), to_date = self.present, series="EQ").drop(drop,axis=1)

    
    def open_downloaded_stock(self, name:str):
        '''
        Open the Individual stock based on it's Official Term
        args:
            name: Name / ID given to the stock. Example, Infosys is "INFY"
        returns: DataFrame of that stock
        '''
        df = pd.read_csv(join(self.data_path,self.all_stocks[name]))
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df
    

    def download_new(self,name:str):
        '''
        Download a New Stock Data
        args:
            name: ID / name of the Stock
        '''
        try:
            df = stock_df(symbol=name, from_date = current_date - timedelta(days = 600), to_date = current_date, series="EQ").drop(drop,axis=1)
            df['DATE'] = pd.to_datetime(df['DATE'])
            ID, NAME, _ = self.all_stocks[name].split('_')
            save = f"./data/{ID}_{NAME}_{str(current_date)}.csv"
            df.to_csv(save,index=None)
        except Exception as e:
            print(e)
            pass


    def multiprocess_download_stocks(self,path:str = './data', worker:int=4):
        '''
        Multiprocess Download stocks
        args:
            path: Path where files will be downloaded
            worker: No of workers
        '''
        all_stocks = self.all_stocks
        stocks = set(all_stocks.keys()) - set([i.split('_')[0] for i in listdir('./data')]) 

        pool = Pool(worker)
        results = pool.map(self.download_new,stocks)
        pool.close()
        pool.join()
        return 'Done'


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
        
        if len(set(self.all_stocks.keys()) - set([i.split('_')[0] for i in listdir('./data')])):
            print('Data Count Mismatch. Downloading Missing.....')
            self.multiprocess_download_stocks()



