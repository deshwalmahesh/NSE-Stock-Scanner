'''
Given stocks and Strategies, it gives you trading signals with a voice and popup
1. Run a thread which fetches data every 5-15 minutes, live
2. Run all the strategies against all stocks
3. Get all the stocks which are eligible for that strategy
4. Alert user using TTS voice and show a popup regarding stock name and the strategy of choice
'''

from gtts import gTTS
from playsound import playsound
from IPython.core.display import display, HTML
from time import sleep
from datetime import datetime, timedelta
import threading
from logging import error


class Alerts():
    def __init__(self, broker):
        '''
        '''

    def create_intraday_alerts(self,stocks:list, strategies:dict, interval:int, broker, silent:bool = False, show_popup:bool = False):
        '''
        Create alerts based on a list of stocks and dictonary of strategies. Apply each strategy to each stock and find if any signal is there
        argS:
            stocks: List of name / symbol of stocks
            strategies: Strategies functions as dictonary as {'strategy-1': fun_1}
            interval: Time interval for the candles to consider. 5,10,15,30 are all generally suitable for intraday
            broker: An object of Broker class with logged in details. Suc as KiteZerodha or such. Ex: Kite = Kite_zerodha() -> Pass in the Kite object
            silent: Whether to use Text to Speech for sound for alerts
            show_popup: Whether to show an alert dialogue. It'll be shown in the notebook on which you are working
        '''
        assert interval in [5,10,15,30,60], "Use 'interval' only from [5,10,15, 30, 60]"

        retry = 0
        while True:
            try:
                result = {}
                for name in stocks:
                    df = broker.get_historical_data(name,data_type = 'min', no_days_back= 10, interval = interval, include_live = True) # open each stock one by one
                    for strategy in strategies.keys():
                        if strategies[strategy](df.iloc[1:,:]): # recent one will be the newest formed live candle formed
                            result[name] = strategy

                self.raise_alert(result) # We need a thread because if this task takes too long, the data 
                retry = 0
                sleep(((df.iloc[0,0].replace(tzinfo=None) + timedelta(minutes = interval, seconds = 2)) - datetime.now() ).total_seconds())
            
            except Exception as e:
                error(f'Error Occured: {e} Retrying for next {interval} minutes candle')
                retry += 1

                if retry > 3:
                    error("Maximum retries reached. Probable causes can be Logout from broker or Network issues. Exiting program")
                    break
        

    def raise_alert(self,results:dict, silent:bool = False, show_popup:bool = False): # another background thread
        '''
        Raise the alert in form of Text to speech voice or an HTML alert box
        args:
            results: A dictonary as {stock_name: strategy_name}
            silent: Whether to use Text to Speech for sound for alerts
            show_popup: Whether to show an alert dialogue. It'll be shown in the notebook on which you are working
        '''
        if len(results):
            for key in results.key():
                text =  f"{key} has an alert based on {results[key]} strategy"
                if not silent:
                    myobj = gTTS(text = text, lang='en', slow=False)
                    myobj.save("recent_alert.mp3")
                    playsound('recent_alert.mp3')
                
                if show_popup:
                    string = f'''
                    <script type="text/Javascript">
                    alert("{text}");
                    </script>
                    '''
                    display(HTML(string))