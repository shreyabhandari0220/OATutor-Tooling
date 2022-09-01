import os
import sys
from os.path import dirname
import re
import ast

from problem import *

CURRENT_PATH = os.getcwd()
CONTENT_PATH = os.path.join(dirname(CURRENT_PATH), 'OpenStax Content')

def get_all_content_filename(content_path=CONTENT_PATH):
    """
    Returns a list of all directory names under "OpenStax Content"
    Ex. ['quadratic17', 'IneqApp2', 'line14', 'partfrac26', 'uni27',...]
    """
    return [direc for direc in os.listdir(content_path) if direc != "stepfiles.txt" and direc != ".DS_Store"]

def process_hint_answer(hint_text):
    hint_list = hint_text[:].split("}, {")
    hint_answers = []
    for hint in hint_list:
        if not re.search(", type: \"(\w+)\"", hint):
            break
        if not re.search("id: \"a[^-]+\-[hs]\d+(?!\-)\"", hint):
            continue
        hint_type = re.search(", type: \"(\w+)\"", hint).group(1)
        if hint_type == "hint":
            hint_answers.append(hint_type)
        elif hint_type == "scaffold":
            scaf_type = re.search('problemType:\s*\"(.*?)\",\s*answerType:', hint).group(1)
            scaf_ans = re.search('hintAnswer:\s*\[\"(.*?)\"\],\s*dependencies:', hint).group(1)
            scaf_ans = scaf_ans.replace('\\\\', '\\')
            if scaf_type == "TextBox":
                scaf_type += " " + re.search('answerType:\s*\"(.*?)\",\s*hintAnswer:', hint).group(1)
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
    problem_path = os.path.join(CONTENT_PATH, problem_name, problem_name + '.js')
    with open(problem_path) as problem_file:
        data = problem_file.read()
        try:
            book_name = re.search(",\scourseName:\s\"([^\"]+)\"", data).group(1)
        except AttributeError:
            book_name = ""
        
    # fetch ans and type
    all_steps_dir = os.path.join(CONTENT_PATH, problem_name, "steps")
    step_name_list = sorted([x for x in next(os.walk(all_steps_dir))][1]) # gives a list of subdirectory names
    problem_info = []
    step_obj_list = []

    for step_name in step_name_list:

        # fetch step type and answer
        step_path = os.path.join(all_steps_dir, step_name, step_name + '.js')
        with open(step_path) as step_file:
            data = step_file.read()
            step_type = re.search('problemType:\s*\"(.*)\",\s*stepTitle:', data).group(1)
            step_ans = re.search('stepAnswer:\s*\[\"(.*)\"\],\s*problemType:', data).group(1)
            if step_type == "TextBox":
                step_type += " " + re.search('answerType:\s*\"(.*)\",\s*hints:', data).group(1)


            step_ans = re.sub("(\d)\{10\}\^([\d\w\{])", "\g<1>*{10}^\g<2>", step_ans)
            if re.search("\}\^", step_ans):
                target_idx = re.search("\}\^", step_ans).start()
                idx = find_matching(step_ans, "}", target_idx)
                step_ans = step_ans[:idx] + "\\\\left(" + step_ans[idx:target_idx+1] + "\\\\right)" + step_ans[target_idx+1:]


            if "@" in step_ans:
                variabilization = re.search('variabilization: {([^}]+)}', data).group(1)
                var_dict = dict(re.findall('([^,:\s]+)+:\s(\[[^]]+\])', variabilization))
                for k, v in var_dict.items():
                    var_dict[k] = ast.literal_eval(v)
                ans_lst = []
                for i in range(len(list(var_dict.values())[0])):
                    ans_lst.append(re.sub("@{(\w+)}", lambda m: var_dict.get(m.group(1))[i], step_ans).replace('\\\\', '\\'))
                step_ans = ans_lst # list of all possible answers
            else:
                step_ans = step_ans.replace('\\\\', '\\')
            problem_info.append([step_ans, step_type])

        # fetch hint and scaffold answer
        hint_path = os.path.join(all_steps_dir, step_name, "tutoring", step_name + "DefaultPathway.js")
        with open(hint_path) as hint_file:
            hint_text = hint_file.read()
            hint_info_list = process_hint_answer(hint_text)

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
