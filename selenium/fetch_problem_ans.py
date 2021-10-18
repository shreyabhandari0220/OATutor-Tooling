import os
import sys
from os.path import dirname
import re

CURRENT_PATH = os.getcwd()
CONTENT_PATH = os.path.join(dirname(CURRENT_PATH), 'OpenStax Content')

def get_all_content_filename(content_path=CONTENT_PATH):
    """
    Returns a list of all directory names under "OpenStax Content"
    Ex. ['quadratic17', 'IneqApp2', 'line14', 'partfrac26', 'uni27',...]
    """
    return [direc for direc in os.listdir(content_path) if direc != "stepfiles.txt"]

def fetch_problem_ans_info(problem_name, verbose=False):
    """
    input: problem name (ex. real1)
    output: list of pairs of [step answer, step type]
    """
    if verbose:
        print("testing {}".format(problem_name))
        
    all_steps_dir = os.path.join(CONTENT_PATH, problem_name, "steps")
    step_name_list = sorted([x for x in next(os.walk(all_steps_dir))][1]) # gives a list of subdirectory names
    problem_info = []

    for step_name in step_name_list:
        step_path = os.path.join(all_steps_dir, step_name, step_name + '.js')
        with open(step_path) as step_file:
            data = step_file.read()
            step_type = re.search('problemType:\s*\"(.*)\",\s*stepTitle:', data).group(1)
            step_ans = re.search('stepAnswer:\s*\[\"(.*)\"\],\s*problemType:', data).group(1)
            if step_type == "TextBox":
                step_type += " " + re.search('answerType:\s*\"(.*)\",\s*hints:', data).group(1)
            # print(data)
            # print(step_ans)
            if "@" in step_ans:
                variabilization = re.search('variabilization: {([^}]+)}', data).group(1)
                var_dict = dict(re.findall('([^,:\s]+)+:\s(\[[^]]+\])', variabilization))
                for k, v in var_dict.items():
                    var_dict[k] = re.search("\[\"(\w+)\",", v).group(1)
                step_ans = re.sub("@{(\w+)}", lambda m: var_dict.get(m.group(1), m.group(1)), step_ans)
            step_ans = step_ans.replace('\\\\', '\\')
            problem_info.append([step_ans, step_type])
    if verbose:
        print(problem_info)
    return problem_info


if __name__ == '__main__':
    problem_name = sys.argv[1]
    if len(sys.argv) == 3:
        verbosity = eval(sys.argv[2])
    else:
        verbosity = False
    print(fetch_problem_ans_info(problem_name, verbose=verbosity))
