import os
import hashlib

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def create_problem_dir(sheet_name, name, path, verbosity, conflict_names):
    #creates directory for problem
    if verbosity:
        print(path, name)
    # handle namespace collision
    tailing = 1
    case = False
    if name in conflict_names:
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
    problem_js = target + "/" + name+".js"
    open(problem_js, "x")
    return name, target, problem_js

def create_fig_dir(path):
    figures = path+"/figures"
    os.mkdir(figures)
    return figures

def create_step_dir(name, path, verbosity):
    target = path + "/" + name
    os.mkdir(target)
    os.mkdir(target + "/tutoring")
    reg_js = target + "/" + name+".js"
    default_pathway = target + "/tutoring/" + name + "DefaultPathway.js"
    if verbosity:
        print("This is the pathway for " + name, default_pathway)
    open(reg_js, "x")
    open(default_pathway,"x")
    return target, reg_js, default_pathway

def create_validator_dir(name, path):
    target = path + "/" + name
    os.makedirs(target)
    return target