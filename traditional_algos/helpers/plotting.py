import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import timedelta

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

                     
    def plot_candlesticks(self,df, names = ('DATE','OPEN','CLOSE','LOW','HIGH'), mv:list = [200], slider:bool = False, fig_size:bool = (1400,700), plot:bool = True):
        '''
        Plot a candlestick on a given dataframe
        args:
            df: DataFrame
            names: Tuple of column names showing ('DATE','OPEN','CLOSE','LOW','HIGH')
            mv: Moving Averages
            slider: Whether to have below zoom slider or not
            fig_size: Size of Figure as (Width, Height)
            plotting: Whether to plot the figure or just return the figure for firther modifications
        '''
        delta = df.iloc[0,0] - df.iloc[1,0]
        kind = 'day' if delta.days > 0 else 'intra'
        freq = int(delta.seconds / 60) if kind == 'intra' else None
        candle_text = f"{str(freq)} Min" if freq else "Daily"
        
        stocks = df.copy()
        stocks.sort_index(ascending=False, inplace = True)  # Without reverse, recent rolling mean will be either NaN or equal to the exact value

        Date, Open, Close, Low, High = names

        mv = [] if not mv else mv # just in case you don't want to have any moving averages
        colors = np.random.choice(['black','magenta','teal','brown'],len(mv), replace = False)

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
                    dict(step = 'all',label = 'All')]))

        else:
            # grab first and last observations from df.date and make a continuous date range from that
            start = stocks['DATE'].iloc[0] - timedelta(days=1)
            end = stocks['DATE'].iloc[-1] + timedelta(days=1)

            dt_all = pd.date_range(start=start,end=end, freq = f'{str(freq)}min')
            # check which dates from your source that also accur in the continuous date range
            dt_obs = [d.strftime("%Y-%m-%d %H:%M:%S") for d in stocks['DATE']]
            # isolate missing timestamps
            dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in dt_obs]

            rangebreaks=[dict(dvalue = freq*60*1000, values=dt_breaks)]
            
            range_selector = dict(buttons = list([dict(step = 'all', label = 'All')]))

        candle = go.Figure(data = [go.Candlestick(opacity = 0.9, x = stocks[Date], name = 'X',
                                                  open = stocks[Open], high = stocks[High], low = stocks[Low], close = stocks[Close]),])
        
        for i in range(len(mv)):
            stocks[f'{str(mv[i])}-SMA'] = stocks[Close].rolling(mv[i], min_periods = 1).mean()
            candle.add_trace(go.Scatter(name=f'{str(mv[i])} MA',x=stocks[Date], y=stocks[f'{str(mv[i])}-SMA'], 
                                             line=dict(color=colors[i], width=1.7)))

            
        candle.update_xaxes(title_text = 'Date', rangeslider_visible = slider, rangeselector = range_selector, rangebreaks=rangebreaks)


        candle.update_layout(autosize = False, width = fig_size[0], height = fig_size[1],
                             title = {'text': f"{stocks['SYMBOL'][0]} : {str(candle_text)} Candles | {self.all_stocks[stocks['SYMBOL'][0]].split('_')[1]}",'y':0.97,'x':0.5,
                                      'xanchor': 'center','yanchor': 'top'},
                             margin=dict(l=30,r=30,b=30,t=30,pad=2),
                             paper_bgcolor="lightsteelblue")

        candle.update_yaxes(title_text = 'Price in Rupees', tickprefix = u"\u20B9" ) # Rupee symbol
        if plot:
            candle.show()
        return candle


    def _matplotlib_plot_pivot(self, pivot_data, name=None, plot_size:tuple = (25,7)):
        '''
        Plot Pivot points with Pivot, Upper Bound, Lower Bound, Support-1, Resistance-1
        args:
            name: Name of the stock
            pivot_data: Pivot data of the stock of the stock. If not given, it'll open the stock from downloaded and run 'get_Pivot_Points()` fun
            num_days_back: Number of days data you want to visualise
            chart_size: Size of the chart as (width, height)
        '''
        piv_data = pivot_data.copy()

        dates = list(piv_data.keys())[::-1]
        null_date = dates[-1] + timedelta(days=1)
        dates.append(null_date)
        piv_data[null_date] = None
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
            
        ax.axvline(x = dates[i], color = 'black', linestyle = 'dotted', linewidth = 1)

        
        i = 0 # Below block is just to plot legends for lines. A trick only
        data = piv_data[dates[i]]
        ax.hlines(y=data['UB'], xmin=dates[i], xmax=dates[i], linewidth=1.5, color='red', linestyles = 'dotted', label = 'Upper Bound')
        ax.hlines(y=data['Pivot'], xmin=dates[i], xmax=dates[i], linewidth=2, color='black',label = 'Lower Bound')
        ax.hlines(y=data['LB'], xmin=dates[i], xmax=dates[i], linewidth=1.5, color='green', linestyles = 'dotted',label = 'Pivot')

        ax.hlines(y=data['S-1'], xmin=dates[i], xmax=dates[i], linewidth=2, color='green',label = 'Support 1')
        ax.hlines(y=data['R-1'], xmin=dates[i], xmax=dates[i], linewidth=2, color='red', label = 'Resistance 1')
            
        plt.legend()
        plt.show()


    def pivot_plot(self,pivot_data, fig=None, name:str = None, fig_size:bool = (1000,600), sr_levels:int = 1):
        '''
        Plot Pivot points with Pivot, Upper Bound, Lower Bound, Support-1, Resistance-1
        args:
            name: Name of the stock
            pivot_data: Pivot data of the stock of the stock. If not given, it'll open the stock from downloaded and run 'get_Pivot_Points()` fun
            fig: Plotly Figure with Candlesticks data 
            fig_size: Size of Figure as (Width, Height)
            name: Name of stock
            sr_levels: Number of Support Resistance Levels. Number from 1,2,3
        '''
        piv_data = pivot_data.copy()
        if not fig:
            return self._matplotlib_plot_pivot(piv_data, name)

        dates = list(piv_data.keys())[::-1]
        null_date = dates[-1] + timedelta(days=1)
        dates.append(null_date)
        piv_data[null_date] = None
        total = len(dates)

        for i,key in enumerate(dates):
            data = piv_data[key]

            if i < total-1:
                curr_date = dates[i]
                next_date = dates[i+1]
                X_range = pd.date_range(curr_date, next_date, freq = '15T')

                fig.add_traces(go.Scatter(x=X_range,y = np.repeat([data['UB']], 100), mode="lines",line_dash="dot",line_color="red",showlegend=False, name='UB',line=dict(width = 1.5)))
                fig.add_traces(go.Scatter(x=X_range,y = np.repeat([data['Pivot']], 100), mode="lines",line_color="black",showlegend=False, name='Pivot',line=dict(width = 2)))
                fig.add_traces(go.Scatter(x=X_range,y = np.repeat([data['LB']], 100), mode="lines",line_color="green",showlegend=False, name='LB',line_dash="dot",line=dict(width = 1.5)))

                for j in range(1,sr_levels+1):
                    fig.add_traces(go.Scatter(x=X_range,y = np.repeat([data[f"S-{str(j)}"]], 100), mode="lines",line_color="green",showlegend=False, name=f"S-{str(j)}",line=dict(width = 1.3+j)))
                    fig.add_traces(go.Scatter(x=X_range,y = np.repeat([data[f"R-{str(j)}"]], 100), mode="lines",line_color="red",showlegend=False, name=f"R-{str(j)}",line=dict(width = 1.3+j)))

                fig.add_vline(x=curr_date, line_width=1, line_dash="dot", line_color="black")

        fig.add_vline(x=next_date, line_width=1, line_dash="dot", line_color="black")

        fig.update_layout(autosize = False, width = fig_size[0], height = fig_size[1])
        return fig


    def plot_Option_chain(self,symbol:str, df, compare_with, top_n:int, sup_plot_text_date: str, fig_size = (25,10)):
        '''
        Plot the N values for option chain. Takes input from with FnO.analyse_option_chain()
        args:
            symbol: Name of the Stock to analyse
            df: Original Data Frame
            compare_with: DataFrame of the stock which to want to compare with
            top_n: Plot the top-N values only
            sup_plot_text_date: Text Date of Expiry
            fig_shape: Shaoe of figure per subplot. Set according to the values you want to plot
        '''
        w,h = fig_size
        length = len(compare_with)
        odd = length%2
        rows = (length//2) + 1 if odd else length//2
        f,ax = plt.subplots(rows,2,figsize = (w,h*rows))
        f.suptitle(f"{symbol} Option Chain Analysis | Expiry : {sup_plot_text_date}", y = 0.93, fontsize = 17, weight = 600, color = 'teal')
        ax = ax.ravel()
        for i,comp_with in enumerate(compare_with):

            ax[i].set_title(comp_with, pad = 13, fontweight = 500, color = 'blue',fontsize = 15)

            if comp_with == 'changeinOpenInterest': # change has to be depicted in + nd -
                topn_df = pd.concat([df[df['contract_type'] == 'Calls_CE'].nlargest(top_n, 'absChangeOI'),df[df['contract_type'] == 'Puts_PE'].nlargest(top_n, 'absChangeOI')])
            
            elif comp_with == 'change': # change has to be depicted in positive and negative
                topn_df = pd.concat([df[df['contract_type'] == 'Calls_CE'].nlargest(top_n, 'absChange'),df[df['contract_type'] == 'Puts_PE'].nlargest(top_n, 'absChange')])

            else:
                topn_df = pd.concat([df[df['contract_type'] == 'Calls_CE'].nlargest(top_n, comp_with),df[df['contract_type'] == 'Puts_PE'].nlargest(top_n, comp_with)])

            fig = sns.barplot(x="strike_price", y=comp_with, hue="contract_type", data = topn_df, palette = {'Calls_CE': 'tab:green','Puts_PE': 'tab:red'}, ci = None, ax = ax[i])

            for c in fig.containers:
                fig.bar_label(c, fmt='%.0f', label_type='edge', padding=5, color = 'black', fontsize = 15)
                fig.margins(y=0.3)

            fig.set_ylabel(comp_with, labelpad = 10,fontsize = 13)
            fig.set_xlabel('Strike Price (in Rupees)', labelpad = 10, fontsize = 13)
            fig.grid()

        if odd:
            ax[-1].set_axis_off()