import sys
from lesson import create_total

if __name__ == '__main__':
    # when calling:
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>

    is_local = sys.argv[1]
    full_update = False
    bank_url = None
    if len(sys.argv) > 2 and sys.argv[2] == "full":
        full_update = True
    elif len(sys.argv) > 2 and sys.argv[2] != "full":
        bank_url = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == "full":
        full_update = True
        
    create_total('../OpenStax Content', is_local, full_update=full_update, bank_url=bank_url)

# TODO:
# final.py full: rename old content. Run script. If checksum and exists in old content, copy over from old content. 
#                Otherwise, re-download. Remove old content.
# final.py: handle in process_sheet.py directly
# process_sheet.py: in create_problem_dir, rename old dir if exists. If checksum and exists in old dir or in full content, copy 
#                   over; otherwise, re-download. Remove old dir. 
