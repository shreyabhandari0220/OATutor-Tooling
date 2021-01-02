#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().system('pip install gspread')


# In[ ]:


get_ipython().system('pip install lax')


# In[ ]:


get_ipython().system('pip install oauth2client')


# In[ ]:


get_ipython().system('pip install pytexit')


# In[ ]:


get_ipython().system('pip install jsbeautifier')


# In[ ]:


get_ipython().system('pip install subprocess')


# In[2]:


import pandas as pd
import numpy as np
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
import jsbeautifier
import os
import urllib.request
import json
import re


# In[3]:


pd.options.display.html.use_mathjax = False


# In[4]:


import textToLatex


# In[5]:


from textToLatex.pytexit import py2tex


# In[ ]:





# In[6]:


scope = ['https://spreadsheets.google.com/feeds'] 
credentials = ServiceAccountCredentials.from_json_keyfile_name('sunlit-shelter-282118-8847831293f8.json', scope) 
gc = gspread.authorize(credentials)


# In[7]:


spreadsheet_key = '1Lp0uGtQsuzxzrm1TSctuZttJRrvaG0E5cwT-75UKZeY' 
book = gc.open_by_key(spreadsheet_key) 
worksheet = book.worksheet("2.3 Models and Applications") 
table = worksheet.get_all_values()


# In[7]:


##Convert table data into a dataframe 
df3 = pd.DataFrame(table[1:], columns=table[0]) 
##Only keep columns we need 
df3 = df3[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]


# In[8]:


df3 = df3.astype(str)
df3.replace('', 0.0, inplace = True)
df = df3


# In[9]:


supported_operators = ["**", "/", "*", "+", ">", "<", "="]
supported_word_operators = ["sqrt", "abs", "inf"]
replace = {"⋅" : "*", "−" : "-", "^" : "**", "𝑥" : "x", "𝑎" : "a", "𝑏" : "b", "𝑦" : "y", "–": "-", "≥" : ">=", "≤": "<=", "∪" : "U"}
conditionally_replace = {"[" : "(", "]" : ")"}
regex = re.compile("|".join(map(re.escape, replace.keys())))

#Figure out way to deal with equal signs
def preprocess_text_to_latex(text, tutoring=False, stepMC= False):
    text = str(text)
    text = regex.sub(lambda match: replace[match.group(0)], text)
    if not re.findall("[\[|\(][-\d\s\w]+,[-\d\s\w]+[\)|\]]", text): #Checking to see if there are coordinates/intervals before replacing () with []
        text = regex.sub(lambda match: conditionally_replace[match.group(0)], text)
    
    
    #Account for space in sqrt(x, y)
    text = re.sub(r"sqrt[\s]?\(([^,]+),[\s]+([^\)])\)", r"sqrt(\g<1>,\g<2>)", text)
    text = re.sub(r"sqrt(?:\s*)?\(", r"sqrt(", text)
    text = re.sub(r"abs(?:\s*)?\(", r"abs(", text)
    text = re.sub("\([\s]*([-\d]+)[\s]*,[\s]*([-\d]+)[\s]*\)", "(\g<1>,\g<2>)", text) #To account for coordinates
    for operator in supported_operators:
        text = re.sub("(\s?){0}(\s?)".format(re.escape(operator)), "{0}".format(operator), text)
        
    words = text.split()
    latex = False
    for i in list(range(len(words))):
        word = words[i]
        
        if any([op in word for op in supported_operators]) or any([op in word for op in supported_word_operators]):
            punctuation = re.findall("[\?\.,:]+}$", word) #Capture all the punctuation at the end of the sentence
            if punctuation:
                punctuation = punctuation[0]
            else:
                punctuation = ""
            word = re.sub("[\?\.,:]+}$", "", word)
            try:                
                sides = re.split('(=|U|<=|>=)', word)
                sides = [handle_word(side) for side in sides]
                new_word = ""
                if tutoring and stepMC:
                    new_word = "$$" + "".join(sides) + "$$"
                    #sides = ["$$" + side + "$$" for side in sides] 
                elif tutoring:
                    new_word = "$$" + "".join([side.replace("\\", "\\\\") for side in sides]) + "$$"
                    #sides = ["$$" + side.replace("\\", "\\\\") + "$$" for side in sides]
                else:
                    new_word = "<InlineMath math=\"" + "".join(sides) + "\"/>"
                    #sides = ["<InlineMath math=\"" + side + "\"/>" for side in sides]
                #new_word = "=".join(sides)
                new_word += punctuation
                latex=True
                words[i] = new_word
                
            except Exception as e:
                print("This failed")
                print(word)
                print(e)
                pass
    text = " ".join(words)
    return text, latex

def handle_word(word):
    latex_dic = {"=": "=", "U": " \cup ", "<=" : " \leq ", ">=" : " \geq "}
    if word in latex_dic:
        return latex_dic[word]
    
    coordinates = re.findall("[\(|\[][-\d\s]+,[-\d\s]+[\)|\]]",word)
    if coordinates:
        word = re.sub("inf", r"\\infty", word)
        return word
    
    word = re.sub("\+/-", "pm(a)", word)
    
    original_word = word
    scientific_notation = re.findall("\(?([\d]{2,})\)?\*([\d]{2,})\*\*", word)
    word = re.sub(":sqrt", ": sqrt", word)
    square_roots = re.findall(r"sqrt\(([^,]*)\,([^\)]*)\)", word)
    word = re.sub(",", "", word)
    for root in square_roots:
        word = re.sub(r"sqrt\("+root[0]+root[1]+"\)", r"sqrt("+root[0]+","+root[1]+")", word)
    #word = re.sub(r"sqrt\(([^,]*)\,([^\)]*)\)", r"sqrt(\g<1>:\g<2>)", "sqrt(2, 3)")
    word = re.sub(r"([\w])(\(+[\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\)+)([\w])", "\g<1>*\g<2>", word)
    word = re.sub(r"(\))(\()", "\g<1>*\g<2>", word)
    word = re.sub(r"([0-9]+)([a-zA-Z])", "\g<1>*\g<2>", word)
    #word = re.sub( r"([a-zA-Z])(?=[a-zA-Z])" , r"\1*" , word)
    word = re.sub(r"sqrt\*", r"sqrt", word)
    word = re.sub(r"abs\*", r"abs", word)
    word = re.sub(r"pm\*", r"pm", word)
    word = py2tex(word, simplify_output=False)
    
    #Here do the substitutions for the things that py2tex can't handle
    for item in scientific_notation:
        word = re.sub(item[0] + "\{" + item[1] + "\}", item[0] + "\\\\times {" + item[1] + "}", word)
    word = re.sub(r"\\operatorname{pm}\\left\(a\\right\)(\\times)?", r"\\pm ", word)
    
    return word[2:-2]


# In[10]:


def create_problem_dir(name, path):
    #creates directory for problem
    target = path + "/" + name
    os.mkdir(target)
    os.mkdir(target + "/steps")
    problem_js = target + "/" + name+".js"
    open(problem_js, "x")
    return target, problem_js


# In[11]:


def create_fig_dir(path):
    figures = path+"/figures"
    os.mkdir(figures)
    return figures


# In[12]:


def create_step_dir(name, path):
    target = path + "/" + name
    os.mkdir(target)
    os.mkdir(target + "/tutoring")
    reg_js = target + "/" + name+".js"
    default_pathway = target + "/tutoring/" + name + "DefaultPathway.js" 
    print("This is the pathway for " + name, default_pathway)
    open(reg_js, "x")
    open(default_pathway,"x")
    return target, reg_js, default_pathway


# In[13]:


def create_problem_index(num_steps, name):
    index_text = ""
    for i in list(range(1, num_steps+1)):
        letter = chr(96+i)
        step = name+letter
        index_text += "import {" + "step as step{0}".format(i) +"}" + " from './steps/{0}/{0}.js'; ".format(step)
    index_text += "var steps = ["
    for i in list(range(1, num_steps+1)):
        step = name + chr(96+i)
        index_text += step + ", "
    index_text = index_text[:len(index_text)-2]
    index_text += "]; export default steps;"
    return index_text
    #return jsbeautifier.beautify(index_text)
    


# In[14]:


hint_dic = {"h1" : "hintyyyy-h1", "h2" : "hintyyyy-h2"}
dependencies = [hint_dic[hint_id] for hint_id in "h1,h2".split(",")]
json.dumps(dependencies)


# In[15]:


def create_hint(step, hint_id, title, body, dependencies=0.0, images=[], subhints=[], hint_dic={}):
    title, title_latex = preprocess_text_to_latex(title, True)
    body, body_latex = preprocess_text_to_latex(body, True)
    
    hint_id = step + "-" + hint_id
    for image in images:
        body += "\\n##{0}##".format(image)
    if type(dependencies) == str:
        try:
            dependencies = json.dumps([hint_dic[hint_id] for hint_id in dependencies.split(",")])
        except Exception as e:
            print("Key error")
            print(step, hint_id, title, body)
            raise Exception("hint key error")
    else:
        dependencies = "[]"
    
    subhint_text = ""
    for subhint in subhints:
        subhint_text += subhint + ", "
    subhint_text = "[" + subhint_text + "]"
    
    hint_obj = "id: \"{0}\", type: \"hint\", dependencies: {1}".format(hint_id, dependencies)
    hint_obj += ", title: \"{0}\"".format(title)
    hint_obj += ", text: \"{0}\"".format(body)
    
    if len(subhints) > 0:
        hint_obj += ", subHints: {0}".format(subhint_text)
    hint_obj = "{" + hint_obj + "}"
    return hint_obj, hint_id
    #return jsbeautifier.beautify(hint_obj), hint_id


# In[71]:


handle_word("49n**2+168n+144")


# In[72]:


hinty = create_hint("pythag1a", "h1", "Net Force", "Just do x+y", dependencies="h1,h2", images=["figure1"],hint_dic={"h1": "pythag1a-h1", "h2":"pythag1a-h2"})
print(hinty[0])


# In[16]:


scaff_dic = {"mc": "string", "numeric": "TextBox", "algebra": "TextBox", "string": "string"}

def handle_answer_type(answer_type):
    if answer_type == "mc":
        return "string", "MultipleChoice"
    elif answer_type == "string":
        return answer_type, "TextBox"
    elif answer_type == "algebra" or answer_type == "numeric":
        return "arithmetic", "TextBox"
    else:
        print(answer_type)
        raise Exception('answer type not correct' + answer_type)


# In[17]:


re.sub("\*\*", "^", "2**2")


# In[18]:


def create_scaffold(step, hint_id, title, body, answer_type, answer, mc_answers, dependencies=0.0, images="", subhints=[], hint_dic={}):
    title, title_latex = preprocess_text_to_latex(title, True)
    body, body_latex = preprocess_text_to_latex(body, True)
    
    scaffold_id = step + "-" + hint_id
    for image in images:
        body += "\\n##{0}##".format(image)

    if type(dependencies) == str:
        try:
            dependencies = json.dumps([hint_dic[hint_id] for hint_id in dependencies.split(",")])
        except Exception as e:
            print("Key error")
            print(step, hint_id, title, body)
            raise Exception("hint key error")
    else:
        dependencies = "[]"
    
    answer_type, problem_type = handle_answer_type(answer_type)
    if answer_type == "arithmetic":
        answer = re.sub("\*\*", "^", answer)
    scaff_ans = "[\"" + str(answer) + "\"]"

    
    if type(mc_answers) != float:
        mc_answers = json.dumps([preprocess_text_to_latex(mc_answer, True)[0] for mc_answer in mc_answers.split("|") if mc_answer])
        answer = preprocess_text_to_latex(answer, True)[0]
    
    

    scaff_obj = "id: \"{0}\", type: \"scaffold\", problemType: \"{1}\", answerType: \"{2}\", hintAnswer: {3}, dependencies: {4}".format(scaffold_id, problem_type, answer_type, scaff_ans, dependencies)
    scaff_obj += ", title: \"{0}\"".format(title)
    scaff_obj += ", text: \"{0}\"".format(body)
    
    
    if type(mc_answers) == str:
        scaff_obj += ", choices: {0}".format(mc_answers)
    if len(subhints) > 0:
        subhint_text = ""
        for subhint in subhints:
            subhint_text += subhint + ", "
        subhint_text = subhint_text[:-2]
        subhint_text = "[" + subhint_text + "]"    
        scaff_obj += ", subHints: {0}".format(subhint_text)

    scaff_obj = "{" + scaff_obj + "}"
    return scaff_obj, scaffold_id
    #return jsbeautifier.beautify(scaff_obj), scaffold_id


# In[19]:


print(create_scaffold("slope2a", "h1", "Slope Example (Part 1)", "what is the answer to x**2+5", "mc", "3", mc_answers="3**2|4**2|5**2|6**2", images=["figure1.gif"]))


# In[ ]:





# In[20]:


""  and True


# In[ ]:





# In[21]:


def create_step(name, title, body, answer, answer_type, number, choices="", image=""):
    step_id = name + chr(ord('a')+number-1)
    if type(body) == float:
        body = ""
    if type(title) == float:
        title = ""
    
    title, title_latex = preprocess_text_to_latex(title)
    body, body_latex = preprocess_text_to_latex(body)
    new_answer, answer_latex = preprocess_text_to_latex(answer)

    for img in image:
        body += "##" + img + "## "
    if choices:
        choices = json.dumps([preprocess_text_to_latex(mc_answer, True, True)[0] for mc_answer in choices.split("|") if mc_answer])
        answer = preprocess_text_to_latex(answer, True)[0]
    
    answer_type, problem_type = handle_answer_type(answer_type)
    if answer_type == "arithmetic":
        answer = re.sub("\*\*", "^", answer)

    step =  "import hints from \"./{0}-index.js\"; const step = ".format(step_id) + "{" + "id: \"{0}\", stepAnswer: [\"{1}\"], problemType: \"{2}\"".format(step_id, answer, problem_type)
    
    if title_latex or body_latex:
        step = "import React from 'react'; import { InlineMath } from 'react-katex';" + step
    if title_latex:
        step += ", stepTitle: <div> " + title + "</div>"
    else:
        step += ", stepTitle: \"{0}\"".format(title)
    if body_latex:
        step += ", stepBody: <div> " + body + "</div>"
    else:
        step += ", stepBody: \"{0}\"".format(body)
    
    if answer_latex:
        ", answerLatex: \"{0}\"".format(new_answer)
    
    
    
    if type(choices) == str:
        step += ", choices: " + str(choices)
    step += ", answerType: \"{0}\", hints: hints".format(answer_type) + "}; export {step};"
    return step
    #return jsbeautifier.beautify(step)


# In[22]:


create_step("slope3", "What is the slope of the line graphed below 2**2?", "", "C: 3/2", "mc", 1, choices="a|b|c|d", image="slope3.jpg")


# In[23]:


def create_step_index(name, number):
    step_id = name + chr(ord('a')+number-1)
    step_index = "import {hints as defaultPathway} from " + "'./tutoring/{0}DefaultPathway.js'; ".format(step_id) + "var hints = {defaultPathway: defaultPathway}; export default hints;"
    return step_index
    #return jsbeautifier.beautify(step_index)


# In[24]:


create_step_index("slope3", 2)


# import hints from './slope3a-index.js';
# 
# const step = {
#   id: 'slope3a',
#   stepTitle: "What is the slope of the line graphed below?",
#   stepBody: "##slope3.jpg##",
#   stepAnswer: ["C: 3/2"],
#   problemType: "MultipleChoice",
#   choices: ["A: -6", "B: -2/3", "C: 3/2", "D: 4", "0"],
#   answerType: "string",
#   hints: hints
# }
# 
# export { step };

# In[25]:


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


# In[26]:


#still working on this 
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
    #return jsbeautifier.beautify(contents)


# In[27]:


create_problem_js("Awesome", "coolio", "raw")


# In[28]:


def create_default_pathway(tutoring):
    to_return = "var hints = ["
    for hint in tutoring:
        to_return += hint + ", "
    to_return += "]; export {hints};"
    return to_return


#     {
#       id: 'pythag1a-h2',
#       title: "Net Force Example",
#       text: "What is the net vertical force if there are 2 vertical forces 2N, 3N?",
#       hintAnswer: ["5"],
#       problemType: "MultipleChoice",
#       choices: ["-5", "0", "2", "5"],
#       answerType: "string",
#       type: "scaffold",
#       dependencies: [], 
#       subHints: [{
#         id: 'pythag1a-h2-s1',
#         title: "Simple Net Force",
#         text: "What is the net vertical force if there are 2 vertical forces 1N, 2N?",
#         hintAnswer: ["3"],
#         problemType: "TextBox",
#         answerType: "numeric",
#         type: "scaffold",
#         dependencies: []
#       }],
#     }
# 

# In[29]:


"alskfdalsfjas dsubHints".find("subHints")


# In[30]:


#it takes the values and creates 
questions = [x for _, x in df.groupby(df['Problem Name'])]
questions[0]


# In[31]:


import json


# skillModelJS_lines = []
# skills = []
# skillModelJS_path = os.path.join("","skillModel.js")
# skillModelJS_file = open(skillModelJS_path,"r")
# break_index = 0
# line_counter = 0
# problem_name = "circle3a"
# problem_skills = df.iloc[0]["openstax KC"].split(",")
# #problem_skills = "short-multiplication,circle,circumference".split(",")
# result_problems = ""
# for i in range(len(problem_skills)):
#     if (i!=0):
#         result_problems += ", "
#     result_problems += "'{0}'".format(problem_skills[i])
# for line in skillModelJS_file:
#     if "Start Inserting" in line:
#         break_index = line_counter
#     skillModelJS_lines.append(line)
#     line_counter+=1
# skillModelJS_lines[break_index]
# skill = "    {0}: [{1}],\n".format(problem_name,result_problems)
# skills.append(skill)
# new_skillModelJS_lines = skillModelJS_lines[0:break_index] + skills + skillModelJS_lines[break_index:]
# new_skillModelJS_lines
# with open(skillModelJS_path, 'w') as f:
#     for item in new_skillModelJS_lines:
#         f.write(item)

# In[32]:


sheet_names = ["3.1 Functions and Function Notation", "3.2 Domain and Range", "3.3 Rates of Change and Behavior of Graphs", "3.4 Composition of Functions", "3.5 Transformation of Functions", "3.6 Absolute Value Functions", "3.7 Inverse Functions"]
for sheet in sheet_names:
    check_sheet(sheet)


# In[ ]:


scaff_dic


# In[33]:


def check_sheet(sheet_name):
    worksheet = book.worksheet(sheet_name) 
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0]) 
    ##Only keep columns we need 
    df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
    
    df = df.astype(str)
    df.replace('', 0.0, inplace = True)
    
    for index, row in df.iterrows():
        if type(row["Problem Name"]) != str:
            print(sheet_name, "Problem Name")
            print(row)
        if (row["Row Type"] == "hint" or row["Row Type"] == "scaffold") and type(row["HintID"]) != str:
            print(sheet_name, "Hint ID")
            print(row)
        if (row["Row Type"] == "step" or row["Row Type"] == "scaffold") and type(row["answerType"]) != str:
            print(sheet_name, "answer type")
            print(row)
        if (row["Row Type"] == "problem" and type(row["openstax KC"]) != str):
            print(sheet_name, "kc")
            print(row)
        if (row["Row Type"] == "scaffold" and row["answerType"] not in scaff_dic):
            print(sheet_name, "answer Type")
            print(row)
        
       
        


# For lesson plan, need the name of the sheet and the skills that it's testing:
#     - dictionary that has the name of each lesson, and then an array of the skills it's testing
# 
# For BktParams:
#     - need list of all skills

# In[34]:


("Lesson " + "1.2").lower()


# In[35]:


def create_bkt_params(name):
    return "\"" + name + "\": {probMastery: 0.1, probTransit: 0.1, probSlip: 0.1, probGuess: 0.1},"


# In[36]:


def create_lesson_plan(sheet, skills):
    lesson_number = sheet.split()[0]
    lesson_topics = " ".join(sheet.split()[1:])
    
    lesson_id = ("lesson" + lesson_number)
    lesson_name = "Lesson " + lesson_number
    learning_objectives = "{"
    for skill in skills:
        learning_objectives += skill + ": 0.95, "
    learning_objectives += "}"
    
    lesson_plan = "{id: " + "\"{0}\", name: \"{1}\", topics: \"{2}\", allowRecyle: false, learningObjectives: {3} ".format(lesson_id, lesson_name, lesson_topics, learning_objectives) + "},"
    return lesson_plan
    


# In[37]:


test = ['{id: "lesson1.6", name: "Lesson 1.6", topics: "Rational Expressions", allowRecyle: false, learningObjectives: {simplifying_complex_rational_expressions: 0.95, rational_expressions: 0.95, } }', '{id: "lesson1.6", name: "Lesson 1.6", topics: "Rational Expressions", allowRecyle: false, learningObjectives: {simplifying_complex_rational_expressions: 0.95, rational_expressions: 0.95, } }']
test 


# In[38]:


print(create_bkt_params('simplifying_complex_rational_expressions'))


# In[39]:


bkt_params = [create_bkt_params('simplifying_complex_rational_expressions'), create_bkt_params('rational_expressions')]


# In[40]:


def finish_lesson_plan(lesson_plan, file):
    lesson_to_write = "var lessonPlans = ["
    for lesson in lesson_plan:
        lesson_to_write += lesson
    lesson_to_write += "]; export default lessonPlans;"
    file.write(lesson_to_write)
    file.close()

def finish_bkt_params(bkt_params, file):
    bkt_params_string = "var bktParams = {"
    for param in bkt_params:
        bkt_params_string += param
    bkt_params_string += "}; export {bktParams};"
    file.write(bkt_params_string)
    file.close()


# In[41]:


def create_total(sheet_names, default_path):
    open(default_path + "/stepfiles.txt", "x")
    lesson_to_skills = {}
    lesson_plan = []
    bkt_params = []
    for sheet in sheet_names:
        skills = process_sheet(sheet, default_path)
        lesson_plan.append(create_lesson_plan(sheet, skills))
        for skill in skills:
            bkt_params.append(create_bkt_params(skill))
    
    open("lessonPlans.js", "x")
    file = open("lessonPlans.js", "a")
    finish_lesson_plan(lesson_plan, file)
    
    open("bktParams.js", "x")
    file = open("bktParams.js", "a")
    finish_bkt_params(bkt_params, file)
    
    file.close()
        
    
        
    
        


# In[42]:


"a".replace("a", "b")


# In[ ]:





# In[43]:


def process_sheet(sheet_name, default_path):
    worksheet = book.worksheet(sheet_name) 
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0]) 
    ##Only keep columns we need 
    df = df[["Problem Name","Row Type","Title","Body Text","Answer", "answerType", "HintID", "Dependency", "mcChoices", "Images (space delimited)","Parent","OER src","openstax KC", "KC","Taxonomy"]]
    
    df = df.astype(str)
    df.replace('', 0.0, inplace = True)
    df["Body Text"] = df["Body Text"].str.replace("\"", "\\\"")
    df["Title"] = df["Title"].str.replace("\"", 
    m["\\\"")
    
    
    skillModelJS_lines = []
    skills = []
    skills_unformatted = []
    skillModelJS_path = os.path.join("","skillModel.js")
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
        if type(problem_row["Images (space delimited)"]) != float:
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


# In[44]:


preprocess_text_to_latex("(z*sqrt(2))**5/(z*sqrt(2))")


# In[46]:


sheet_names = ["3.1 Functions and Function Notation", "3.2 Domain and Range", "3.3 Rates of Change and Behavior of Graphs", "3.4 Composition of Functions", "3.5 Transformation of Functions", "3.6 Absolute Value Functions", "3.7 Inverse Functions", "blockchain", "1.1 Real Numbers", "1.2 Exponents and Scientific Notation", "1.3 Radicals and Rational Exponents", "1.4 Polynomials", "1.5 Factoring Polynomials", "1.6 Rational Expressions", "2.1 The Rectangular Coordinate Systems and Graph  ", "2.2 Linear Equations in One Variable", "2.3 Models and Applications", "2.4 Complex Numbers", "2.5 Quadratic Equations", "2.7 Linear Inequalities and Absolute Value Inequalities"]
default_path = "new2"
create_total(sheet_names, default_path)


# sheet_names = ["1.1 Real Numbers", "1.2 Exponents and Scientific Notation", "1.3 Radicals and Rational Exponents", "1.4 Polynomials", "1.5 Factoring Polynomials", "1.6 Rational Expressions"]
# default_path = "testing4"
# open(default_path + "/stepfiles.txt", "x")
# for sheet in sheet_names:
#     process_sheet(sheet, default_path)

# $\frac{a^m}{a^n}$
