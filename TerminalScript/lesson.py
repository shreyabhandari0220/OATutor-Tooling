import sys
import pandas as pd
from process_sheet import process_sheet

def create_bkt_params(name):
    return "\"" + name + "\": {probMastery: 0.1, probTransit: 0.1, probSlip: 0.1, probGuess: 0.1},"


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


def create_total(sheet_keys, default_path, is_local, sheet_names=None):
    ''' if sheet_names is not provided, default to run all sheets'''
    # open(default_path + "/stepfiles.txt", "x")
    lesson_to_skills = {}
    lesson_plan = []
    bkt_params = []
    excel_path = "../Excel/"
    for sheet_key in sheet_keys:
        if not sheet_names or len(sheet_keys) > 1:
            myexcel = pd.ExcelFile(excel_path + sheet_key)
            sheet_names = [tab for tab in myexcel.sheet_names if tab[:2] != '!!']
        for sheet in sheet_names:
            skills = process_sheet(sheet_key, sheet, default_path, is_local)
            lesson_plan.append(create_lesson_plan(sheet, skills))
            for skill in skills:
                bkt_params.append(create_bkt_params(skill))

    # open("../lessonPlans1.js", "x")
    file = open("../lessonPlans1.js", "a")
    finish_lesson_plan(lesson_plan, file)
    
    # open("../bktParams1.js", "x")
    file = open("../bktParams1.js", "a")
    finish_bkt_params(bkt_params, file)
    
    file.close()

if __name__ == '__main__':
    # when calling:
    # if stored locally: python3 final.py "local" <filename> <sheet_names>
    # if store on google sheet: python3 final.py "online" <url> <sheet_names>
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_names = sys.argv[3:]
    create_total(sheet_key, sheet_names, '../OpenStax Content', is_local)