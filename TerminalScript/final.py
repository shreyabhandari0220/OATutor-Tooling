import sys
from install import pip_install
from lesson import create_total

if __name__ == '__main__':
    pip_install()
    spreadsheet_key = sys.argv[1]
    sheet_names = sys.argv[2:]
    create_total(spreadsheet_key, sheet_names, '../Open')