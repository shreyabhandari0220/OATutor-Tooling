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
    # is_local = sys.argv[1]
    # get_all_in_dir = sys.argv[2]
    # sheet_keys = []
    # if get_all_in_dir == '..' and is_local == 'local':
    #     for f in os.listdir("../Excel"):
    #         if not f.startswith('~$') and f.endswith(".xlsx"):
    #             sheet_keys.append(f)
    #     create_total('../OpenStax Content', is_local, sheet_keys)
    # elif get_all_in_dir == '..' and is_local == 'online':
    #     create_total('../OpenStax Content', is_local)
    # else:
    #     sheet_keys = sys.argv[2:]
    #     create_total('../OpenStax Content', is_local, sheet_keys)
    
    is_local = sys.argv[1]
    create_total('../OpenStax Content', is_local)
