import pandas as pd
import numpy as np
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
# import jsbeautifier
import os
import urllib.request
import json
import re
import sys

pd.options.display.html.use_mathjax = False

# from get_sheet import get_sheet
from create_dir import *
from create_content import *


def get_sheet(spreadsheet_key, sheet_name):
    scope = ['https://spreadsheets.google.com/feeds'] 
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope) 
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(spreadsheet_key) 
    return book


def save_images(images,path, num):
    #images is a string of urls separated by spaces
    if type(images) != str:
        return "", 0
    images = images.split(" ");
    names = []
    for i in images: 
        num += 1
        name = "figure" + str(num) + ".gif"
        names.append(name)
        urllib.request.urlretrieve(i, path + "/" + name);
    return names, num


def create_default_pathway(tutoring):
    to_return = "var hints = ["
    for hint in tutoring:
        to_return += hint + ", "
    to_return += "]; export {hints};"
    return to_return


def create_problem_js(name,title,body, images=[]):
    if type(body) == float:
        body= ""
    for image in images:
        body += "\\n##{0}##".format(image)
    if type(title) == float:
        title = ""
    contents = "import React from 'react'; import { InlineMath } from 'react-katex';" + "import steps from \"./{0}-index.js\"; const problem = ".format(name) + "{" + "id: \"{0}\", title: \"{1}\", body: \"{2}\", ".format(name, title, body) 
    contents +=  "steps: steps, }; export { problem };"
    
    return contents


def process_sheet(spreadsheet_key, sheet_name, default_path):
    book = get_sheet(spreadsheet_key, sheet_name)
    worksheet = book.worksheet(sheet_name) 
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0]) 
    ##Only keep columns we need 
    df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
    
    df = df.astype(str)
    df.replace('', 0.0, inplace = True)
    df["Body Text"] = df["Body Text"].str.replace("\"", "\\\"")
    df["Title"] = df["Title"].str.replace("\"", "\\\"")
    
    
    skillModelJS_lines = []
    skills = []
    skills_unformatted = []
    skillModelJS_path = os.path.join("..","skillModel.js")
    skillModelJS_file = open(skillModelJS_path,"r")
    break_index = 0
    line_counter = 0
    for line in skillModelJS_file:
        if "Start Inserting" in line:
            break_index = line_counter
        skillModelJS_lines.append(line)
        line_counter+=1
    
    questions = [x for _, x in df.groupby(df['Problem Name'])]
    
    for question in questions:
        #gets the initial name through the first row problem name 
        problem_name = question.iloc[0]['Problem Name']
        try:
            #problem_skills = question.iloc[0]["openstax KC"].split(",")
            problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
            problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
        except:
            print("Problem skills empty for: ", problem_name)
            raise Exception("Problem Skills broken")
        result_problems = ""
        path, problem_js  = create_problem_dir(problem_name, default_path)
        step_count = tutor_count = 0
        #nice coding bro
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
                    #Look into this tomorrow it might not be taking the last step not sure what this does 
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
                    step_file = open(step_reg_js, "w")
                    step_images = ""
                    #checks images and creates the figures path if necessary
                    if type(row["Images (space delimited)"]) == str:
                        if not images:
                            figure_path = create_fig_dir(path)
                        step_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
                        images += num
                    choices = type(row["mcChoices"]) == str and row["mcChoices"]
                    step_file.write(create_step(row['Problem Name'], row['Title'], row["Body Text"], row["Answer"], row["answerType"], step_count, choices, step_images))
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
                        subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic)
                    else:
                        subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], hint_images, hint_dic=hint_dic)
                    hint_dic[row["HintID"]] = subhint_id
                    current_subhints.append(subhint)
                    tutoring.pop()
                    if previous_tutor['Row Type'] == 'hint':
                        previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic)
                    else:
                        previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"], previous_tutor["Title"], previous_tutor["Body Text"], previous_tutor["answerType"], previous_tutor["Answer"], previous_tutor["mcChoices"], previous_tutor["Dependency"], previous_images, subhints=current_subhints, hint_dic=hint_dic)
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
                        hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["Dependency"], hint_images, hint_dic=hint_dic)
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
                        scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"], row["Body Text"], row["answerType"], row["Answer"], row["mcChoices"], row["Dependency"], scaff_images, hint_dic=hint_dic)
                        hint_dic[row["HintID"]] = full_id
                        tutoring.append(scaff)
                        previous_tutor = row
                        previous_images = hint_images



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
        prob_js = create_problem_js(problem_name, problem_row["Title"], problem_row["Body Text"], problem_images)
        file = open(problem_js, "w")
        file.write(prob_js)
        file.close()

    new_skillModelJS_lines = skillModelJS_lines[0:break_index] + skills + skillModelJS_lines[break_index:]
    new_skillModelJS_lines
    with open(skillModelJS_path, 'w') as f:
        for item in new_skillModelJS_lines:
            f.write(item)
    skills_unformatted = ["_".join(skill.lower().split()) for skill in skills_unformatted]
    return list(set(skills_unformatted))

if __name__ == '__main__':
    process_sheet(sys.argv[1], sys.argv[2], '../OpenStax Content')