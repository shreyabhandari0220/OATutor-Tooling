import shutil
import sys
import time
import uuid
from datetime import datetime
from distutils.dir_util import copy_tree
from urllib.parse import urlparse
import gspread
import numpy as np
import pandas as pd
import requests
import shortuuid
from Naked.toolshed.shell import muterun_js, execute_js
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

pd.options.display.html.use_mathjax = False

from create_dir import *
from create_content import *
from validate_problem import *
from create_problem_js_files import *

import functools

print = functools.partial(print, flush=True)

URL_SPREADSHEET_KEY = '1yyeDxm52Zd__56Y0T3CdoeyXvxHVt0ITDKNKWIoIMkU'


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
    worksheet = book.worksheet('URLs')
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0])
    df = df[["Book", "URL", "Editor Sheet"]]
    df = df.astype(str)
    df.replace('', 0.0, inplace=True)
    return df


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
            if type(row["Row Type"]) == float:
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
        create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"],
                            problem_row["OER src"], problem_images,
                            variabilization=problem_row["Variabilization"], latex=latex, verbosity=verbosity)
    else:
        create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"],
                            problem_row["OER src"], problem_images, latex=latex, verbosity=verbosity)

    return error_message[:-1]  # get rid of the last newline


def process_sheet(spreadsheet_key, sheet_name, default_path, is_local, latex, verbosity=False, validator_path='',
                  editor=False, skill_model="skillModel.js", course_name=""):
    if is_local == "online":
        book = get_sheet(spreadsheet_key)
        worksheet = book.worksheet(sheet_name)
        table = worksheet.get_all_values()
        try:
            df = pd.DataFrame(table[1:], columns=table[0])
        except:
            print("[{}] data frame not found, returning early".format(sheet_name))
            return None, None
        if "Problem ID" not in df.columns:
            df["Problem ID"] = ""
        if "Lesson ID" not in df.columns:
            df["Lesson ID"] = ""
        ##Only keep columns we need
        variabilization = 'Variabilization' in df.columns
        try:
            if variabilization:
                df = df[["Problem Name", "Row Type", "Variabilization", "Title", "Body Text", "Answer", "answerType",
                         "HintID", "Dependency", "mcChoices", "Images (space delimited)", "Parent", "OER src",
                         "openstax KC", "KC", "Taxonomy", "Problem ID", "Lesson ID"]]
            else:
                df = df[
                    ["Problem Name", "Row Type", "Title", "Body Text", "Answer", "answerType", "HintID", "Dependency",
                     "mcChoices", "Images (space delimited)", "Parent", "OER src", "openstax KC", "KC", "Taxonomy",
                     "Problem ID", "Lesson ID"]]
        except KeyError as e:
            print("[{}] error found: {}".format(sheet_name, e))
            error_df = pd.DataFrame(index=range(len(df)), columns=['Check 1', 'Check 2', 'Time Last Checked'])
            error_df.at[0, 'Time Last Checked'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            error_df.at[0, 'Check 1'] = str(e)
            error_df.at[0, 'Check 2'] = 'UNCHECKED'
            try:
                if variabilization:
                    set_with_dataframe(worksheet, error_df, col=18)
                else:
                    set_with_dataframe(worksheet, error_df, col=17)
            except Exception as e:
                print('Fail to write to google sheet. Waiting...')
                print('sheetname:', sheet_name, e)
                time.sleep(40)
            return None, None
        df = df.astype(str)
        df.replace('', 0.0, inplace=True)
        df.replace(' ', 0.0, inplace=True)


    elif is_local == "local":
        excel_path = '../Excel/'
        excel_path += spreadsheet_key
        try:
            df = pd.read_excel(excel_path, sheet_name, header=0)
        except:
            print("path not found:", excel_path, sheet_name)
            return None, None
        ##Only keep columns we need
        if "Problem ID" not in df.columns:
            df["Problem ID"] = ""
        if "Lesson ID" not in df.columns:
            df["Lesson ID"] = ""
        variabilization = 'Variabilization' in df.columns
        if variabilization:
            df = df[
                ["Problem Name", "Row Type", "Variabilization", "Title", "Body Text", "Answer", "answerType", "HintID",
                 "Dependency", "mcChoices", "Images (space delimited)", "Parent", "OER src", "openstax KC", "KC",
                 "Taxonomy", "Problem ID", "Lesson ID"]]
        else:
            df = df[["Problem Name", "Row Type", "Title", "Body Text", "Answer", "answerType", "HintID", "Dependency",
                     "mcChoices", "Images (space delimited)", "Parent", "OER src", "openstax KC", "KC", "Taxonomy",
                     "Problem ID", "Lesson ID"]]
        df = df.astype(str)
        df.replace('nan', float(0.0), inplace=True)

    elif is_local != "local" and is_local != "online":
        raise NameError(
            'Please enter either \'local\' to indicate a locally stored file, or \'online\' to indicate a file stored as a google sheet.')
    try:
        df["Problem Name"] = df["Problem Name"].str.replace(r"\s", "", regex=True)
        df["Body Text"] = df["Body Text"].str.replace("\"", "\\\"")
        df["Title"] = df["Title"].str.replace("\"", "\\\"")
        df["Answer"] = df["Answer"].str.replace("\"", "\\\"")
        df["mcChoices"] = df["mcChoices"].str.replace("\"", "\\\"")
        df["Body Text"] = df["Body Text"].str.replace("\\n", r" \\\\n ", regex=True)
        df["Title"] = df["Title"].str.replace("\\n", r" \\\\n ", regex=True)
        df["openstax KC"] = df["openstax KC"].str.replace("\'", "\\\'")
        df["KC"] = df["KC"].str.replace("\'", "\\\'")
    except AttributeError:
        pass
    

    skillModelJS_lines = []
    skills = []
    skills_unformatted = []
    if not editor:
        skillModelJS_path = os.path.join("..", skill_model)
        if not os.path.exists(skillModelJS_path):
            skillModelJS_file = open(skillModelJS_path, "a", encoding="utf-8")
            skillModelJS_file.write("const skillModel = {\n\n    // Start Inserting\n\n}\n\nexport default skillModel;")
            skillModelJS_file.close()
        skillModelJS_file = open(skillModelJS_path, "r", encoding="utf-8")

        # Insert before "Start Inserting"
        break_index = 0
        line_counter = 0
        for line in skillModelJS_file:
            if "Start Inserting" in line:
                break_index = line_counter
            skillModelJS_lines.append(line)
            line_counter += 1

    error_data = []
    error_df = pd.DataFrame(index=range(len(df)), columns=['Check 1', 'Check 2', 'Time Last Checked'])
    error_df.at[0, 'Time Last Checked'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    debug_df = pd.DataFrame(index=range(len(df)), columns=['Debug Link', 'Problem ID', 'Lesson ID'])
    debug_platform_template = "https://cahlr.github.io/OATutor-Content-Staging/#/debug/{}"

    print("[{}] JS validator start".format(sheet_name))

    lesson_id = df.at[0, "Lesson ID"]
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
                error_df.at[error_row, 'Check 1'] = question_error_message
                error_df.at[error_row, 'Check 2'] = 'UNCHECKED'
                raise Exception("Error encountered in validator")
        except Exception as e:
            if str(e) != "Error encountered in validator":  # unknown error
                error_row = (df[df['Problem Name'] == problem_name].index)[0]
                error_df.at[error_row, 'Check 1'] = str(e)
                error_df.at[error_row, 'Check 2'] = 'UNCHECKED'
            continue

        # process problem skill(s)
        try:
            problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
            problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
        except:
            if verbosity:
                print("Problem skills empty for: ", problem_name)
            raise Exception("Problem Skills broken")

        result_problems = ""
        problem_name, path, problem_js = create_problem_dir(sheet_name, problem_name, default_path, verbosity)
        step_count = 0
        debug_df.at[first_problem_index, 'Debug Link'] = debug_platform_template.format(problem_name)
        debug_df.at[first_problem_index, 'Problem ID'] = problem_name
        current_step_name = step_reg_js = default_pathway_js = ""
        images = False
        figure_path = ""
        problem_row = question.iloc[0]
        tutoring = []
        current_subhints = []
        previous_tutor = ""
        previous_images = ""
        hint_dic = {}

        for i in range(len(problem_skills)):
            if (i != 0):
                result_problems += ", "
            result_problems += "'{0}'".format(problem_skills[i])
            skills_unformatted.extend(problem_skills)

        for index, row in question.iterrows():
            # checks row type
            row_type = row['Row Type'].strip().lower()
            if index != 0:  # Not problem row
                if row_type == "step":
                    step_count, current_step_name, tutoring, skills, images, figure_path, default_pathway_js = \
                        write_step_js(default_path, problem_name, row, step_count, tutoring, skills, images, 
                        figure_path, default_pathway_js, path, verbosity, variabilization, latex, result_problems)

                if (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                    images, hint_dic, current_subhints, tutoring, figure_path = \
                        write_subhint_js(row, row_type, current_step_name, current_subhints, tutoring, previous_tutor, 
                        previous_images, images, path, figure_path, hint_dic, verbosity, variabilization, latex)

                elif row_type == "hint":
                    images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path = \
                        write_hint_js(row, current_step_name, tutoring, images, figure_path, path, hint_dic, 
                        verbosity, variabilization, latex)
                
                elif row_type == "scaffold":
                    images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path = \
                        write_scaffold_js(row, current_step_name, tutoring, images, figure_path, path, hint_dic, 
                                    verbosity, variabilization, latex)

        to_write = create_default_pathway(tutoring)
        default_pathway = open(default_pathway_js, "w", encoding="utf-8")
        default_pathway.write(to_write)
        default_pathway.close()

        write_problem_js(problem_row, problem_name, problem_js, course_name, sheet_name, images, path, 
        figure_path, verbosity, variabilization, latex)

        # Copy problem tree over to validator_path for validator check
        if validator_path:
            val_path = create_validator_dir(problem_name, validator_path)
            try:
                shutil.copytree(path, val_path)
            except Exception as e:
                if os.path.isdir(val_path):
                    shutil.rmtree(val_path)
                os.mkdir(val_path)
                try:
                    copy_tree(path, val_path)
                except:
                    print("error with inner copy_tree")
                print("For problem:", problem_name)
                print("Encountered error when copying to validator folder")
                print(str(e))

    print("[{}] JS validator complete".format(sheet_name))

    # Write skills to skillModel
    if not editor:
        new_skillModelJS_lines = skillModelJS_lines[0:break_index] + skills + skillModelJS_lines[break_index:]
        with open(skillModelJS_path, 'w', encoding="utf-8") as f:
            for item in new_skillModelJS_lines:
                f.write(item)
    skills_unformatted = ["_".join(skill.lower().split()) for skill in skills_unformatted]

    # Update errors on the error sheet

    # for each sheet, do:
    #   1. run tinna's script, update check 1 column of error_df
    #   2. write json files to both OpenStax/ and OpenStax1/
    #   3. run matthew's index and validator script on OpenStax1/
    #   4. use validator output to update check 2 column of error_df
    #   5. write check 1 and check 2 to google spreadsheet
    #   6. Set debug links
    #   7. remove Openstax1/

    if validator_path and os.path.isdir(validator_path):
        try:
            # runs postScriptValidator.js
            execute_js('../util/indexGenerator.js', 'auto')
            response = muterun_js('../.postScriptValidator.js', 'auto')
            if response.exitcode == 0:
                error_df = validator_check(response, df, error_df, sheet_name)

            else:
                sys.stderr.write(response.stderr.decode("utf-8"))
            # remove validator directory
            shutil.rmtree(validator_path)
            for col in ['Check 1', 'Check 2']:
                if error_df[col].isnull().values.all():
                    error_df.at[0, col] = "No errors found"

        except Exception as e:
            print("For sheet:", sheet_name)
            print("Encountered error during Check 2:", e)
            pass

        try:
            set_with_dataframe(worksheet, error_df, col=len(df.columns))
        except Exception as e:
            print('Fail to write to google sheet. Waiting...')
            print('sheetname:', sheet_name, e)
            time.sleep(40)

    elif validator_path:
        try:
            set_with_dataframe(worksheet, error_df, col=len(df.columns))
        except Exception as e:
            print('Fail to write to google sheet. Waiting...')
            print('sheetname:', sheet_name, e)
            time.sleep(40)
    try:
        set_with_dataframe(worksheet, debug_df, col=len(df.columns) + len(error_df.columns))
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

    if os.path.isdir(validator_path):
        shutil.rmtree(validator_path)

    print("[{}] processing complete".format(sheet_name))

    return list(set(skills_unformatted)), lesson_id


def generate_id():
    shortuuid.set_alphabet("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQSRTUVWXYZ1234567890")
    raw_id = shortuuid.encode(uuid.uuid4())
    return raw_id[:8] + "-" + raw_id[8:12] + "-" + raw_id[12:]


def validator_check(response, df, error_df, sheet_name):
    post_script_errors = response.stdout.decode("utf-8").split('\n')
    for error in post_script_errors:
        if error:
            row_id, error_message = error.split(': ')
            # determine problem_name and row
            sha = hashlib.sha1(sheet_name.encode('utf-8')).hexdigest()[:6]
            if row_id[1:7] == sha:  # using sha1 only
                problem_name = re.search('[\D]*\d+', row_id[7:]).group(0)
            elif row_id[0] == 'b' and row_id[1].isnumeric():  # using b# and sha1
                problem_name = re.search('[\D]*\d+', row_id[re.search(sha, row_id).end(0):]).group(0)
            else:  # shouldn't need to use this
                problem_name = re.search('[\D]*[\d]+', row_id).group(0)
            if '-h' not in row_id:
                ord_step = ord(row_id[-1]) - 97
                error_row = \
                    (df[df['Problem Name'] == problem_name].index & df[df['Row Type'] == 'step'].index)[
                        ord_step]
            elif '-h' in row_id:
                ord_step = ord(re.search('\d([\D]+)\-h', row_id).group(1)) - 97
                hint_num = re.search('-(h[\d]+)', row_id).group(1)
                step_row = \
                    (df[df['Problem Name'] == problem_name].index & df[df['Row Type'] == 'step'].index)[
                        ord_step]
                all_hints = df[df['Problem Name'] == problem_name].index & df[
                    df['HintID'] == hint_num].index
                error_row = min(r for r in all_hints if r > step_row)
            else:
                error_row = (df[df['Problem Name'] == problem_name].index)[0]

            # add error message
            if not pd.isna(error_df.at[error_row, 'Check 2']):
                error_message = str(error_df.at[error_row, 'Check 2']) + '\n' + error_message
            error_df.at[error_row, 'Check 2'] = error_message

    return error_df


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
    process_sheet(sheet_key, sheet_name, '../OpenStax1', is_local, latex, validator_path='../.OpenStax Validator',
                  skill_model="skillModel1.js", course_name="")
