import sys
import os
import time
import uuid
from datetime import datetime
import gspread
import pandas as pd
import numpy as np
import shortuuid
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from pathlib import Path

pd.options.display.html.use_mathjax = False

from create_dir import *
from create_content import *
from validate_problem import *
from create_problem_js_files import *

import functools

print = functools.partial(print, flush=True)

# load problem bank url
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
URL_SPREADSHEET_KEY = os.environ['URL_SPREADSHEET_KEY']

def get_sheet(spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope)
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(spreadsheet_key)
    return book


def get_all_url(bank_url):
    if not bank_url:
        bank_url = URL_SPREADSHEET_KEY
    book = get_sheet(bank_url)

    url_sheet = book.worksheet('URLs')
    url_table = url_sheet.get_all_values()
    url_df = pd.DataFrame(url_table[1:], columns=url_table[0])
    url_df = url_df[["Book", "URL", "OER", "License", "Editor Sheet"]]
    url_df = url_df.astype(str)
    url_df.replace('', 0.0, inplace=True)

    hash_sheet = book.worksheet('Content Hash')
    hash_table = hash_sheet.get_all_values()
    hash_df = pd.DataFrame(hash_table[1:], columns=hash_table[0])
    hash_df = hash_df[["Sheet Name", "Content Hash", "Changed Sheets"]]
    hash_df = hash_df.astype(str)
    hash_df.replace('', 0.0, inplace=True)

    return url_df, hash_df


def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list) + 1)


def validate_question(question, variabilization, latex, verbosity):
    problem_row = question.iloc[0]
    previous_tutor = ""
    hint_dic = {}
    problem_name = question.iloc[0]['Problem Name']
    error_message = ''
    scaff_lst = []

    if not question['Row Type'].str.contains('problem').any() and not question['Row Type'].str.contains(
            'Problem').any():
        raise Exception("Missing problem row")

    try:
        problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
        problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
    except:
        error_message = error_message + "Problem Skills broken" + '\n'

    if type(problem_row["OER src"]) != str:
        error_message = error_message + "Problem OER src missing" + '\n'

    if not question['Row Type'].str.contains('step').any() and not question['Row Type'].str.contains('Step').any():
        raise Exception("Problem does not have step(s)")

    for index, row in question.iterrows():
        # checks row type
        try:
            if type(row["Row Type"]) == float or type(row["Row Type"]) == np.float64:
                raise Exception("Row type is missing")

            row_type = row['Row Type'].strip().lower()
            if index != 0:
                if row_type == "step":
                    validate_step(row, variabilization, latex, verbosity)

                elif row_type == "hint" and type(row["Answer"]) != float:
                    raise Exception("{} is \"hint\" but has answer".format(row["HintID"]))

                elif (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                    scaff_lst, hint_dic = validate_hint_with_parent(row, scaff_lst, row_type, hint_dic, 
                                            previous_tutor, variabilization, latex, verbosity)

                elif row_type == "hint" or row_type == "scaffold":
                    previous_tutor, hint_dic = validate_hint_without_parent(row, scaff_lst, row_type, 
                                                hint_dic, variabilization, latex, verbosity)

        except Exception as e:
            error_message = error_message + str(e) + '\n'
            continue

    problem_images = ""
    if type(problem_row["Images (space delimited)"]) == str:
        validate_image(problem_row["Images (space delimited)"])
    if variabilization:
        create_problem_json(problem_name, problem_row["Title"], problem_row["Body Text"],
                            problem_row["OER src"], problem_images,
                            var_str=problem_row["Variabilization"], latex=latex, verbosity=verbosity)
    else:
        create_problem_json(problem_name, problem_row["Title"], problem_row["Body Text"],
                            problem_row["OER src"], problem_images, latex=latex, verbosity=verbosity)

    return error_message[:-1]  # get rid of the last newline


def process_sheet(spreadsheet_key, sheet_name, default_path, is_local, latex, verbosity=False, course_name=""):

    if is_local == "online":
        book = get_sheet(spreadsheet_key)
        worksheet = book.worksheet(sheet_name)
        table = worksheet.get_all_values()
        try:
            df = pd.DataFrame(table[1:], columns=table[0])
        except:
            print("[{}] data frame not found, returning early".format(sheet_name))
            return None, None, None, {}
        if "Problem ID" not in df.columns:
            df["Problem ID"] = ""
        if "Lesson ID" not in df.columns:
            df["Lesson ID"] = ""
        # Only keep columns we need
        variabilization = 'Variabilization' in df.columns
        meta = 'Meta' in df.columns
        try:
            if variabilization and meta:
                df = df[["Problem Name", "Row Type", "Variabilization", "Title", "Body Text", "Answer", "answerType",
                         "HintID", "Dependency", "mcChoices", "Images (space delimited)", "Parent", "OER src",
                         "openstax KC", "KC", "Taxonomy", "License", "Problem ID", "Lesson ID", "Meta"]]
            elif variabilization:
                df = df[["Problem Name", "Row Type", "Variabilization", "Title", "Body Text", "Answer", "answerType",
                         "HintID", "Dependency", "mcChoices", "Images (space delimited)", "Parent", "OER src",
                         "openstax KC", "KC", "Taxonomy", "License", "Problem ID", "Lesson ID"]]
            elif meta:
                df = df[["Problem Name", "Row Type", "Title", "Body Text", "Answer", "answerType",
                         "HintID", "Dependency", "mcChoices", "Images (space delimited)", "Parent", "OER src",
                         "openstax KC", "KC", "Taxonomy", "License", "Problem ID", "Lesson ID","Meta"]]
            else:
                df = df[["Problem Name", "Row Type", "Title", "Body Text", "Answer", "answerType", "HintID", "Dependency",
                     "mcChoices", "Images (space delimited)", "Parent", "OER src", "openstax KC", "KC", "Taxonomy", "License", 
                     "Problem ID", "Lesson ID"]]
        except KeyError as e:
            print("[{}] error found: {}".format(sheet_name, e))
            error_df = pd.DataFrame(index=range(len(df)), columns=['Validator Check', 'Time Last Checked'])
            error_df.at[0, 'Time Last Checked'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            error_df.at[0, 'Validator Check'] = str(e)
            try:
                if variabilization:
                    set_with_dataframe(worksheet, error_df, col=19)
                else:
                    set_with_dataframe(worksheet, error_df, col=18)
            except Exception as e:
                print('Fail to write to google sheet. Waiting...')
                print('sheetname:', sheet_name, e)
                time.sleep(40)
            return None, None, None, {}
        df = df.astype(str)
        df.replace('', 0.0, inplace=True)
        df.replace(' ', 0.0, inplace=True)


    elif is_local == "local":
       raise Exception("Local problem reads no longer supported.")

    elif is_local != "local" and is_local != "online":
        raise NameError(
            'Please enter either \'local\' to indicate a locally stored file, or \'online\' to indicate a file stored as a google sheet.')
    try:
        df["Problem Name"] = df["Problem Name"].str.replace(r"\s", "", regex=True)
    except AttributeError:
        pass

    if sheet_name[:2] == "##":
        sheet_name = sheet_name[2:]

    skills: dict = {}
    skills_unformatted = []

    error_data = []
    error_df = pd.DataFrame(index=range(len(df)), columns=['Validator Check', 'Time Last Checked'])
    error_df.at[0, 'Time Last Checked'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    debug_df = pd.DataFrame(index=range(len(df)), columns=['Debug Link', 'Problem ID', 'Lesson ID'])
    debug_platform_template = "https://cahlr.github.io/OATutor-Content-Staging/#/debug/{}"

    print("[{}] Start validating".format(sheet_name))

    lesson_id = df.at[0, "Lesson ID"]
    if type(lesson_id) is pd.Series:
        lesson_id = lesson_id[0]
    if not lesson_id or len(str(lesson_id)) <= 3:
        lesson_id = generate_id()  # DF sometimes infer float for this col
    debug_df.at[0, "Lesson ID"] = lesson_id

    questions = [x for _, x in df.groupby(df['Problem Name'])]

    for question in questions:
        first_problem_index = min(question.index)
        problem_name = question.iloc[0]['Problem Name']

        # skip empty rows
        if type(problem_name) != str:
            continue

        # validate all fields that relate to this problem
        try:
            question_error_message = validate_question(question, variabilization, latex, verbosity)
            if question_error_message:
                error_row = (df[df['Problem Name'] == problem_name].index)[0]
                error_df.at[error_row, 'Validator Check'] = question_error_message
                raise Exception("Error encountered in validator")
        except Exception as e:
            if str(e) != "Error encountered in validator":  # unknown error
                error_row = (df[df['Problem Name'] == problem_name].index)[0]
                error_df.at[error_row, 'Validator Check'] = str(e)
            continue

        # process problem skill(s)
        try:
            problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
            problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
        except:
            if verbosity:
                print("Problem skills empty for: ", problem_name)
            raise Exception("Problem Skills broken")

        problem_name, path, problem_json_path = create_problem_dir(sheet_name, problem_name, default_path, verbosity)
        step_count = 0 # used for naming steps (first step is a, second is b, etc.)

        # creates debug link from the name of the problem on the first index row of the problem
        debug_df.at[first_problem_index, 'Debug Link'] = debug_platform_template.format(problem_name)
        debug_df.at[first_problem_index, 'Problem ID'] = problem_name

        current_step_name = default_pathway_json_path = ""
        images = False
        figure_path = ""
        problem_row = question.iloc[0]
        tutoring = []
        current_subhints = []
        previous_tutor = ""
        previous_images = ""
        hint_dic = {}
        hint_oer = ""

        skills_unformatted.extend(problem_skills)

        for index, row in question.iterrows():
            # checks row type
            row_type = row['Row Type'].strip().lower()
            if index != 0:  # Not problem row
                if row_type == "step":
                    hint_oer = "" # reset hint oer for each step
                    step_count, current_step_name, tutoring, skills, images, figure_path, default_pathway_json_path = \
                        write_step_json(default_path, problem_name, row, step_count, tutoring, skills, images, 
                        figure_path, default_pathway_json_path, path, verbosity, variabilization, latex, problem_skills)

                if (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                    images, hint_dic, current_subhints, tutoring, figure_path = \
                        write_subhint_json(row, row_type, current_step_name, current_subhints, tutoring, previous_tutor, 
                        previous_images, images, path, figure_path, hint_dic, verbosity, variabilization, latex)

                elif row_type == "hint":
                    if type(row["OER src"]) != float and row["OER src"] != "":
                        hint_oer = row["OER src"]
                    images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path = \
                        write_hint_json(row, current_step_name, hint_oer, tutoring, images, figure_path, path, hint_dic, 
                        verbosity, variabilization, latex)
                
                elif row_type == "scaffold":
                    if type(row["OER src"]) != float and row["OER src"] != "":
                        hint_oer = row["OER src"]
                    images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path = \
                        write_scaffold_json(row, current_step_name, hint_oer, tutoring, images, figure_path, path, hint_dic,
                                    verbosity, variabilization, latex)

        default_pathway_str = create_default_pathway(tutoring)
        default_pathway_json_file = open(default_pathway_json_path, "w", encoding="utf-8")
        default_pathway_json_file.write(default_pathway_str)
        default_pathway_json_file.close()
        
        write_problem_json(problem_row, problem_name, problem_json_path, course_name, sheet_name, images, path, 
        figure_path, verbosity, variabilization, latex)

    print("[{}] Problems validated and written".format(sheet_name))

    skills_unformatted = ["_".join(skill.lower().split()) for skill in skills_unformatted]

    meta_dict = {}
    if meta:
        for m in df["Meta"]:
            if m:
                try:
                    key, value = m.split(": ")
                    if value.lower() == "true":
                        meta_dict[key] = True
                    elif value.lower() == "false":
                        meta_dict[key] = False
                    elif value.isnumeric():
                        meta_dict[key] = int(value)
                    else:
                        meta_dict[key] = value
                except ValueError:
                    continue

    # write error checks to content google sheets
    for col in ['Validator Check']:
        if error_df[col].isnull().values.all():
            error_df.at[0, col] = "No errors found"

    error_debug_df = pd.concat([error_df, debug_df], axis=1)
    try:
        col = len(df.columns) if not meta else len(df.columns) - 1
        set_with_dataframe(worksheet, error_debug_df, col=col)
    except Exception as e:
        print('Fail to write to google sheet. Waiting...')
        print('sheetname:', sheet_name, e)
        time.sleep(40)

    for e in error_data:
        print("====")
        print('Sheet name:', e[0])
        print('Problem name:', e[1])
        print('Error type:', e[2])
        print()

    print("[{}] Processing (and writing errors) complete".format(sheet_name))

    return list(set(skills_unformatted)), lesson_id, skills, meta_dict


def generate_id():
    shortuuid.set_alphabet("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQSRTUVWXYZ1234567890")
    raw_id = shortuuid.encode(uuid.uuid4())
    return raw_id[:8] + "-" + raw_id[8:12] + "-" + raw_id[12:]



if __name__ == '__main__':
    # when calling:
    # if stored locally: python3 final.py "local" <filename> <sheet_names>
    # if store on google sheet: python3 final.py online <sheet_key> <sheet_names> <verbosity (true or false)>
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_name = sys.argv[3]
    if sheet_name[:2] == '##':
        latex = 'FALSE'
    else:
        latex = 'TRUE'
    process_sheet(sheet_key, sheet_name, '../OpenStax1', is_local, latex, course_name="")
