import sys
from install import pip_install
from lesson import create_total

if __name__ == '__main__':
    pip_install()

    # when calling:
    # if stored locally: python3 final.py "local" <filename.xlsx> <sheet_names>
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_names = sys.argv[3:]
    create_total(sheet_key, sheet_names, '../OpenStax Content', is_local)