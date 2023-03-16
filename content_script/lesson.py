import hashlib
import sys
import os
import pandas as pd
import time
import shutil
from gspread_dataframe import set_with_dataframe
from openpyxl import load_workbook
import json

from process_sheet import process_sheet, get_all_url, get_sheet_online, URL_SPREADSHEET_KEY



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


def create_lesson_plan(sheet, skills, lesson_id, meta):
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

    if meta:
        lesson_plan.update(meta)

    return lesson_plan


def create_course_plan(course_name, lesson_plan, course_oer, course_license, editor=False):
    if not lesson_plan:
        lesson_plan = []

    course_plan = {
        "courseName": course_name,
        "courseOER": course_oer,
        "courseLicense": course_license,
        "lessons": lesson_plan
    }

    if editor:
        course_plan.update({
            "editor": True
        })

    return course_plan


def finish_course_plan(courses, file):
    file.write(json.dumps(courses, indent=4))
    file.close()


def finish_bkt_params(bkt_params, file):
    file.write(json.dumps(bkt_params, indent=4))
    file.close()

def finish_skill_model(bkt_params, file):
    file.write(json.dumps(bkt_params, indent=4))
    file.close()


def create_total(default_path, is_local, sheet_names=None, bank_url=None, full_update=False):
    """if sheet_names is not provided, default to run all sheets"""

    if is_local != "local" and is_local != "online":
        raise Exception("Running mode must be either 'local' or 'online")

    course_plan = old_course_plan = []
    bkt_params = old_bkt_params = {}
    skill_model: dict = {}

    skill_model_path = os.path.join("..", "skillModel.json")
    editor_content_path = os.path.join("..", "Editor Content")
    validator_path = os.path.join("..", ".OpenStax Validator")
    bkt_params_path = os.path.join("..", "bktParams.json")
    course_plans_path = os.path.join("..", "coursePlans.json")
    
    if full_update:
        if os.path.exists(skill_model_path):
            os.remove(skill_model_path)
        if os.path.isdir(default_path):
            shutil.rmtree(default_path)
        if os.path.isdir(editor_content_path):
            shutil.rmtree(editor_content_path)
        if os.path.isdir(validator_path):
            shutil.rmtree(validator_path)

    else:
        if os.path.exists(skill_model_path):
            with open(skill_model_path) as skill_model_file:
                skill_model = json.load(skill_model_file)

        if os.path.exists(bkt_params_path):
            with open(bkt_params_path) as bkt_params_file:
                old_bkt_params = json.load(bkt_params_file)
            os.remove(bkt_params_path)

        if os.path.exists(course_plans_path):
            with open(course_plans_path) as course_plans_file:
                old_course_plan = json.load(course_plans_file)
            os.remove(course_plans_path)


    url_df, hash_df = get_all_url(bank_url=bank_url, is_local=is_local)

    sheets_queue = []
    for _, row in url_df.iterrows():
        course_name, book_url, book_oer, book_license, editor_url = row['Book'], row['URL'], row['OER'], row['License'], row['Editor Sheet']
        if book_url:
            sheets_queue.append((book_url, False, course_name, book_oer, book_license))
        if editor_url:
            sheets_queue.append((editor_url, True, "", "", ""))
            
    for sheet_url, is_editor, course_name, course_oer, course_license in sheets_queue:
        lesson_plan = []
        if is_editor:
            course_name = "!!Editor Sheet " + hashlib.sha1(str(sheet_url).encode("utf-8")).hexdigest()[:6]

        if is_local == 'online':
            book = get_sheet_online(sheet_url)
            try:
                sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']
            except Exception as e:
                print("Gspread Error in {}, {}:".format(course_name, sheet_url), e)
        
        else:
            book = load_workbook(sheet_url)
            sheet_names = [sheet.title for sheet in book.worksheets if sheet.title[:2] != '!!']
        
        for sheet in sheet_names:
            # process only the sheets that have changed since last final.py run
            if is_local == 'local' or full_update or sheet != 0.0 and sheet + sheet_url in list(hash_df["Changed Sheets"].unique()):
                start = time.time()
                if sheet[:2] == '##':
                    skills, lesson_id, skills_dict, meta = process_sheet(sheet_url, sheet, default_path, is_local, 'FALSE',
                                        course_name=course_name)
                    sheet = sheet[2:]
                else:
                    skills, lesson_id, skills_dict, meta = process_sheet(sheet_url, sheet, default_path, is_local, 'TRUE',
                                        course_name=course_name)
                if not lesson_id:
                    continue
                if not skills:
                    continue
                skill_model.update(skills_dict)
                skills.sort()
                lesson_plan.append(create_lesson_plan(sheet, skills, lesson_id, meta))
                for skill in skills:
                    bkt_params.update(create_bkt_params(skill))

                end = time.time()
                if is_local == "online" and end - start < 4.5:
                    time.sleep(4.5 - (end - start))
        
        if is_local == 'online' and not full_update:
            # Append everything from the old lesson_plan to the new lesson_plan
            old_lesson_plan = []
            for course in old_course_plan:
                if course["courseName"] == course_name:
                    old_lesson_plan = course["lessons"]
                    break

            new_lesson_ids = []
            for lesson in lesson_plan:
                new_lesson_ids.append(lesson["id"])

            for lesson in old_lesson_plan:
                if lesson["id"] not in new_lesson_ids:
                    lesson_plan.append(lesson)

        lesson_plan.sort(key=lambda lesson: lesson["name"])
        course_plan.append(create_course_plan(course_name, lesson_plan, course_oer, course_license, editor=is_editor))

    if is_local == 'online' and not full_update:
        # Append everything from the old bkt_params to the new bkt_params
        new_skills = list(bkt_params.keys())
        for skill, param in old_bkt_params.items():
            if skill not in new_skills:
                bkt_params.update({skill: param})

    file = open(os.path.join("..", "coursePlans.json"), "w")
    finish_course_plan(course_plan, file)

    file = open(os.path.join("..", "bktParams.json"), "w")
    finish_bkt_params(bkt_params, file)

    file = open(os.path.join("..", "skillModel.json"), "w")
    finish_skill_model(skill_model, file)

    # cleared changed sheet list, only support google sheets
    if is_local == "online":
        changed_df = pd.DataFrame(index=range(len(hash_df)), columns=["Changed Sheets"])
        changed_df["Changed Sheets"] = ""
        try:
            hash_sheet = get_sheet_online(URL_SPREADSHEET_KEY).worksheet('Content Hash')
            set_with_dataframe(hash_sheet, changed_df, col=4)
        except Exception as e:
            print('Fail to clear changed sheets list')

if __name__ == '__main__':
    is_local = sys.argv[1]
    sheet_names = sys.argv[2:]
    create_total('../OpenStax Content', is_local, sheet_names)
