import sys
import os
import pandas as pd

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

from test_page import test_page
from fetch_problem_ans import *
from alert_error import alert


def test_all_content():
    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager(version="94.0.4606.41").install(), options=options)

    all_files = get_all_content_filename()
    alert_df = pd.DataFrame(columns=["Error Log", "Issue Type", "Status", "Comment"])

    for problem_name in all_files:
        try:
            problem_ans_info = fetch_problem_ans_info(problem_name, verbose=False)
            alert_df = test_page(problem_name, problem_ans_info, driver, alert_df)
        except Exception as e:
            err = "Exception on problem {0}: {1}".format(problem_name, e)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass

    try:
        alert(alert_df)
    except:
        print("Error encounted when alerting error")

if __name__ == '__main__':
    test_all_content()
