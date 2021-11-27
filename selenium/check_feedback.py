from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import os
import time
import random
import sys
from datetime import datetime
import slack
from pathlib import Path
from dotenv import load_dotenv

from fetch_problem_ans import get_all_content_filename

def submit_feedback(url_prefix):
    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    # options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager(version="94.0.4606.41").install(), options=options)

    problem_names = random.sample(get_all_content_filename(), 5)
    for problem_name in problem_names:
        url = url_prefix + problem_name
        driver.get(url)
        found_report = False
        idx = 0
        failed = []
        for i in range(4, 30):
            try:
                report_button_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div[2]/button".format(i)
                report_button = driver.find_element_by_xpath(report_button_selector)
                report_button.click()
                time.sleep(0.45)
                found_report = True
                idx = i + 1
                break
            except NoSuchElementException:
                pass
        if not found_report:
            print("Did not find report button for problem: {}".format(problem_name))
            failed.append(problem_name)
            continue
        try:
            report_text_selector = "//*[@id=\"outlined-multiline-flexible\"]"
            report_text = driver.find_element_by_xpath(report_text_selector)
            report_text.send_keys("selenium test for feedback")
        except NoSuchElementException:
            print("Unable to write report to problem: {}".format(problem_name))
            failed.append(problem_name)
            continue

        try:
            submit_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div[2]/div/div[2]/button".format(idx)
            submit = driver.find_element_by_xpath(submit_selector)
            submit.click()
            time.sleep(0.3)
        except NoSuchElementException:
            print("Unable to click submit for problem: {}".format(problem_name))
            failed.append(problem_name)
            continue
    
    try:
        driver.close()
    except InvalidSessionIdException:
        pass

    return [p for p in problem_names if p not in failed]

def check_firebase(str_now):
    feedback_problem = []
    cred = credentials.Certificate('../firebase_service_account.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    feedbacks = db.collection('feedbackFall21').where("timeStamp", ">=", str_now).get()
    for f in feedbacks:
        dic = f.to_dict()
        if dic["feedback"] == "selenium test for feedback":
            feedback_problem.append(dic["problemID"])
            db.collection("feedbackFall21").document(dic["timeStamp"]).delete()
    return feedback_problem

if __name__ == '__main__':
    if len(sys.argv) == 2:
        url_prefix = sys.argv[1]
    else:
        url_prefix = "https://cahlr.github.io/OATutor-Staging/#/debug/"
    
    now = datetime.now()
    str_now = now.strftime("%m-%d-%Y %H:%M:%S")
    problem_names = submit_feedback(url_prefix)
    firebase_problem_names = check_firebase(str_now)
    # print("problem_names:", problem_names)
    # print("firebase_problem_names:", firebase_problem_names)
    if set(problem_names) == set(firebase_problem_names):
        print("Feedback successful")
    else:
        print("Feedback Unsuccessful")

        # Slack Bot
        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path)
        client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
        client.chat_postMessage(channel='#openits', text='Hello World!')
