import sys
import os
import pandas as pd

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

from test_page import test_page, start_driver
from fetch_problem_ans import *
from alert_error import alert


def test_all_content(url_prefix):
    driver = start_driver()

    all_files = get_all_content_filename()
    alert_df = pd.DataFrame(columns=["Book Name", "Error Log", "Issue Type", "Status", "Comment"])

    count = 0

    for problem_name in all_files:
        if count % 10 == 0:
            print("Progress: {}/{} problems checked".format(count, len(all_files)))

        count += 1
        
        try:
            problem = fetch_problem_ans_info(problem_name, verbose=False)
        except Exception as e:
            err = "{0}: Exception encountered when fetching problem answer. Message: {1}".format(problem_name, str(e))
            alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
        try:
            alert_df, driver = test_page(url_prefix, problem, driver, alert_df)
        except Exception as e:
            err = "Exception on problem {0}: {1}".format(problem_name, e)
            print(err)
            alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass

    try:
        alert(alert_df)
    except:
        print("Error encounted when alerting error")

if __name__ == '__main__':
    if len(sys.argv) == 2:
        url_prefix = sys.argv[1]
    else:
        url_prefix = "https://cahlr.github.io/OATutor-Staging/#/debug/"
    
    test_all_content(url_prefix)
