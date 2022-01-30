import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import matplotlib.pyplot as plt
from random import sample
import json

pio.renderers.default = 'colab' 


class Plots():
    def __init__(self, json_file:str = './data.json'):
        '''
        args:
            path: Path where all the stock files are saved
        '''
        with open(json_file) as f:
            self.data = json.load(f)

        self.colors = self.data['colors']
        self.all_stocks = self.data['all_stocks']
        self.indices = {'nifty_50': 'Nifty 50','nifty_100':'Nifty 100','nifty_200':'Nifty 200','nifty_500':'Nifty 500'}

                     
    def plot_candlesticks(self,df, names = ('DATE','OPEN','CLOSE','LOW','HIGH'), mv:list = [200], slider:bool = False, fig_size:bool = (1400,700)):
        '''
        Plot a candlestick on a given dataframe
        args:
            df: DataFrame
            names: Tuple of column names showing ('DATE','OPEN','CLOSE','LOW','HIGH')
            mv: Moving Averages
            slider: Whether to have below zoom slider or not
            fig_size: Size of Figure as (Width, Height)
        '''
        delta = df.iloc[0,0] - df.iloc[1,0]
        kind = 'day' if delta.days > 0 else 'intra'
        freq = int(delta.seconds / 60) if kind == 'intra' else None
        
        stocks = df.copy()
        stocks.sort_index(ascending=False, inplace = True)  # Without reverse, recent rolling mean will be either NaN or equal to the exact value

        Date, Open, Close, Low, High = names

        mv = [] if not mv else mv # just in case you don't want to have any moving averages
        colors = sample(self.colors,len(mv))

        # To remove gaps in candles due to Non- Trading days
        if kind == 'day':
            dt_all = pd.date_range(start=stocks.iloc[0,0],end=stocks.iloc[-1,0])
            dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(stocks.DATE)]
            dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]

            rangebreaks=[dict(values=dt_breaks)]
            
            range_selector = dict(buttons = list([
                    dict(count = 1, label = '1M', step = 'month', stepmode = 'backward'),
                    dict(count = 6, label = '6M', step = 'month', stepmode = 'backward'),
                    dict(count = 1, label = '1Y', step = 'year', stepmode = 'backward'),
                    dict(step = 'all')]))

        else:
            # grab first and last observations from df.date and make a continuous date range from that
            dt_all = pd.date_range(start=stocks['DATE'].iloc[0],end=stocks['DATE'].iloc[-1], freq = f'{str(freq)}min')
            # check which dates from your source that also accur in the continuous date range
            dt_obs = [d.strftime("%Y-%m-%d %H:%M:%S") for d in stocks['DATE']]
            # isolate missing timestamps
            dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in dt_obs]

            rangebreaks=[dict(dvalue = freq*60*1000, values=dt_breaks)]
            
            range_selector = dict(buttons = list([
                    dict(count = 5, label = '5Min', step = 'minute', stepmode = 'backward'),
                    dict(count = 15, label = '15Min', step = 'minute', stepmode = 'backward'),
                    dict(count = 1, label = '1D', step = 'day', stepmode = 'backward'),
                    dict(step = 'all')]))

        
        candle = go.Figure(data = [go.Candlestick(opacity = 0.9, x = stocks[Date], name = 'X',
                                                  open = stocks[Open], high = stocks[High], low = stocks[Low], close = stocks[Close]),])
        
        for i in range(len(mv)):
            stocks[f'{str(mv[i])}-SMA'] = stocks[Close].rolling(mv[i], min_periods = 1).mean()
            candle.add_trace(go.Scatter(name=f'{str(mv[i])} MA',x=stocks[Date], y=stocks[f'{str(mv[i])}-SMA'], 
                                             line=dict(color=colors[i], width=1.1)))

            
        candle.update_xaxes(title_text = 'Date', rangeslider_visible = slider, rangeselector = range_selector, rangebreaks=rangebreaks)


        candle.update_layout(autosize = False, width = fig_size[0], height = fig_size[1],
                             title = {'text': f"{stocks['SYMBOL'][0]} | {self.all_stocks[stocks['SYMBOL'][0]].split('_')[1]}",'y':0.97,'x':0.5,
                                      'xanchor': 'center','yanchor': 'top'},
                             margin=dict(l=30,r=30,b=30,t=30,pad=2),
                             paper_bgcolor="lightsteelblue")

        candle.update_yaxes(title_text = 'Price in Rupees', tickprefix = u"\u20B9" ) # Rupee symbol
        candle.show()


    def plot_pivot(self, name:str, piv_data, plot_size:tuple = (25,7)):
        '''
        Plot Pivot points with Pivot, Upper Bound, Lower Bound, Support-1, Resistance-1
        args:
            name: Name of the stock
            pivot_data: Pivot data of the stock of the stock. If not given, it'll open the stock from downloaded and run 'get_Pivot_Points()` fun
            num_days_back: Number of days data you want to visualise
            chart_size: Size of the chart as (width, height)
        '''
        dates = list(piv_data.keys())[::-1]
        dates.append("Day END")
        piv_data["Day END"] = None
        total = len(dates)

        fig, ax = plt.subplots(figsize = plot_size)
        plt.title(f'Pivot Plot for {name}',weight='bold',fontsize=15)

        for i,key in enumerate(dates):
            data = piv_data[key]

            if i < total-1:
                ax.hlines(y=data['UB'], xmin=dates[i], xmax=dates[i+1], linewidth=1.5, color='red', linestyles = 'dotted')
                ax.hlines(y=data['Pivot'], xmin=dates[i], xmax=dates[i+1], linewidth=2, color='black',)
                ax.hlines(y=data['LB'], xmin=dates[i], xmax=dates[i+1], linewidth=1.5, color='green', linestyles = 'dotted',)

                ax.hlines(y=data['S-1'], xmin=dates[i], xmax=dates[i+1], linewidth=2, color='green')
                ax.hlines(y=data['R-1'], xmin=dates[i], xmax=dates[i+1], linewidth=2, color='red',)
                
                ax.axvline(x = dates[i], color = 'black', linestyle = 'dotted', linewidth = 1)
            
        ax.axvline(x = "Day END", color = 'black', linestyle = 'dotted', linewidth = 1)

        
        i = 0 # Below block is just to plot legends for lines. A trick only
        data = piv_data[dates[i]]
        ax.hlines(y=data['UB'], xmin=dates[i], xmax=dates[i], linewidth=1.5, color='red', linestyles = 'dotted', label = 'Upper Bound')
        ax.hlines(y=data['Pivot'], xmin=dates[i], xmax=dates[i], linewidth=2, color='black',label = 'Lower Bound')
        ax.hlines(y=data['LB'], xmin=dates[i], xmax=dates[i], linewidth=1.5, color='green', linestyles = 'dotted',label = 'Pivot')

        ax.hlines(y=data['S-1'], xmin=dates[i], xmax=dates[i], linewidth=2, color='green',label = 'Support 1')
        ax.hlines(y=data['R-1'], xmin=dates[i], xmax=dates[i], linewidth=2, color='red', label = 'Resistance 1')
            
        plt.legend()
        plt.show()