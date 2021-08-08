from pandas import DataFrame as frame


class CandlePattern:
    
    def find_color(self, open:float, close:float):
        '''
        Find if Candle is Green / Red
        args:
            open: Opening Price
            close: Closing Price
        '''
        if close < open:
            return 'Red'
        return 'Green'

    
    def find_name(self, open:float, close:float, low:float=None, high:float=None):
        '''
        Find if Candle is Doji / Hammer / Shooting Star / Normal
        args:
            open: Opening Price
            close: Closing Price
        '''    
        o_c_diff = abs(close - open)
        color = self.find_color(open,close)

        if high == open == close:
            return 'Dragonfly Doji'

        if low == open == close:
            return 'Gravestone Doji'

        if open == close:
            return 'Doji' # doji
        
        if (abs(low - min(open,close)) > 2 * abs(open-close)) and (abs(low - min(open,close) > abs(high - max(open,close)))): # twice the diff of oopen-close
            return 'Hammer' if color == 'Green' else 'Hanging Man' 
        
        if (abs(high - max(open,close)) > 2 * abs(open-close)) and (abs(high - max(open,close) > abs(low - min(open,close)))): # Opposite of Hammer
            return 'Shooting Star' if color == 'Red' else 'Inverted Hammer'
        
        if abs(high - max(close,open)) > o_c_diff and abs(low - min(close,open)) > o_c_diff:
            return 'Green Doji' if color == 'Green' else 'Red Doji' # doji
        
        if abs(high - max(close,open)) <  0.15 * o_c_diff  and  abs(low - min(close,open)) < 0.15 * o_c_diff:
            return 'Bullish' if color == 'Green' else 'Bearish'

        else:
            return f"Unknown {color}" 
    
    
    def double_candle_pattern(self, df, names = ('DATE','OPEN','CLOSE','LOW','HIGH')):
        '''
        Find Bullish or Bearish Engulfing or any pattern with 2 candles
        args:
            stocks: Pandas DataFrame
            names: Name of Columns representing ('DATE','OPEN','CLOSE','LOW','HIGH') in same order
        '''
        result = []
        Date, Open, Close, Low, High = names
        stocks = df.copy()
        
        if stocks.iloc[0,0] > stocks.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order
            last_traded = stocks.iloc[0,:]
            second_last_traded = stocks.iloc[1,:]    
        else:
            last_traded = stocks.iloc[-1,:]
            second_last_traded = stocks.iloc[-2,:] 
            
        low, high, open_ , close = last_traded[Low],last_traded[High],last_traded[Open],last_traded[Close]
        sec_low, sec_high, sec_open_ , sec_close = second_last_traded[Low], second_last_traded[High], second_last_traded[Open], second_last_traded[Close]
        
        # If current or last candle is Green and it's Open, Close Engulfs the whole of previous one, then it is Bullish Engulfing
        if (self.find_color(sec_open_, sec_close) == 'Red' and self.find_color(open_,close) == 'Green') and (sec_close >= open_ and sec_open_ <= close):
            return 'Bullish Engulfing'
        
        elif (self.find_color(sec_open_, sec_close) == 'Green' and self.find_color(open_,close) == 'Red') and (sec_close <= open_ and sec_open_ >= close):
            return 'Bearish Engulfing'

        elif (self.find_color(sec_open_, sec_close) == 'Green') and (sec_open_ < low and sec_close > high) and self.find_name(open_, close, low, high) == 'Red Doji':
            return "Bearish Harami"

        elif (self.find_color(sec_open_, sec_close) == 'Red') and (sec_close < low and sec_open_ > high) and self.find_name(open_, close, low, high) == 'Green Doji':
            return "Bullish Harami"
        
        else:
            return 'Unknown'
    
    
    def triple_candle_pattern(self, stocks, names = ('DATE','OPEN','CLOSE','LOW','HIGH')):
        '''
        Find Morning Star, Evening, V or Reverse V pattern for 3 candles
         args:
            stocks: Pandas DataFrame
            names: Name of Columns representing ('DATE','OPEN','CLOSE','LOW','HIGH') in same order
        '''
        Date, Open, Close, Low, High = names
        
        if stocks.iloc[0,0] > stocks.iloc[1,0]: # if the first Date entry [0,0] is > previous data entry [1,0] then it is in descending order
            last_traded = stocks.iloc[0,:]
            second_last_traded = stocks.iloc[1,:] 
            third_last_traded = stocks.iloc[2,:]   
        else:
            last_traded = stocks.iloc[-1,]
            second_last_traded = stocks.iloc[-2,]
            third_last_traded = stocks.iloc[-3,]
            
        
        curr_low, curr_high, curr_open_ , curr_close = last_traded[Low],last_traded[High],last_traded[Open],last_traded[Close] # current Candle
        sec_low, sec_high, sec_open_ , sec_close = second_last_traded[Low], second_last_traded[High], second_last_traded[Open], second_last_traded[Close] # Middle
        third_low, third_high, third_open_ , third_close = third_last_traded[Low], third_last_traded[High], third_last_traded[Open], third_last_traded[Close] # Third
        
        if (third_high > sec_high and third_low > sec_low) and (curr_low > sec_low and curr_high > sec_high):
            return 'V Pattern'
        
        elif (third_low < sec_low and third_high < sec_high) and (sec_high > curr_high and sec_low > curr_low):
            return 'Reverse V Pattern'

        elif ((self.find_name(curr_open_, curr_close, curr_low, curr_high) == self.find_name(sec_open_, sec_close, sec_low, sec_high) == self.find_name(third_open_, third_close, third_low, third_high) == 'Bullish') 
                and (third_close > sec_open_ > third_open_) and (sec_close > curr_open_ > sec_open_)):
            return "Three White Soldiers"

        elif ((self.find_name(curr_open_, curr_close, curr_low, curr_high) == self.find_name(sec_open_, sec_close, sec_low, sec_high) == self.find_name(third_open_, third_close, third_low, third_high) == 'Bearish') 
                and (third_close < sec_open_ < third_open_) and (sec_close < curr_open_ < sec_open_)):
            return "Three Black Crows"
        
        # shooting star. Reverse V but dependent on low and middle one should be a shooting star or reverse hammer
        else:
            return 'Unknown'
        
        
        
    