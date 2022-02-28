import sys
import os
import pandas as pd
import gspread
import numpy as np
import re
import time
import shutil
import json
from oauth2client.service_account import ServiceAccountCredentials
import hashlib
import pickle

URL_SPREADSHEET_KEY = '1yyeDxm52Zd__56Y0T3CdoeyXvxHVt0ITDKNKWIoIMkU'

def get_all_url():
    book = get_sheet(URL_SPREADSHEET_KEY)
    worksheet = book.worksheet('URLs')
    table = worksheet.get_all_values()
    df = pd.DataFrame(table[1:], columns=table[0])
    df = df[["Book", "URL", "Editor Sheet"]]
    df = df.astype(str)
    df.replace('', 0.0, inplace=True)
    return df

def get_sheet(spreadsheet_key):
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('../sunlit-shelter-282118-8847831293f8.json', scope)
    gc = gspread.authorize(credentials)
    book = gc.open_by_key(spreadsheet_key)
    return book


def get_lesson_skill_df():
    result_df = pd.DataFrame(columns=["problem_name", "hashed_name", "sheet_name", "skills", "lesson_name"])
    url_df = get_all_url()

    # For each book
    for index, row in url_df.iterrows():
        course_name, book_url = row['Book'], row['URL']
        book = get_sheet(book_url)
        sheet_names = [sheet.title for sheet in book.worksheets() if sheet.title[:2] != '!!']

        # For each lesson
        for sheet in sheet_names:
            start = time.time()
            print(sheet)
            hash_key = 'a' + hashlib.sha1(sheet.encode('utf-8')).hexdigest()[:6]
            worksheet = book.worksheet(sheet)
            table = worksheet.get_all_values()
            try:
                df = pd.DataFrame(table[1:], columns=table[0])
            except:
                print("[{}] data frame not found, returning early".format(sheet))
                continue

            questions = [x for _, x in df.groupby('Problem Name')]

            for question in questions:
                problem_name = question.iloc[0]['Problem Name']
                problem_skills = re.split("\||,", question.iloc[0]["openstax KC"])
                problem_skills = ["_".join(skill.lower().split()).replace("-", "_") for skill in problem_skills]
                result_df = result_df.append({"problem_name": problem_name, 
                                            "hashed_name": hash_key + problem_name, 
                                            "sheet_name": sheet, 
                                            "skills": problem_skills, 
                                            "lesson_name": course_name}, ignore_index=True)
            end = time.time()
            if end - start < 2.3:
                time.sleep(2.3 - (end - start))

    result_df.to_csv("./data/lesson_skill.csv")

if __name__ == '__main__':
    get_lesson_skill_df()
