import sys
import os
import pandas as pd
from install import pip_install
from lesson import create_total

if __name__ == '__main__':
    # pip_install()

    # when calling:
    # if stored locally: python3 final.py "local" <filename.xlsx> <sheet_names>
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>
    is_local = sys.argv[1]

    get_all_in_dir = sys.argv[2]
    sheet_keys = []
    if get_all_in_dir == '..':
        for f in os.listdir("../Excel"):
            if not f.startswith('~$') and f.endswith(".xlsx"):
                sheet_keys.append(f)
    else:
        sheet_keys = sys.argv[2:]

    # sheet_key = sys.argv[2:]
    # sheet_names = sys.argv[4:]
    # if sheet_names[0] == '..':
    #     myexcel = pd.ExcelFile(sheet_key)
    #     sheet_names = [tab for tab in myexcel.sheet_names if tab[:2] != '!!']
    # create_total(sheet_key, sheet_names, '../OpenStax', is_local)

    create_total(sheet_keys, '../OpenStax', is_local)