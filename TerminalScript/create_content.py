import json
import re

from process_text import preprocess_text_to_latex

def create_variabilization(variabilization):
    if variabilization:
        variabilization = re.sub('\s*', '', variabilization)
        var_list = variabilization.split("\n")
        var_str = ""
        for var in var_list:
            name, field = var.split(":")
            fields = field[1:-1].split(",")  #get rid of brackets
            var_str += name + ": ["
            for f in fields:
                var_str += "\"" + f + "\", "
            var_str = var_str[:-2]
            var_str += "], "
        var_str = "{" + var_str[:-2] + "}"
    else:
        var_str = "{}"
    return var_str

def create_problem_js(name,title,body,images=[],variabilization=''):
    if type(body) == float:
        body= ""
    for image in images:
        body += "\\n##{0}##".format(image)
    if type(title) == float:
        title = ""
    title, title_latex = preprocess_text_to_latex(title)
    body, body_latex = preprocess_text_to_latex(body)
    
    var_str = create_variabilization(variabilization)

    # contents = "import React from 'react'; import { InlineMath } from 'react-katex';" + "import steps from \"./{0}-index.js\"; const problem = ".format(name) + "{" + "id: \"{0}\", ".format(name)
    contents = "import steps from \"./{0}-index.js\"; const problem = ".format(name) + "{" + "id: \"{0}\", ".format(name)

    # if title_latex:
    #     contents += "title: <div> {0} </div>, ".format(title)
    # else:
    contents += "title: \"{0}\", ".format(title)
    # if body_latex:
    #     contents += "body: <div> {0} </div>, ".format(body)
    # else:
    contents += "body: \"{0}\", ".format(body)
    
    contents +=  "steps: steps, "
    contents += "variabilization: {0}".format(var_str)
    contents += "}; export { problem };"
    
    contents = re.sub("(\.js){2,}", ".js", contents) #To account for .js.js or .js.js.js
    
    return contents


def create_hint(step, hint_id, title, body, dependencies=0.0, images=[], subhints=[], hint_dic={}, variabilization=''):
    if type(body) == float:
        body = ""
    if type(title) == float:
        title = ""
    title, title_latex = preprocess_text_to_latex(title, True)
    body, body_latex = preprocess_text_to_latex(body, True)

    var_str = create_variabilization(variabilization)
    
    hint_id = step + "-" + hint_id
    for image in images:
        body += "\\n##{0}##".format(image)
    if type(dependencies) == str and dependencies != 'None':
        try:
            dependencies = json.dumps([hint_dic[hint_id] for hint_id in dependencies.split(",")])
        except Exception as e:
            print("Key error")
            print(step, hint_id, title, body)
            raise Exception("Hint key error")
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
    
    hint_obj += ", variabilization: {0}".format(var_str)

    hint_obj = "{" + hint_obj + "}"
    return hint_obj, hint_id


scaff_dic = {"mc": "string", "numeric": "TextBox", "algebra": "TextBox", "string": "string"}

def handle_answer_type(answer_type):
    if answer_type == "mc":
        return "string", "MultipleChoice"
    elif answer_type == "string":
        return answer_type, "TextBox"
    elif answer_type == "algebra" or answer_type == "algebraic" or answer_type == "numeric":
        return "arithmetic", "TextBox"
    elif type(answer_type) != str:
        raise Exception("Answer type is missing")
    else:
        raise Exception('Answer type not correct' + answer_type)


def create_scaffold(step, hint_id, title, body, answer_type, answer, mc_answers, dependencies=0.0, images="", subhints=[], hint_dic={}, variabilization=""):
    if type(body) == float:
        body = ""
    if type(title) == float:
        title = ""
    
    title, title_latex = preprocess_text_to_latex(title, True)
    body, body_latex = preprocess_text_to_latex(body, True)

    var_str = create_variabilization(variabilization)

    # getting rid of timestamp format for fractions
    try:
        if len(answer) > 8 and answer[-8:] == '00:00:00':
            li = re.split('-| ', answer)
            answer = str(int(li[1])) + '/' + str(int(li[2]))
    except TypeError:
        raise Exception("Scaffold answer missing")
    
    scaffold_id = step + "-" + hint_id
    for image in images:
        body += "\\n##{0}##".format(image)

    if type(dependencies) == str and dependencies != 'None':
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
        mc_answers = json.dumps([preprocess_text_to_latex(mc_answer, True, True)[0] for mc_answer in mc_answers.split("|") if mc_answer])
        answer = json.dumps(preprocess_text_to_latex(answer, True, True)[0])
        scaff_ans = "[" + str(answer) + "]"
    
    
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

    scaff_obj += ", variabilization: {0}".format(var_str)

    scaff_obj = "{" + scaff_obj + "}"
    return scaff_obj, scaffold_id


def create_step(name, title, body, answer, answer_type, number, choices="", image="", variabilization=""):
    step_id = name + chr(ord('a')+number-1)
    if type(body) == float:
        body = ""
    if type(title) == float:
        title = ""
    
    title, title_latex = preprocess_text_to_latex(title)
    body, body_latex = preprocess_text_to_latex(body)

    var_str = create_variabilization(variabilization)

    # getting rid of timestamp format for fractions
    try:
        if len(answer) > 8 and answer[-8:] == '00:00:00':
            li = re.split('-| ', answer)
            answer = str(int(li[1])) + '/' + str(int(li[2]))
    except TypeError:
        raise Exception("Step answer missing")

    new_answer, answer_latex = preprocess_text_to_latex(answer)

    for img in image:
        body += "##" + img + "## "
    if choices:
        choices = json.dumps([preprocess_text_to_latex(mc_answer, True, True)[0] for mc_answer in choices.split("|") if mc_answer])
        answer = preprocess_text_to_latex(answer, tutoring=True, stepAns=True)[0]
    
    answer_type, problem_type = handle_answer_type(answer_type)
    if answer_type == "arithmetic":
        answer = re.sub("\*\*", "^", answer)

    step =  "import hints from \"./{0}-index.js\"; const step = ".format(step_id) + "{" + "id: \"{0}\", stepAnswer: [\"{1}\"], problemType: \"{2}\"".format(step_id, answer, problem_type)
    step += ", stepTitle: \"{0}\"".format(title)
    step += ", stepBody: \"{0}\"".format(body)
    
    if answer_latex:
        ", answerLatex: \"{0}\"".format(new_answer)
    
    
    
    if type(choices) == str:
        step += ", choices: " + str(choices)
    step += ", answerType: \"{0}\", hints: hints".format(answer_type)
    step += ", variabilization: {0}".format(var_str)
    step += "}; export {step};"

    return step
