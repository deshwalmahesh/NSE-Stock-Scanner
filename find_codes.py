from jugaad_data.nse import stock_df
from nsetools import Nse

from datetime import date, datetime, timedelta
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as fplt
import plotly.graph_objects as go

from multiprocessing import Pool

import requests
from bs4 import BeautifulSoup
import random


import requests
from bs4 import BeautifulSoup

url = 'https://www.indian-share-tips.com/2011/11/nse-stock-codes-stock-code-list-india.html'

page = requests.get(url).text
soup = BeautifulSoup(page,'lxml')

soup = soup.find('table',{'class':'tableizer-table'})
table = soup
df = pd.read_html(str(table))[0]
df['Stock NSE Code'] = df['Stock NSE Code'].apply(lambda x: x.strip())
# df.to_csv('./data/code.csv',index=None)
df.head(1)

names = pd.read_csv('./names/names.csv')

codes = pd.read_csv('./names/Equity.csv')
four = dict(zip(codes['Issuer Name'],codes['Security Code']))


nse = Nse()
all_stocks = nse.get_stock_codes()


two = dict(zip(df['Stock NSE Code'],df['Unnamed: 1']))
three = dict(zip(names['SYMBOL'],names['SYMBOL']))

all_stocks.update(two)
all_stocks.update(three)
all_stocks.update(four)

len(all_stocks)
# uni = set(df['Stock NSE Code'].apply(lambda x: x.strip()).values).union(set(pd.read_csv('./data/Equity.csv')['Issuer Name'].apply(lambda x: x.strip()).values))
# uni = uni.union(set(all_stocks.keys()))
# uni = uni.union(set(names['SYMBOL']))



mypath = './data'
from os import listdir
from os.path import isfile, join
onlyfiles = [f.split('_')[0] for f in listdir(mypath) if isfile(join(mypath, f))]
onlyfiles

x = all_stocks.copy()
all_stocks = {}
for key in x.keys():
    if key not in onlyfiles:
        all_stocks[key] = x[key]

len(all_stocks)