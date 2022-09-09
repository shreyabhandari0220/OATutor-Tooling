import pandas as pd
import numpy as np
import gspread 
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

FEEDBACK_SPREADSHEET = "1PoPG4i_gQy20YdeyYpD5SvjfohbuUwSyLCcNOKDBQ20"
SHEET_NAME = "Selenium Error Log"

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
        original_df = pd.DataFrame(columns=["Book Name", "Error Log", "Commit Hash", "Issue Type", "Status", "Comment"])

    check_df = original_df.merge(alert_df[["Error Log", "Status"]], how="left", left_on="Error Log", right_on="Error Log")
    original_df.at[(check_df["Status_x"] == "resolved") & (check_df["Status_y"] == "open"), "Status"] = "open"

    original_df = original_df.set_index("Error Log")
    alert_df = alert_df.set_index("Error Log")
    missing_rows = alert_df.index.difference(original_df.index)
    new_df = original_df.append(alert_df.loc[missing_rows])

    new_df = new_df.reset_index()
    new_df = new_df.reindex(columns=['Book Name', 'Error Log', 'Commit Hash', 'Issue Type', 'Status', 'Comment'])
    try:
        set_with_dataframe(worksheet, new_df, include_index=False)
    except Exception as e:
        print('Fail to write to google sheet.')
        print(e)
    