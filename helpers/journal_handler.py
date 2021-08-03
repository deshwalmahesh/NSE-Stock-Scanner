import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .investing import *
from os import remove


class JournalHandler:
    def __init__(self, key_file:str='client_sec.json',):
        '''
        Read the journal that you have used to track your investments directy from Google Drive using Google API and Credential
        args:
            key_file: json file which holds your secret key
        '''
        scope = 'https://www.googleapis.com/auth/drive' #['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
        self.gs = gspread.authorize(creds)
        
        
    def get_journal(self,excel_file_name:str='Finance Journal',working_sheet_name:str='Real Trades'):
        '''
        Open the desired Google Sheet
        args:
            excel_file_name: Name of the Excel File
            working_sheet_name: Name of the Exact you want to open
        '''
        gsheet = self.gs.open(excel_file_name)
        wsheet = gsheet.worksheet(working_sheet_name)
        df = pd.DataFrame(wsheet.get_all_records())

        df.to_csv('csvfile.csv', encoding='utf-8', index=False)
        df = pd.read_csv('csvfile.csv')
        df.dropna(subset=['Entry'],inplace = True)
        df['Buy Date'] = pd.to_datetime(df['Buy Date'])
        df['Exit Date'] = pd.to_datetime(df['Exit Date'])

        remove('csvfile.csv')
        return df