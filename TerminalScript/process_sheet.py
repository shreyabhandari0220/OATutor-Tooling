import pandas as pd
import numpy as np
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
# import jsbeautifier
import os
import urllib.request
import requests
import json
import re
import sys
import time

pd.options.display.html.use_mathjax = False

# from get_sheet import get_sheet
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
    df = df[["Book","URL","Latex"]]
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

def validate_question(question, variabilization, latex):
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

    try:
        problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
        problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
    except:
        print("Problem skills empty for: ", problem_name)
        raise Exception("Problem Skills broken")

    for index, row in question.iterrows():
        #checks row type 
        row_type = row['Row Type'].strip().lower()
        if index != 0:
            if row_type == "step":
                step_images = ""
                #checks images and creates the figures path if necessary
                if type(row["Images (space delimited)"]) == str:
                    validate_image(row["Images (space delimited)"])
                choices = type(row["mcChoices"]) == str and row["mcChoices"]
                if variabilization:
                    create_step(row['Problem Name'], row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, "", variabilization=row["Variabilization"],latex=latex)
                else:
                    create_step(row['Problem Name'], row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, "",latex=latex)
            
            elif (row_type == 'hint' or row_type == "scaffold") and type(row['Parent']) != float:
                hint_images = ""
                if type(row["Images (space delimited)"]) == str and type(row["Images (space delimited)"]) != np.float64:
                    validate_image(row["Images (space delimited)"])
                hint_id = row['Parent'] + "-" + row['HintID']
                if row_type == 'hint':
                    if variabilization:
                        subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                    else:
                        subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
                else:
                    if variabilization:
                        subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                    else:   
                        subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
                hint_dic[row["HintID"]] = subhint_id
                current_subhints.append(subhint)
                tutoring.pop()
                if previous_tutor['Row Type'] == 'hint':
                    if variabilization:
                        previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex)
                    else:
                        previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex)
                else:
                    if variabilization:
                        previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex)
                    else:
                        previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex)
                tutoring.append(previous)

            elif row_type == "hint" or row_type == "scaffold":
                tutor_count += 1
                current_subhints = []
                if row_type == "hint":
                    hint_images = ""
                    if type(row["Images (space delimited)"]) == str:
                        validate_image(row["Images (space delimited)"])
                    if variabilization:
                        hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                    else:                     
                        hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
                    hint_dic[row["HintID"]] = full_id
                    tutoring.append(hint)
                    previous_tutor = row
                    previous_images = hint_images
                if row_type == "scaffold":
                    scaff_images = ""
                    if type(row["Images (space delimited)"]) == str:
                        validate_image(row["Images (space delimited)"])
                    if variabilization:
                        scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                    else:
                        scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic,latex=latex)
                    hint_dic[row["HintID"]] = full_id
                    tutoring.append(scaff)
                    previous_tutor = row
                    previous_images = scaff_images
        
        problem_images = ""
        if type(problem_row["Images (space delimited)"]) == str:
            validate_image(problem_row["Images (space delimited)"])
        if variabilization:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images, variabilization=problem_row["Variabilization"],latex=latex)
        else:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images,latex=latex)

def process_sheet(spreadsheet_key, sheet_name, default_path, is_local, latex):
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
            print(excel_path, sheet_name)
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
    df["openstax KC"] = df["openstax KC"].str.replace("\'", "\\\'")
    df["KC"] = df["KC"].str.replace("\'", "\\\'")

    scope = ['https://spreadsheets.google.com/feeds'] 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
    gc = gspread.authorize(credentials)
    error_book = gc.open_by_key('1-QliKCPEEbq8dNI7IUAkUF_Ws6mbB738g64QaGMdN7o')
    error_worksheet = error_book.worksheet('Errors')
    
    
    skillModelJS_lines = []
    skills = []
    skills_unformatted = []
    skillModelJS_path = os.path.join("..","skillModel1.js")
    skillModelJS_file = open(skillModelJS_path,"r", encoding="utf-8")
    break_index = 0
    line_counter = 0
    error_data = []
    for line in skillModelJS_file:
        if "Start Inserting" in line:
            break_index = line_counter
        skillModelJS_lines.append(line)
        line_counter+=1
    
    questions = [x for _, x in df.groupby(df['Problem Name'])]
    
    for question in questions:
        problem_name = question.iloc[0]['Problem Name']

        try:
            validate_question(question, variabilization, latex)
        except Exception as e:
            error = [sheet_name, problem_name, str(e), time.asctime(time.localtime(time.time()))]
            error_data.append(error)
            continue

        #gets the initial name through the first row problem name 
        try:
            problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
            problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
        except:
            print("Problem skills empty for: ", problem_name)
            raise Exception("Problem Skills broken")
        result_problems = ""
        path, problem_js  = create_problem_dir(problem_name, default_path)
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
                    current_step_path, step_reg_js, default_pathway_js = create_step_dir(current_step_name, path+"/steps")
                    step_file = open(step_reg_js, "w", encoding="utf-8")
                    step_images = ""
                    #checks images and creates the figures path if necessary
                    if type(row["Images (space delimited)"]) == str:
                        if not images:
                            figure_path = create_fig_dir(path)
                        step_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                        images += num
                    choices = type(row["mcChoices"]) == str and row["mcChoices"]
                    if variabilization:
                        step_file.write(create_step(row['Problem Name'], row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, step_images, variabilization=row["Variabilization"],latex=latex))
                    else:
                        step_file.write(create_step(row['Problem Name'], row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, step_images,latex=latex))
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
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                        else:
                            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
                    else:
                        if variabilization:
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                        else:   
                            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
                    hint_dic[row["HintID"]] = subhint_id
                    current_subhints.append(subhint)
                    tutoring.pop()
                    if previous_tutor['Row Type'] == 'hint':
                        if variabilization:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex)
                        else:
                            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex)
                    else:
                        if variabilization:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic, variabilization=previous_tutor["Variabilization"],latex=latex)
                        else:
                            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic,latex=latex)
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
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                        else:                     
                            hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic,latex=latex)
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
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic, variabilization=row["Variabilization"],latex=latex)
                        else:
                            scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic,latex=latex)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(scaff)
                        previous_tutor = row
                        previous_images = scaff_images



        to_write = create_default_pathway(tutoring)
        default_pathway = open(default_pathway_js, "w", encoding="utf-8")
        default_pathway.write(to_write)
        default_pathway.close()


        problem_images = ""
        if type(problem_row["Images (space delimited)"]) == str:
            if not images:
                figure_path = create_fig_dir(path)
            problem_images, num = save_images(problem_row["Images (space delimited)"], figure_path, int(images))
            images += num
        if variabilization:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images, variabilization=problem_row["Variabilization"],latex=latex)
        else:
            prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images,latex=latex)
        re.sub("[\.js]{2,}", ".js", prob_js)
        file = open(problem_js, "w", encoding="utf-8")
        file.write(prob_js)
        file.close()

    new_skillModelJS_lines = skillModelJS_lines[0:break_index] + skills + skillModelJS_lines[break_index:]
    new_skillModelJS_lines
    with open(skillModelJS_path, 'w', encoding="utf-8") as f:
        for item in new_skillModelJS_lines:
            f.write(item)
    skills_unformatted = ["_".join(skill.lower().split()) for skill in skills_unformatted]

    # Update errors on the error sheet
    next_row = next_available_row(error_worksheet)
    end_row = str(int(next_row) + len(error_data) - 1)
    error_worksheet.update('A{}:D{}'.format(next_row, end_row), error_data)

    return list(set(skills_unformatted))

if __name__ == '__main__':
    # when calling:
    # if stored locally: python3 final.py "local" <filename> <sheet_names>
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_name = sys.argv[3]
    process_sheet(sheet_key, sheet_name, '../OpenStax1', is_local, latex)