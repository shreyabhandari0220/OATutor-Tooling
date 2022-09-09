import os
import sys
from os.path import dirname
import re
import ast
import json

from problem import *

CURRENT_PATH = os.getcwd()
CONTENT_PATH = os.path.join(dirname(CURRENT_PATH), 'OpenStax Content')

def get_all_content_filename(content_path=CONTENT_PATH):
    """
    Returns a list of all directory names under "OpenStax Content"
    Ex. ['quadratic17', 'IneqApp2', 'line14', 'partfrac26', 'uni27',...]
    """
    return [direc for direc in os.listdir(content_path) if direc != "stepfiles.txt" and direc != ".DS_Store"]

def process_hint_answer(hint_list):
    hint_answers = []
    for hint in hint_list:
        hint_type = hint["type"]
        if hint_type == "hint":
            hint_answers.append(hint_type)
        elif hint_type == "scaffold":
            scaf_type = hint["problemType"]
            scaf_ans = hint["hintAnswer"][0]
            if scaf_type == "TextBox":
                scaf_type += " " + hint["answerType"]
            hint_answers.append([scaf_ans, scaf_type])
    return hint_answers

def find_matching(word, char, idx):
    match = {'(': ')', '{': '}', '[': ']', '\\left(': '\\right)', ')': '(', '}': '{', ']': '[', '\\right)': '\\left('}
    l_count = r_count = 0
    idx -= 1
    while idx >= 0:
        if word[idx] == char:
            l_count += 1
        elif word[idx] == match[char]:
            r_count += 1
        if r_count > l_count:
            return idx
        idx -= 1
    raise Exception("unmatched" + char)

def fetch_problem_ans_info(problem_name, verbose=False):
    """
    input: problem name (ex. real1)
    output: list of pairs of [step answer, step type]
    """
    if verbose:
        print("testing {}".format(problem_name))
    
    # fetch book name
    problem_path = os.path.join(CONTENT_PATH, problem_name, problem_name + '.json')
    with open(problem_path) as problem_file:
        data = json.load(problem_file)
        try:
            book_name = data["courseName"]
        except KeyError:
            book_name = ""
        
    # fetch ans and type
    all_steps_dir = os.path.join(CONTENT_PATH, problem_name, "steps")
    step_name_list = sorted([x for x in next(os.walk(all_steps_dir))][1]) # gives a list of subdirectory names
    problem_info = []
    step_obj_list = []

    for step_name in step_name_list:

        # fetch step type and answer
        step_path = os.path.join(all_steps_dir, step_name, step_name + '.json')
        with open(step_path) as step_file:
            data = json.load(step_file)
            step_type = data["problemType"]
            step_ans = data["stepAnswer"][0]
            if step_type == "TextBox":
                step_type += " " + data["answerType"]

            step_ans = re.sub("(\d)\{10\}\^([\d\w\{])", "\g<1>*{10}^\g<2>", step_ans)
            if re.search("\}\^", step_ans):
                target_idx = re.search("\}\^", step_ans).start()
                idx = find_matching(step_ans, "}", target_idx)
                step_ans = step_ans[:idx] + "\\\\left(" + step_ans[idx:target_idx+1] + "\\\\right)" + step_ans[target_idx+1:]


            if "@" in step_ans:
                var_dict = data["variabilization"]
                ans_lst = []
                for i in range(len(list(var_dict.values())[0])):
                    ans_lst.append(re.sub("@{(\w+)}", lambda m: var_dict.get(m.group(1))[i], step_ans))
                step_ans = ans_lst # list of all possible answers

            problem_info.append([step_ans, step_type])

        # fetch hint and scaffold answer
        hint_path = os.path.join(all_steps_dir, step_name, "tutoring", step_name + "DefaultPathway.json")
        with open(hint_path) as hint_file:
            hint_data = json.load(hint_file)
            hint_info_list = process_hint_answer(hint_data)

        step = Step(step_name, step_ans, step_type, hint_info_list)
        step_obj_list.append(step)
    
    problem = Problem(book_name, problem_name, step_obj_list)

    # if verbose:
    #     print(book_name, problem_info)

    return problem


if __name__ == '__main__':
    problem_name = sys.argv[1]
    if len(sys.argv) == 3:
        verbosity = eval(sys.argv[2])
    else:
        verbosity = False
    print(fetch_problem_ans_info(problem_name, verbose=verbosity))
