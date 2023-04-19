import os
import hashlib
import shutil

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

    # remove old content
    if os.path.isdir(target):
        shutil.rmtree(target)

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

def rename_problem_dir(sheet_name, name, path):
    # handle namespace collision
    name = 'a' + hashlib.sha1(sheet_name.encode('utf-8')).hexdigest()[:6] + name
    target = path + "/" + name

    # rename old content
    if os.path.isdir(target):
        new_target = path + "/." + name
        os.makedirs(new_target)
        for file in os.listdir(target):
            shutil.move(os.path.join(target, file), new_target)
        return new_target
    else:
        return ""
