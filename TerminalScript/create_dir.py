import os
import hashlib

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def create_problem_dir(sheet_name, name, path, verbosity):
    #creates directory for problem
    if verbosity:
        print(path, name)
    # handle namespace collision
    tailing = 1
    case = False
    name = 'a' + hashlib.sha1(sheet_name.encode('utf-8')).hexdigest()[:6] + name
    target = path + "/" + name

    # most likely will not use this, but this is an additional catch for namespace error
    if os.path.exists(target):
        target = path + "/b" + str(tailing) + name
        case = True 
    while os.path.exists(target):
        case = True
        tailing += 1
        target = path + "/b" + str(tailing) + name
    if case:
        name = "b" + str(tailing) + name

    os.makedirs(target)
    os.mkdir(target + "/steps")
    problem_json_path = target + "/" + name+".json"
    open(problem_json_path, "x")
    return name, target, problem_json_path

def create_fig_dir(path):
    figures = path+"/figures"
    os.mkdir(figures)
    return figures

def create_step_dir(name, path, verbosity):
    target = path + "/" + name
    os.mkdir(target)
    os.mkdir(target + "/tutoring")
    step_reg_json_path = target + "/" + name+".json"
    default_pathway = target + "/tutoring/" + name + "DefaultPathway.json"
    if verbosity:
        print("This is the pathway for " + name, default_pathway)
    open(step_reg_json_path, "x")
    open(default_pathway,"x")
    return target, step_reg_json_path, default_pathway

def create_validator_dir(name, path):
    target = path + "/" + name
    # os.makedirs(target)
    return target