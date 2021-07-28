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

    
    def find_name(self, open:float, close:float, low:float, high:float):
        '''
        Find if Candle is Doji / Hammer / Shooting Star / Normal
        args:
            open: Opening Price
            close: Closing PRice
        '''
        o_c_diff = abs(close - open)
        if abs(high - max(close,open)) > o_c_diff and abs(low - min(close,open)) > o_c_diff:
            return 'Doji' # doji

        elif abs(low - min(close,open)) >  o_c_diff  or 0.30 * abs(low - min(close,open)) > abs(high - max(close,open)): # if 30% of lower > upper OR lower  > diff
            return 'Hammer'

        elif abs(high - max(close,open)) >  o_c_diff  or 0.30 * abs(high - max(close,open)) > abs(low - min(close,open)): # opposite of Hammer
            return 'Shooting Star'
        
        elif abs(high - max(close,open)) <  o_c_diff >  abs(low - min(close,open)):
            return 'Normal'

        else:
            return 'Unknown'

        
    def candle_type(self, open:float, close:float, low:float, high:float):
        color = self.find_color(open, close)
        name = self.find_name(open, close, low, high)
        return color, name  