import pandas as pd
import numpy as np
import gspread 
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

FEEDBACK_SPREADSHEET = "1PoPG4i_gQy20YdeyYpD5SvjfohbuUwSyLCcNOKDBQ20"
SHEET_NAME = "Selenium Error Log"
# SHEET_NAME = "Test"

def alert(alert_df):
    scope = ['https://spreadsheets.google.com/feeds'] 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(FEEDBACK_SPREADSHEET)
    worksheet = book.worksheet(SHEET_NAME) 
    table = worksheet.get_all_values()
    try:
        original_df = pd.DataFrame(table[1:], columns=table[0])
    except Exception as e:
        original_df = pd.DataFrame(columns=["Error Log", "Issue Type", "Status", "Comment"])
        # print("Error when retrieving original df")
        # print(e)
        # return
    original_df = original_df.set_index("Error Log")
    alert_df = alert_df.set_index("Error Log")
    missing_rows = alert_df.index.difference(original_df.index)
    new_df = original_df.append(alert_df.loc[missing_rows])
    try:
        set_with_dataframe(worksheet, new_df, include_index=True)
    except Exception as e:
        print('Fail to write to google sheet.')
        print(e)
    

if __name__ == '__main__':
    df = pd.DataFrame([["hie", "bcd", "cde", "asdf"], 
                       ["def", 'efg', 'ghi', 'sfad']], 
                      columns = ['Error Log', 'Issue Type', 'Status', 'Comment'])
    alert(df)