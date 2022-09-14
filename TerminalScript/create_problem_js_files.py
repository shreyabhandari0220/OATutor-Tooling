import re
import sys
import requests
import numpy as np
from urllib.parse import urlparse

from create_dir import *
from create_content import *


fake_headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/96.0.4664.93 Safari/537.36',
    'upgrade-insecure-requests': '1',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
              '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9'
}


def create_default_pathway(tutoring):
    return json.dumps(tutoring, indent=4)


def save_images(images, path, num):
    # images is a string of urls separated by spaces
    if type(images) != str:
        return "", 0
    images = images.split(" ")
    names = []
    for i in images:
        num += 1
        name = "figure" + str(num) + ".gif"
        names.append(name)
        i = re.sub(r"https://imgur\.com/([\d\w]+)", r"https://i.imgur.com/\g<1>.png", i)
        try:
            r = requests.get(i, headers=fake_headers)
        except (requests.exceptions.ConnectionError, ConnectionResetError) as exc:
            # could be because the requested service is blocking our ip, try again with a free proxy service
            parse_result = urlparse(i)
            if bool(parse_result.query):
                print("image query params are not supported by the proxy. {}".format(i))
                # query params are not supported :(
                sys.exit(1)
            new_i = "https://cdn.statically.io/img/{}{}".format(parse_result.netloc, parse_result.path)
            print("trying to proxy image {} with {}".format(i, new_i))
            r = requests.get(new_i, headers=fake_headers)
        except BaseException:
            print("error saving image: {}".format(i))
            sys.exit(1)
        with open(path + "/" + name, 'wb') as outfile:
            outfile.write(r.content)
    return names, num


def write_step_json(default_path, problem_name, row, step_count, tutoring, skills, images, figure_path, 
                default_pathway_json_path, path, verbosity, variabilization, latex, result_problems):
    if step_count > 0:
        # writes to step
        to_write = create_default_pathway(tutoring)
        default_pathway = open(default_pathway_json_path, "w", encoding="utf-8")
        default_pathway.write(to_write)
        default_pathway.close()
    tutoring = []
    step_count += 1
    # sets the current step name and path
    current_step_name = problem_name + chr(96 + step_count)
    step_file = open(default_path + "/stepfiles.txt", "a+", encoding="utf-8")
    step_file.writelines("    " + current_step_name + ": " + "[\"realnumber\"], \n")
    # creates step js files
    _, step_reg_json_path, default_pathway_json_path = create_step_dir(current_step_name, path + "/steps", verbosity)
    step_file = open(step_reg_json_path, "w", encoding="utf-8")
    step_images = ""
    # checks images and creates the figures path if necessary
    if type(row["Images (space delimited)"]) == str:
        if not images:
            figure_path = create_fig_dir(path)
        step_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
        images += num
    choices = type(row["mcChoices"]) == str and row["mcChoices"]
    if variabilization:
        step_file.write(
            create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"],
                        step_count, choices, step_images, var_str=row["Variabilization"],
                        latex=latex, verbosity=verbosity))
    else:
        step_file.write(
            create_step(problem_name, row['Title'], row["Body Text"], row["Answer"], row["answerType"],
                        step_count, choices, step_images, latex=latex, verbosity=verbosity))
    step_file.close()

    skill = "    {0}: [{1}],\n".format(current_step_name, result_problems)
    skills.append(skill)

    return step_count, current_step_name, tutoring, skills, images, figure_path, default_pathway_json_path


def write_subhint_json(row, row_type, current_step_name, current_subhints, tutoring, previous_tutor, 
                    previous_images, images, path, figure_path, hint_dic, verbosity, variabilization, latex):
    hint_images = ""
    if type(row["Images (space delimited)"]) == str and type(
            row["Images (space delimited)"]) != np.float64:
        if not images:
            figure_path = create_fig_dir(path)
        hint_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
        images += num
    hint_id = row['Parent'] + "-" + row['HintID']
    if row_type == 'hint':
        if variabilization:
            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"],
                                                row["Body Text"], row["Dependency"], hint_images,
                                                hint_dic=hint_dic, var_str=row["Variabilization"],
                                                latex=latex, verbosity=verbosity)
        else:
            subhint, subhint_id = create_hint(current_step_name, hint_id, row["Title"],
                                                row["Body Text"], row["Dependency"], hint_images,
                                                hint_dic=hint_dic, latex=latex, verbosity=verbosity)
    else:
        if variabilization:
            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"],
                                                    row["Body Text"], row["answerType"], row["Answer"],
                                                    row["mcChoices"], row["Dependency"], hint_images,
                                                    hint_dic=hint_dic,
                                                    var_str=row["Variabilization"], latex=latex,
                                                    verbosity=verbosity)
        else:
            subhint, subhint_id = create_scaffold(current_step_name, hint_id, row["Title"],
                                                    row["Body Text"], row["answerType"], row["Answer"],
                                                    row["mcChoices"], row["Dependency"], hint_images,
                                                    hint_dic=hint_dic, latex=latex, verbosity=verbosity)
    hint_dic[row["HintID"]] = subhint_id
    current_subhints.append(subhint)
    tutoring.pop()
    if previous_tutor['Row Type'] == 'hint':
        if variabilization:
            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"],
                                            previous_tutor["Title"], previous_tutor["Body Text"],
                                            previous_tutor["Dependency"], previous_images,
                                            subhints=current_subhints, hint_dic=hint_dic,
                                            var_str=previous_tutor["Variabilization"],
                                            latex=latex, verbosity=verbosity)
        else:
            previous, hint_id = create_hint(current_step_name, previous_tutor["HintID"],
                                            previous_tutor["Title"], previous_tutor["Body Text"],
                                            previous_tutor["Dependency"], previous_images,
                                            subhints=current_subhints, hint_dic=hint_dic, latex=latex,
                                            verbosity=verbosity)
    else:
        if variabilization:
            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"],
                                                previous_tutor["Title"], previous_tutor["Body Text"],
                                                previous_tutor["answerType"], previous_tutor["Answer"],
                                                previous_tutor["mcChoices"],
                                                previous_tutor["Dependency"], previous_images,
                                                subhints=current_subhints, hint_dic=hint_dic,
                                                var_str=previous_tutor["Variabilization"],
                                                latex=latex, verbosity=verbosity)
        else:
            previous, hint_id = create_scaffold(current_step_name, previous_tutor["HintID"],
                                                previous_tutor["Title"], previous_tutor["Body Text"],
                                                previous_tutor["answerType"], previous_tutor["Answer"],
                                                previous_tutor["mcChoices"],
                                                previous_tutor["Dependency"], previous_images,
                                                subhints=current_subhints, hint_dic=hint_dic,
                                                latex=latex, verbosity=verbosity)
    tutoring.append(previous)

    return images, hint_dic, current_subhints, tutoring, figure_path


def write_hint_json(row, current_step_name, tutoring, images, figure_path, path, hint_dic, verbosity, variabilization, latex):
    current_subhints = []
    hint_images = ""
    if type(row["Images (space delimited)"]) == str:
        if not images:
            figure_path = create_fig_dir(path)
        hint_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
        images += num
    if variabilization:
        hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"],
                                    row["Body Text"], row["Dependency"], hint_images,
                                    hint_dic=hint_dic, var_str=row["Variabilization"],
                                    latex=latex, verbosity=verbosity)
    else:
        hint, full_id = create_hint(current_step_name, row["HintID"], row["Title"],
                                    row["Body Text"], row["Dependency"], hint_images,
                                    hint_dic=hint_dic, latex=latex, verbosity=verbosity)
    hint_dic[row["HintID"]] = full_id
    tutoring.append(hint)
    previous_tutor = row
    previous_images = hint_images

    return images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path


def write_scaffold_json(row, current_step_name, tutoring, images, figure_path, path, hint_dic, verbosity, variabilization, latex):
    current_subhints = []
    scaff_images = ""
    if type(row["Images (space delimited)"]) == str:
        if not images:
            figure_path = create_fig_dir(path)
        scaff_images, num = save_images(row["Images (space delimited)"], figure_path, int(images))
        images += num
    if variabilization:
        scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"],
                                            row["Body Text"], row["answerType"], row["Answer"],
                                            row["mcChoices"], row["Dependency"], scaff_images,
                                            hint_dic=hint_dic, var_str=row["Variabilization"],
                                            latex=latex, verbosity=verbosity)
    else:
        scaff, full_id = create_scaffold(current_step_name, row["HintID"], row["Title"],
                                            row["Body Text"], row["answerType"], row["Answer"],
                                            row["mcChoices"], row["Dependency"], scaff_images,
                                            hint_dic=hint_dic, latex=latex, verbosity=verbosity)
    hint_dic[row["HintID"]] = full_id
    tutoring.append(scaff)
    previous_tutor = row
    previous_images = scaff_images

    return images, hint_dic, current_subhints, tutoring, previous_tutor, previous_images, figure_path


def write_problem_json(problem_row, problem_name, problem_json_path, course_name, sheet_name, images, path, figure_path, verbosity, variabilization, latex):
    problem_images = ""
    if type(problem_row["Images (space delimited)"]) == str:
        if not images:
            figure_path = create_fig_dir(path)
        problem_images, num = save_images(problem_row["Images (space delimited)"], figure_path, int(images))
        images += num
    if variabilization:
        prob_js = create_problem_json(problem_name, problem_row["Title"], problem_row["Body Text"],
                                    problem_row["OER src"], problem_images,
                                    var_str=problem_row["Variabilization"], latex=latex,
                                    verbosity=verbosity, course_name=course_name, sheet_name=sheet_name)
    else:
        prob_js = create_problem_json(problem_name, problem_row["Title"], problem_row["Body Text"],
                                    problem_row["OER src"], problem_images, latex=latex, verbosity=verbosity,
                                    course_name=course_name, sheet_name=sheet_name)
    file = open(problem_json_path, "w", encoding="utf-8")
    file.write(prob_js)
    file.close()

