import pandas as pd
import numpy as np
import gspread 
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from Naked.toolshed.shell import muterun_js, execute_js
from distutils.dir_util import copy_tree
import shutil
# import jsbeautifier
import os
import urllib.request
import requests
import json
import re
import sys
import time
import hashlib

pd.options.display.html.use_mathjax = False

from create_dir import *
from create_content import *

URL_SPREADSHEET_KEY = '1yyeDxm52Zd__56Y0T3CdoeyXvxHVt0ITDKNKWIoIMkU'

def get_sheet(spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds'] 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(spreadsheet_key) 
    return book


def save_images(images,path, num):
    #images is a string of urls separated by spaces
    if type(images) != str:
        return "", 0
    images = images.split(" ")
    names = []
    for i in images: 
        num += 1
        name = "figure" + str(num) + ".gif"
        names.append(name)
        r = requests.get(i)
        with open(path + "/" + name, 'wb') as outfile:
            outfile.write(r.content)
    return names, num


def create_default_pathway(tutoring):
    to_return = "var hints = ["
    for hint in tutoring:
        to_return += hint + ", "
    to_return += "]; export {hints};"
    return to_return

def get_all_url():
    book = get_sheet(URL_SPREADSHEET_KEY)
    worksheet = book.worksheet('URLs')
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0])
    df = df[["Book","URL"]]
    df = df.astype(str)
    df.replace('', 0.0, inplace = True)
    return df

def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)

def validate_image(image):
    try:
        requests.get(image)
    except:
        raise Exception("Image retrieval error")

def validate_question(sheet_name, question, variabilization, latex, verbosity):
    result_problems = ""
    step_count = tutor_count = 0
    current_step_path = current_step_name = step_reg_js = step_index_js = default_pathway_js = ""
    images = False
    figure_path = ""
    problem_row = question.iloc[0]
    tutoring = []
    current_subhints = []
    previous_tutor = ""
    previous_images = ""
    hint_dic = {}
    problem_name = question.iloc[0]['Problem Name']
    error_message = ''

    if not question['Row Type'].str.contains('problem').any() and not question['Row Type'].str.contains('Problem').any():
        raise Exception("Missing problem row")

    try:
        problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
        problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
    except:
        raise Exception("Problem Skills broken")

    if not question['Row Type'].str.contains('step').any() and not question['Row Type'].str.contains('Step').any():
        raise Exception("Problem does not have step(s)")
    

    for index, row in question.iterrows():
        #checks row type 
        try:
            row_type = row['Row Type'].strip().lower()
            if index != 0:
                if row_type == "step":
                    step_images = ""
                    #checks images and creates the figures path if necessary
                    if type(row["Images (space delimited)"]) == str:
                        validate_image(row["Images (space delimited)"])
                    choices = type(row["mcChoices"]) == str and row["mcChoices"]
                    if variabilization:
                        create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, "", variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                    else:
                        create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, "",latex=latex,verbosity=verbosity)
                
                elif (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                    hint_images = ""
                    if type(row["Images (space delimited)"]) == str and type(row["Images (space delimited)"]) != np.float64:
                        validate_image(row["Images (space delimited)"])
                    try:
                        hint_id = row['Parent'] + "-" + row['HintID']
                    except TypeError:
                        raise Exception("Hint ID is missing")
                    if row_type == 'hint':
                        # if type(row['Answer']) != float:
                        #     raise Exception("hint row has answer. Should be a scaffold")
                        if variabilization:
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    else:
                        if variabilization:
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:   
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    hint_dic[row["HintID"]] = subhint_id
                    current_subhints.append(subhint)
                    tutoring.pop()
                    if previous_tutor['Row Type'] == 'hint':
                        # if type(row['Answer']) != float:
                        #     raise Exception("hint row has answer. Should be a scaffold")
                        if variabilization:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    else:
                        if variabilization:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    tutoring.append(previous)

                elif row_type == "hint" or row_type == "scaffold":
                    tutor_count += 1
                    current_subhints = []
                    if row_type == "hint":
                        # if type(row['Answer']) != float:
                        #     raise Exception("hint row has answer. Should be a scaffold")
                        hint_images = ""
                        if type(row["Images (space delimited)"]) == str:
                            validate_image(row["Images (space delimited)"])
                        if variabilization:
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:                     
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(hint)
                        previous_tutor = row
                        previous_images = hint_images
                    if row_type == "scaffold":
                        scaff_images = ""
                        if type(row["Images (space delimited)"]) == str:
                            validate_image(row["Images (space delimited)"])
                        if variabilization:
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(scaff)
                        previous_tutor = row
                        previous_images = scaff_images
        except Exception as e:
            error_message = error_message + str(e) + '\n'
            continue

        
    problem_images = ""
    if type(problem_row["Images (space delimited)"]) == str:
        validate_image(problem_row["Images (space delimited)"])
    if variabilization:
        prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images, variabilization=problem_row["Variabilization"],latex=latex,verbosity=verbosity)
    else:
        prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images,latex=latex,verbosity=verbosity)
    
    return error_message[:-1] # get rid of the last newline

def process_sheet(spreadsheet_key, sheet_name, default_path, is_local, latex, verbosity=False, conflict_names=[], validator_path=''):
    if is_local == "online":
        book = get_sheet(spreadsheet_key)
        worksheet = book.worksheet(sheet_name) 
        table = worksheet.get_all_values()
        df = pd.DataFrame(table[1:], columns=table[0]) 
        ##Only keep columns we need 
        variabilization = 'Variabilization' in df.columns
        if variabilization:
            df = df[["Problem Name","Row Type","Variabilization","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
        else:
            df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
        df = df.astype(str)
        df.replace('', 0.0, inplace = True)
        df.replace(' ', 0.0, inplace = True)
        

    elif is_local == "local":
        excel_path = '../Excel/'
        excel_path += spreadsheet_key
        try:
            df = pd.read_excel(excel_path, sheet_name, header=0)
        except:
            print("path not found:", excel_path, sheet_name)
            return
        ##Only keep columns we need 
        variabilization = 'Variabilization' in df.columns
        if variabilization:
            df = df[["Problem Name","Row Type","Variabilization","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
        else:
            df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
        df = df.astype(str)
        df.replace('nan', float(0.0), inplace=True)

    elif is_local != "local" and is_local != "online":
        raise NameError('Please enter either \'local\' to indicate a locally stored file, or \'online\' to indicate a file stored as a google sheet.')

    df["Body Text"] = df["Body Text"].str.replace("\"", "\\\"")
    df["Title"] = df["Title"].str.replace("\"", "\\\"")
    df["Answer"] = df["Answer"].str.replace("\"", "\\\"")
    try:
        df["mcChoices"] = df["mcChoices"].str.replace("\"", "\\\"")
    except AttributeError:
        pass
    df["Body Text"] = df["Body Text"].str.replace("\\n", r" \\\\n ")
    df["Title"] = df["Title"].str.replace("\\n", r" \\\\n ")
    df["openstax KC"] = df["openstax KC"].str.replace("\'", "\\\'")
    df["KC"] = df["KC"].str.replace("\'", "\\\'")
    

    skillModelJS_lines = []
    skills = []
    skills_unformatted = []
    skillModelJS_path = os.path.join("..","skillModel1.js")
    skillModelJS_file = open(skillModelJS_path,"r")
    break_index = 0
    line_counter = 0
    error_data = []
    error_df = pd.DataFrame(index=range(len(df)), columns=['Check 1', 'Check 2'])
    for line in skillModelJS_file:
        if "Start Inserting" in line:
            break_index = line_counter
        skillModelJS_lines.append(line)
        line_counter+=1
    
    questions = [x for _, x in df.groupby(df['Problem Name'])]
    
    for question in questions:
        problem_name = question.iloc[0]['Problem Name']
        
        # skip empty rows
        if type(problem_name) != str:
            continue

        # validate all fields that relate to this problem
        try:
            question_error_message = validate_question(sheet_name, question, variabilization, latex, verbosity)
            if question_error_message:
                error_row = (df[df['Problem Name'] == problem_name].index)[0]
                # error_row = worksheet.find(problem_name).row
                error_df.at[error_row, 'Check 1'] = question_error_message
                error_df.at[error_row, 'Check 2'] = 'UNCHECKED'
                raise Exception("Error encountered in validator")
        except Exception as e:
            if str(e) != "Error encountered in validator":
                error_row = (df[df['Problem Name'] == problem_name].index)[0]
                # error_row = worksheet.find(problem_name).row
                error_df.at[error_row, 'Check 1'] = str(e)
                error_df.at[error_row, 'Check 2'] = 'UNCHECKED'
            continue

        #gets the initial name through the first row problem name 
        try:
            problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
            problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
        except:
            if verbosity:
                print("Problem skills empty for: ", problem_name)
            raise Exception("Problem Skills broken")
        result_problems = ""
        problem_name, path, problem_js = create_problem_dir(sheet_name, problem_name, default_path, verbosity, conflict_names)
        step_count = tutor_count = 0
        current_step_path = current_step_name = step_reg_js = step_index_js = default_pathway_js = ""
        images = False
        figure_path = ""
        problem_row = question.iloc[0]
        tutoring = []
        current_subhints = []
        previous_tutor = ""
        previous_images = ""
        hint_dic = {}

        for i in range(len(problem_skills)):
            if (i!=0):
                result_problems += ", "
            result_problems += "'{0}'".format(problem_skills[i])
            skills_unformatted.extend(problem_skills)


        for index, row in question.iterrows():
            #checks row type 
            row_type = row['Row Type'].strip().lower()
            if index != 0:
                if row_type == "step":
                    if step_count > 0:
                        #writes to step 
                        to_write = create_default_pathway(tutoring)
                        default_pathway = open(default_pathway_js, "w")
                        default_pathway.write(to_write)
                        default_pathway.close()
                    tutoring = []
                    step_count += 1
                    tutor_count = 0
                    #sets the current step name and path
                    current_step_name = problem_name + chr(96+step_count)
                    step_file = open(default_path + "/stepfiles.txt", "a+")
                    step_file.writelines("    " + current_step_name + ": " + "[\"realnumber\"], \n")
                    #creates step js files 
                    current_step_path, step_reg_js, default_pathway_js = create_step_dir(current_step_name, path+"/steps", verbosity)
                    step_file = open(step_reg_js, "w")
                    step_images = ""
                    #checks images and creates the figures path if necessary
                    if type(row["Images (space delimited)"]) == str:
                        if not images:
                            figure_path = create_fig_dir(path)
                        step_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                        images += num
                    choices = type(row["mcChoices"]) == str and row["mcChoices"]
                    if variabilization:
                        step_file.write(create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, step_images, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity))
                    else:
                        step_file.write(create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, step_images,latex=latex,verbosity=verbosity))
                    step_file.close()
                    
                    
                    
                    skill = "    {0}: [{1}],\n".format(current_step_name,result_problems)
                    skills.append(skill)
                    
                if (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                    hint_images = ""
                    if type(row["Images (space delimited)"]) == str and type(row["Images (space delimited)"]) != np.float64:
                        if not images:
                            figure_path = create_fig_dir(path)
                        hint_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                        images += num
                    hint_id = row['Parent'] + "-" + row['HintID']
                    if row_type == 'hint':
                        if variabilization:
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    else:
                        if variabilization:
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:   
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    hint_dic[row["HintID"]] = subhint_id
                    current_subhints.append(subhint)
                    tutoring.pop()
                    if previous_tutor['Row Type'] == 'hint':
                        if variabilization:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    else:
                        if variabilization:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                    tutoring.append(previous)
                elif row_type == "hint" or row_type == "scaffold":
                    tutor_count += 1
                    current_subhints = []
                    if row_type == "hint":
                        hint_images = ""
                        if type(row["Images (space delimited)"]) == str:
                            if not images:
                                figure_path = create_fig_dir(path)
                            hint_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                            images += num   
                        if variabilization:
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:                     
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(hint)
                        previous_tutor = row
                        previous_images = hint_images
                    if row_type == "scaffold":
                        scaff_images = ""
                        if type(row["Images (space delimited)"]) == str:
                            if not images:
                                figure_path = create_fig_dir(path)
                            scaff_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                            images += num
                        if variabilization:
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex,verbosity=verbosity)
                        else:
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic,latex=latex,verbosity=verbosity)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(scaff)
                        previous_tutor = row
                        previous_images = scaff_images



        to_write = create_default_pathway(tutoring)
        default_pathway = open(default_pathway_js, "w")
        default_pathway.write(to_write)
        default_pathway.close()


        problem_images = ""
        if type(problem_row["Images (space delimited)"]) == str:
            if not images:
                figure_path = create_fig_dir(path)
            problem_images, num = save_images(problem_row["Images (space delimited)"], figure_path, int(images))
            images += num
        if variabilization:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images, variabilization=problem_row["Variabilization"],latex=latex,verbosity=verbosity)
        else:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images,latex=latex,verbosity=verbosity)
        re.sub("[\.js]{2,}", ".js", prob_js)
        file = open(problem_js, "w")
        file.write(prob_js)
        file.close()
        if validator_path:
            val_path = create_validator_dir(problem_name, validator_path)
            copy_tree(path, val_path)

    new_skillModelJS_lines = skillModelJS_lines[0:break_index] + skills + skillModelJS_lines[break_index:]
    with open(skillModelJS_path, 'w') as f:
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
    #   6. remove Openstax1/

    if validator_path and os.path.isdir(validator_path):
        try:
            # runs postScriptValidator.js
            execute_js('../util/indexGenerator.js', 'auto')
            response = muterun_js('../.postScriptValidator.js', 'auto')
            if response.exitcode == 0:
                post_script_errors = response.stdout.decode("utf-8").split('\n')
                for error in post_script_errors:
                    if error:
                        row_id, error_message = error.split(': ')
                        # determine problem_name and row
                        if row_id[1:7] == hashlib.sha1(sheet_name.encode('utf-8')).hexdigest()[:6]: #case 1 of name conflict
                            problem_name = re.search('[\D]*\d', row_id[7:]).group(0)
                        elif row_id[0] == 'a' and row_id[1].isnumeric():  #case 2 of name conflict
                            problem_name = re.search('(?<=a\d)([\D]*\d)', row_id).group(0)
                        else: #case without name conflict
                            problem_name = re.search('[\D]*\d', row_id).group(0)
                        if '-h' not in row_id:
                            ord_step = ord(row_id[-1]) - 97
                            error_row = (df[df['Problem Name'] == problem_name].index & df[df['Row Type'] == 'step'].index)[ord_step]
                        elif '-h' in row_id:
                            ord_step = ord(re.search('\d([\D]+)\-h', row_id).group(1)) - 97
                            hint_num = re.search('-(h[\d]+)', row_id).group(1)
                            step_row = (df[df['Problem Name'] == problem_name].index & df[df['Row Type'] == 'step'].index)[ord_step]
                            all_hints = df[df['Problem Name'] == problem_name].index & df[df['HintID'] == hint_num].index
                            error_row = min(r for r in all_hints if r > step_row)
                        else:
                            error_row = (df[df['Problem Name'] == problem_name].index)[0]

                        # add error message
                        if not pd.isna(error_df.at[error_row, 'Check 2']):
                            error_message = str(error_df.at[error_row, 'Check 2']) + '\n' + error_message
                        error_df.at[error_row, 'Check 2'] = error_message
                
            else:
                sys.stderr.write(response.stderr.decode("utf-8"))
            #remove validator directory
            shutil.rmtree(validator_path)

        except Exception as e:
            print(e)
            pass

        set_with_dataframe(worksheet, error_df, col=len(df.columns)+2)


    for e in error_data:
        print("====")
        print('Sheet name:', e[0])
        print('Problem name:', e[1])
        print('Error type:', e[2])
        print()
    
    

    return list(set(skills_unformatted))

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
    if len(sys.argv) == 5:
        validator_path = sys.argv[4]
    else:
        validator_path = ''
    process_sheet(sheet_key, sheet_name, '../OpenStax1', is_local, latex, validator_path='../OpenStax Validator')