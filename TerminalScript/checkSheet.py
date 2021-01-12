import pandas as pd
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
import sys

pd.options.display.html.use_mathjax = False


def check_sheet(spreadsheet_key, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds'] 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(spreadsheet_key) 

    scaff_dic = {"mc": "string", "numeric": "TextBox", "algebra": "TextBox", "string": "string"}
    worksheet = book.worksheet(sheet_name) 
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0]) 
    ##Only keep columns we need 
    df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
    
    df = df.astype(str)
    df.replace('', 0.0, inplace = True)
    
    for index, row in df.iterrows():
        if type(row["Problem Name"]) != str:
            print(sheet_name, "Problem Name")
            print(row)
        if (row["Row Type"] == "hint" or row["Row Type"] == "scaffold") and type(row["HintID"]) != str:
            print(sheet_name, "Hint ID")
            print(row)
        if (row["Row Type"] == "step" or row["Row Type"] == "scaffold") and type(row["answerType"]) != str:
            print(sheet_name, "answer type")
            print(row)
        if (row["Row Type"] == "problem" and type(row["openstax KC"]) != str):
            print(sheet_name, "kc")
            print(row)
        if (row["Row Type"] == "scaffold" and row["answerType"] not in scaff_dic):
            print(sheet_name, "answer Type")
            print(row)

if __name__ == '__main__':
    spreadsheet_key = sys.argv[1]
    sheets = sys.argv[2:]
    for sheet in sheets:
        print('checking:', sheet)
        check_sheet(spreadsheet_key, sheet)