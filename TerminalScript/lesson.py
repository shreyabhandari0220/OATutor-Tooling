import sys
import pandas as pd
from process_sheet import process_sheet, get_all_url, get_sheet

def create_bkt_params(name):
    return "\"" + name + "\": {probMastery: 0.1, probTransit: 0.1, probSlip: 0.1, probGuess: 0.1},"


def create_lesson_plan(sheet, skills):
    lesson_number = sheet.split()[0]
    lesson_topics = " ".join(sheet.split()[1:])
    
    lesson_id = ("lesson" + lesson_number)
    lesson_name = "Lesson " + lesson_number
    learning_objectives = "{"
    for skill in skills:
        learning_objectives += "\"" + skill + "\": 0.95, "
    # strip the last comma
    if len(learning_objectives) > 1:
        learning_objectives = learning_objectives[:-2]
    learning_objectives += "}"
    
    lesson_plan = "{\"id\": " + "\"{0}\", \"name\": \"{1}\", \"topics\": \"{2}\", \"allowRecyle\": false, \"learningObjectives\": {3} ".format(lesson_id, lesson_name, lesson_topics, learning_objectives) + "},"
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

def names_from_one_sheet(sheet_key, sheet_name):
    book = get_sheet(sheet_key)
    worksheet = book.worksheet(sheet_name) 
    table = worksheet.get_all_values()
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
        problem_row = question.iloc[0]
        if problem_name in all_problem_names:
            conflict_names.append(problem_name)
        else:
            all_problem_names.append(problem_name)

def check_names_online():
    url_df = get_all_url()
    for index, row in url_df.iterrows():
        course_name, book_url, latex = row['Book'], row['URL'], row['Latex']
        book = get_sheet(book_url)
        sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
        for sheet in sheet_names:
            names_from_one_sheet(book_url, sheet)

def create_total(default_path, is_local, sheet_keys=None, sheet_names=None):
    '''if sheet_names is not provided, default to run all sheets'''
    course_plan = []
    bkt_params = []
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
        check_names_online()
        url_df = get_all_url()
        for index, row in url_df.iterrows():
            lesson_plan = []
            course_name, book_url, latex = row['Book'], row['URL'], row['Latex']
            book = get_sheet(book_url)
            sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
            for sheet in sheet_names:
                skills = process_sheet(book_url, sheet, default_path, 'online',latex,conflict_names=conflict_names)
                lesson_plan.append(create_lesson_plan(sheet, skills))
                for skill in skills:
                    bkt_params.append(create_bkt_params(skill))
            course_plan.append(create_course_plan(course_name, lesson_plan))
    # strip the last comma
    course_plan[-1] = course_plan[-1][:-1]

    # open("../lessonPlans1.js", "x")
    file = open("../coursePlans1.js", "a")
    finish_course_plan(course_plan, file)
    
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