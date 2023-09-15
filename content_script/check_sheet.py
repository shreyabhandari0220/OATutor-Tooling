import pandas as pd
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
import sys

pd.options.display.html.use_mathjax = False


def check_sheet(spreadsheet_key, sheet_name, is_local):
    scaff_dic = {"mc": "string", "numeric": "TextBox", "algebra": "TextBox", "string": "string", "short-essay": "string"}

    if is_local == "online":
        scope = ['https://spreadsheets.google.com/feeds'] 
        credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
        gc = gspread.authorize(credentials)
        book = gc.open_by_key(spreadsheet_key)
        worksheet = book.worksheet(sheet_name) 
        table = worksheet.get_all_values()
        df = pd.DataFrame(table[1:], columns=table[0])
    
    elif is_local != "local" and is_local != "online":
        raise NameError('Please enter either \'local\' to indicate a locally stored file, or \'online\' to indicate a file stored as a google sheet.')

    ##Only keep columns we need 
    df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
    
    df = df.astype(str)
    if not is_local:
        df.replace('', 0.0, inplace = True)
    else:
        df.replace('nan', float(0.0), inplace=True)

    df["Body Text"] = df["Body Text"].str.replace("\"", "\\\"")
    df["Title"] = df["Title"].str.replace("\"", "\\\"")

    for index, row in df.iterrows():
        if type(row["Problem Name"]) != str:
            # file.write('\n' + str(sheet_name) + "Problem Name\n")
            # file.write(str(row))
            # file.write('\n')
            print(sheet_name, "Problem Name")
            print(row)
        if (row["Row Type"] == "hint" or row["Row Type"] == "scaffold") and type(row["HintID"]) != str:
            # file.write('\n' + str(sheet_name) + "Hint ID\n")
            # file.write(str(row))
            # file.write('\n')
            print(sheet_name, "Hint ID")
            print(row)
        if (row["Row Type"] == "step" or row["Row Type"] == "scaffold") and type(row["answerType"]) != str:
            # file.write('\n' + str(sheet_name) + "answer type\n")
            # file.write(str(row))
            # file.write('\n')
            print(sheet_name, "answer type")
            print(row)
        if (row["Row Type"] == "problem" and type(row["openstax KC"]) != str):
            # file.write('\n' + str(sheet_name) + "kc\n")
            # file.write(str(row))
            # file.write('\n')
            print(sheet_name, "kc")
            print(row)
        if (row["Row Type"] == "scaffold" and row["answerType"] not in scaff_dic):
            # file.write('\n' + str(sheet_name) + "answer Type\n")
            # file.write(str(row))
            # file.write('\n')
            print(sheet_name, "answer Type")
            print(row)

if __name__ == '__main__':
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_names = sys.argv[3:]
    if sheet_names[0] == '..':
        myexcel = pd.ExcelFile(sheet_key)
        sheet_names = [tab for tab in myexcel.sheet_names if tab[:2] != '!!']    
    file = open("errors.txt", "a")
    for sheet in sheet_names:
        file.write('checking:' + str(sheet) + '\n')
        print('checking:', sheet)
        check_sheet(sheet_key, sheet, is_local)

    file.close()