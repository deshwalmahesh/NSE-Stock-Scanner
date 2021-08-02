from jugaad_data.nse import stock_df
from nsetools import Nse

from datetime import date, datetime, timedelta

import pandas as pd
import numpy as np

from os import listdir
from os.path import isfile, join

import json
import warnings
import math
from random import sample

import requests
from bs4 import BeautifulSoup
import random



class DataHandler:
    def __init__(self, data_path = '../data', check_fresh = True):
        self.present = date.today()
        self.week_num = self.present.strftime("%W")
        
        self.data_path = data_path
        
        if check_fresh:
            self.__fresh()
        self.data = self.read_data()
        self.all_stocks = self.read_data()['all_stocks']
        
         
    def __fresh(self,):
        files = listdir(self.data_path)
        if not len(files):
            raise Exception(f"No CSV data files present at {self.data_path} Download new data for analysis")

        self.data = self.read_data()
        for file in files:
            key, _ , _ = file.split('_')
            self.data['all_stocks'][key] = file
        self.update_data(self.data)
  
    
    def read_data(self, path = '../', file = 'data.json'):
        '''
        Write the data in json file
        args:
            path: Path of the directory
            File: Json Filename
        '''
        with open(join(path,file)) as f:
            return json.load(f)


    def update_data(self, updated_data:dict, path:str = '../', file:str = 'data.json'):
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
        drop = ['SERIES','PREV. CLOSE','VWAP','VOLUME','VALUE','NO OF TRADES']
        return stock_df(symbol=name, from_date = self.present - timedelta(days = 600), to_date = self.present, series="EQ").drop(drop,axis=1)
    
    
    def open_downloaded_stock(self,name:str):
        '''
        Open the Individual stock based on it's Official Term
        args:
            name: Name / ID given to the stock. Example, Infosys is "INFY"
        returns: DataFrame of that stock
        '''
        return pd.read_csv(join(self.data_path,self.all_stocks[name]))