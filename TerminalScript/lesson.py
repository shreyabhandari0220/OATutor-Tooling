import hashlib
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


def create_lesson_plan(sheet, skills, lesson_id):
    lesson_number = sheet.split()[0]
    lesson_topics = " ".join(sheet.split()[1:])

    lesson_name = ("Lesson " + lesson_number)

    lesson_plan = {
        "id": lesson_id,
        "name": lesson_name,
        "topics": lesson_topics,
        "allowRecycle": True,
        "learningObjectives": dict(zip(skills, [0.85 for _ in skills]))
    }

    return lesson_plan


def create_course_plan(course_name, lesson_plan, editor=False):
    if not lesson_plan:
        lesson_plan = []

    course_plan = {
        "courseName": course_name,
        "lessons": lesson_plan
    }

    if editor:
        course_plan.update({
            "editor": True
        })

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


def create_total(default_path, is_local, sheet_keys=None, sheet_names=None, bank_url=None):
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
        raise Exception("Local problem reads no longer supported.")

    elif is_local == 'online':
        url_df = get_all_url(bank_url=bank_url)

        sheets_queue = []
        for _, row in url_df.iterrows():
            course_name, book_url, editor_url = row['Book'], row['URL'], row['Editor Sheet']
            if book_url:
                sheets_queue.append((book_url, False, course_name))
            if editor_url:
                sheets_queue.append((editor_url, True, ""))
        for sheet_url, is_editor, course_name in sheets_queue:
            lesson_plan = []
            book = get_sheet(sheet_url)

            if is_editor:
                course_name = "!!Editor Sheet " + hashlib.sha1(str(sheet_url).encode("utf-8")).hexdigest()[:6]
            try:
                sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
            except Exception as e:
                print("Gspread Error in {}, {}:".format(course_name, sheet_url), e)
            for sheet in sheet_names:
                start = time.time()
                if sheet[:2] == '##':
                    skills, lesson_id = process_sheet(sheet_url, sheet, default_path, 'online', 'FALSE',
                                           validator_path=validator_path, course_name=course_name, editor=is_editor)
                else:
                    skills, lesson_id = process_sheet(sheet_url, sheet, default_path, 'online', 'TRUE',
                                           validator_path=validator_path, course_name=course_name, editor=is_editor)
                if not lesson_id:
                    continue
                if not skills:
                    skills = []
                skills.sort()
                lesson_plan.append(create_lesson_plan(sheet, skills, lesson_id))
                for skill in skills:
                    bkt_params.update(create_bkt_params(skill))

                end = time.time()
                if end - start < 4.5:
                    time.sleep(4.5 - (end - start))
            course_plan.append(create_course_plan(course_name, lesson_plan, editor=is_editor))

    file = open(os.path.join("..", "coursePlans.js"), "w")
    finish_course_plan(course_plan, file)

    file = open(os.path.join("..", "bktParams.js"), "w")
    finish_bkt_params(bkt_params, file)

    file.close()


if __name__ == '__main__':
    is_local = sys.argv[1]
    sheet_key = sys.argv[2]
    sheet_names = sys.argv[3:]
    create_total(sheet_key, sheet_names, '../OpenStax Content', is_local)
