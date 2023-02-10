import sys
from lesson import create_total

if __name__ == '__main__':
    # when calling:
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>

    is_local = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "full":
        full_update = True
    else:
        full_update = False
    create_total('../OpenStax Content', is_local, full_update=full_update)
