import sys
import os
import pandas as pd
import time
import shutil
from process_sheet import process_sheet, get_all_url, get_sheet

def escape_quotes(name):
    return name.replace('"', r'\"').replace('“', r'\"').replace('”', r'\"')

def create_bkt_params(name):
    return "\"" + escape_quotes(name) + "\": {probMastery: 0.1, probTransit: 0.1, probSlip: 0.1, probGuess: 0.1},"


def create_lesson_plan(sheet, skills):
    lesson_number = sheet.split()[0]
    lesson_topics = " ".join(sheet.split()[1:])

    lesson_id = ("lesson" + lesson_number)
    lesson_name = "Lesson " + lesson_number
    learning_objectives = "{"
    if skills:
        for skill in skills:
            learning_objectives += "\"" + escape_quotes(skill) + "\": 0.85, "
    # strip the last comma
    if len(learning_objectives) > 1:
        learning_objectives = learning_objectives[:-2]
    learning_objectives += "}"

    lesson_plan = "{\"id\": " + "\"{0}\", \"name\": \"{1}\", \"topics\": \"{2}\", \"allowRecyle\": true, \"learningObjectives\": {3} ".format(lesson_id, lesson_name, lesson_topics, learning_objectives) + "},"
    return lesson_plan


def create_course_plan(course_name, lesson_plan):
    course_to_write = "{courseName: \"" + course_name + "\", " + "lessons: ["
    for lesson in lesson_plan:
        course_to_write += lesson
    course_to_write += "]},"
    return course_to_write

def finish_course_plan(courses, file):
    course_to_write = "var courses =  ["
    for course in courses:
        course_to_write += course
    course_to_write += "]; export default courses;"
    file.write(course_to_write)
    file.close()

def finish_bkt_params(bkt_params, file):
    bkt_params_string = "var bktParams = {"
    for param in bkt_params:
        bkt_params_string += param
    bkt_params_string += "}; export {bktParams};"
    file.write(bkt_params_string)
    file.close()


all_problem_names = []
conflict_names = []

def names_from_one_sheet(book, sheet_name):
    worksheet = book.worksheet(sheet_name)
    table = worksheet.get_all_values()
    try:
        df = pd.DataFrame(table[1:], columns=table[0])
        df = df[["Problem Name"]]
        df = df.astype(str)
        df.replace('', 0.0, inplace = True)
        df.replace(' ', 0.0, inplace = True)
        questions = [x for _, x in df.groupby(df['Problem Name'])]
        for question in questions:
            problem_name = question.iloc[0]['Problem Name']
            # skip empty rows
            if type(problem_name) != str:
                continue
            if problem_name in all_problem_names:
                conflict_names.append(problem_name)
            else:
                all_problem_names.append(problem_name)
    except:
        pass

def check_names_online():
    url_df = get_all_url()
    for index, row in url_df.iterrows():
        course_name, book_url = row['Book'], row['URL']
        book = get_sheet(book_url)
        sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
        for sheet in sheet_names:
            start = time.time()
            names_from_one_sheet(book, sheet)
            end = time.time()
            if end - start < 3:
                time.sleep(3 - (end - start))

def check_names_repeat():
    global all_problem_names
    global conflict_names
    count = 0
    success = False
    while count < 5 and not success:
        try:
            check_names_online()
            success = True
            count += 1
        except Exception:
            all_problem_names = []
            conflict_names = []
            count += 1
            time.sleep(20)
    if not success:
        raise Exception("Failed to read sheet names from google sheet. Try again later.")


def create_total(default_path, is_local, sheet_keys=None, sheet_names=None):
    '''if sheet_names is not provided, default to run all sheets'''
    global all_problem_names
    global conflict_names
    course_plan = []
    bkt_params = []
    skillModelJS_path = os.path.join("..","skillModel.js")
    editor_content_path = os.path.join("..", "Editor Content")
    validator_path = os.path.join("..", ".OpenStax Validator")
    if os.path.exists(skillModelJS_path):
        os.remove(skillModelJS_path)
    if os.path.isdir(default_path):
        shutil.rmtree(default_path)
    if os.path.isdir(editor_content_path):
        shutil.rmtree(editor_content_path)
    if os.path.isdir(validator_path):
        shutil.rmtree(validator_path)
    if is_local == 'local':
        excel_path = "../Excel/"
        for sheet_key in sheet_keys:
            lesson_plan = []
            course_name = sheet_key[:-5]
            if not sheet_names or len(sheet_keys) > 1:
                myexcel = pd.ExcelFile(excel_path + sheet_key)
                sheet_names = [tab for tab in myexcel.sheet_names if tab[:2] != '!!']
            for sheet in sheet_names:
                skills = process_sheet(sheet_key, sheet, default_path, is_local)
                lesson_plan.append(create_lesson_plan(sheet, skills))
                for skill in skills:
                    bkt_params.append(create_bkt_params(skill))
            course_plan.append(create_course_plan(course_name, lesson_plan))
    elif is_local == 'online':
        # checks for problem name conflicts. Conflicted names are stored in conflict_names in conflict_names.py

        # check_names_repeat()

        url_df = get_all_url()
        for index, row in url_df.iterrows():
            lesson_plan = []
            course_name, book_url = row['Book'], row['URL']
            book = get_sheet(book_url)
            sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
            for sheet in sheet_names:
                start = time.time()
                if sheet[:2] == '##':
                    skills = process_sheet(book_url, sheet, default_path, 'online','FALSE',
                                            validator_path=validator_path, course_name=course_name)
                else:
                    skills = process_sheet(book_url, sheet, default_path, 'online','TRUE',
                                            validator_path=validator_path, course_name=course_name)
                lesson_plan.append(create_lesson_plan(sheet, skills))
                if skills:
                    for skill in skills:
                        bkt_params.append(create_bkt_params(skill))
                end = time.time()
                if end - start < 4:
                    time.sleep(4 - (end - start))
            course_plan.append(create_course_plan(course_name, lesson_plan))

        # process editor sheet
        for index, row in url_df.iterrows():
            editor_url = row['Editor Sheet']
            if editor_url:
                editor_book = get_sheet(editor_url)
                sheet_names = [sheet.title for sheet in editor_book.worksheets() if sheet.title[:2] != '!!']
                # check name conflicts in editor sheet
                # for sheet in sheet_names:
                #     start = time.time()
                #     names_from_one_sheet(editor_book, sheet)
                #     end = time.time()
                #     if end - start < 3:
                #         time.sleep(3 - (end - start))
                for sheet in sheet_names:
                    start = time.time()
                    try:
                        if sheet[:2] == '##':
                            process_sheet(editor_url, sheet, editor_content_path, 'online','FALSE',
                                                validator_path=validator_path,editor=True,course_name="")
                        else:
                            process_sheet(editor_url, sheet, editor_content_path, 'online','TRUE',
                                                validator_path=validator_path,editor=True,course_name="")
                    except Exception as e:
                        print("Error in {}:".format(sheet), e)

                    end = time.time()
                    if end - start < 4:
                        time.sleep(4 - (end - start))



    # strip the last comma
    course_plan[-1] = course_plan[-1][:-1]

    # open("../lessonPlans.js", "x")
    file = open("../coursePlans.js", "w")
    finish_course_plan(course_plan, file)

    # open("../bktParams.js", "x")
    file = open("../bktParams.js", "w")
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