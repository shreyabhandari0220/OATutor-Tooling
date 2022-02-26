import sys
import os
import pandas as pd
import time
import shutil
from process_sheet import process_sheet, get_all_url, get_sheet
import json


def create_bkt_params(name):
    bkt_params = {
        name: {
            "probMastery": 0.1,
            "probTransit": 0.1,
            "probSlip": 0.1,
            "probGuess": 0.1
        }
    }

    return bkt_params


def create_lesson_plan(sheet, skills):
    lesson_number = sheet.split()[0]
    lesson_topics = " ".join(sheet.split()[1:])

    lesson_id = ("lesson" + lesson_number)
    lesson_name = ("Lesson " + lesson_number)

    lesson_plan = {
        "id": lesson_id,
        "name": lesson_name,
        "topics": lesson_topics,
        "allowRecycle": True,
        "learningObjectives": dict(zip(skills, [0.85 for _ in skills]))
    }

    return lesson_plan


def create_course_plan(course_name, lesson_plan):
    if not lesson_plan:
        lesson_plan = []

    course_plan = {
        "courseName": course_name,
        "lessons": lesson_plan
    }

    return course_plan


def finish_course_plan(courses, file):
    course_to_write = "const courses="
    course_to_write += json.dumps(courses, separators=(',', ':'))
    course_to_write += ";export default courses"
    file.write(course_to_write)
    file.close()


def finish_bkt_params(bkt_params, file):
    bkt_params_string = "const bktParams="
    bkt_params_string += json.dumps(bkt_params, separators=(',', ':'))
    bkt_params_string += ";export {bktParams}"
    file.write(bkt_params_string)
    file.close()


def create_total(default_path, is_local, sheet_keys=None, sheet_names=None):
    """if sheet_names is not provided, default to run all sheets"""
    course_plan = []
    bkt_params = {}

    skill_model_path = os.path.join("..", "skillModel.js")
    editor_content_path = os.path.join("..", "Editor Content")
    validator_path = os.path.join("..", ".OpenStax Validator")
    if os.path.exists(skill_model_path):
        os.remove(skill_model_path)
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
                if not skills:
                    skills = []
                skills.sort()
                lesson_plan.append(create_lesson_plan(sheet, skills))
                for skill in skills:
                    bkt_params.update(create_bkt_params(skill))
            course_plan.append(create_course_plan(course_name, lesson_plan))
    elif is_local == 'online':
        url_df = get_all_url()
        for index, row in url_df.iterrows():
            lesson_plan = []
            course_name, book_url = row['Book'], row['URL']
            book = get_sheet(book_url)
            sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
            for sheet in sheet_names:
                start = time.time()
                if sheet[:2] == '##':
                    skills = process_sheet(book_url, sheet, default_path, 'online', 'FALSE',
                                           validator_path=validator_path, course_name=course_name)
                else:
                    skills = process_sheet(book_url, sheet, default_path, 'online', 'TRUE',
                                           validator_path=validator_path, course_name=course_name)
                if not skills:
                    skills = []
                skills.sort()
                lesson_plan.append(create_lesson_plan(sheet, skills))
                for skill in skills:
                    bkt_params.update(create_bkt_params(skill))
                end = time.time()
                if end - start < 4:
                    time.sleep(4 - (end - start))
            course_plan.append(create_course_plan(course_name, lesson_plan))

        # process editor sheet
        for index, row in url_df.iterrows():
            editor_url = row['Editor Sheet']
            if editor_url:
                editor_book = get_sheet(editor_url)
                editor_sheet_names = [sheet.title for sheet in editor_book.worksheets() if sheet.title[:2] != '!!']
                # check name conflicts in editor sheet
                # for sheet in sheet_names:
                #     start = time.time()
                #     names_from_one_sheet(editor_book, sheet)
                #     end = time.time()
                #     if end - start < 3:
                #         time.sleep(3 - (end - start))
                for sheet in editor_sheet_names:
                    start = time.time()
                    try:
                        if sheet[:2] == '##':
                            process_sheet(editor_url, sheet, editor_content_path, 'online', 'FALSE',
                                          validator_path=validator_path, editor=True, course_name="")
                        else:
                            process_sheet(editor_url, sheet, editor_content_path, 'online', 'TRUE',
                                          validator_path=validator_path, editor=True, course_name="")
                    except Exception as e:
                        print("Error in {}:".format(sheet), e)

                    end = time.time()
                    if end - start < 4:
                        time.sleep(4 - (end - start))

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
