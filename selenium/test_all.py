import sys
import os
import pandas as pd
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

from test_page import test_page, start_driver
from fetch_problem_ans import *
from alert_error import alert


def test_all_content(url_prefix):
    driver = start_driver()

    all_files = get_all_content_filename()
    alert_df = pd.DataFrame(columns=["Book Name", "Error Log", "Commit Hash", "Issue Type", "Status", "Comment"])

    count = 0
    commit_hash = ""

    init_time = time.time()
    start_time = time.time()

    # testing
    # all_files = ['a616928pvalue4', 'a1279cdpowers29']

    for problem_name in all_files:
        if count % 10 == 0:

            end_time = time.time()
            time_elapse = round(end_time - start_time, 2)
            
            if count != 0 and time_elapse < 5:
                print("Fetching blank pages. Logging result and breaking program...")
                print("Last 11 problems:", all_files[max(0, count - 11): min(count + 1, len(all_files))])

                try:
                    driver.close()
                except InvalidSessionIdException:
                    print("driver not active")
                    pass

                try:
                    alert(alert_df)
                except:
                    print("Error encounted when alerting error")
                return
            
            print("Progress: {0}/{1} problems checked, time taken: {2} s".format(count, len(all_files), time_elapse))
            
            start_time = time.time()

        count += 1
        
        try:
            problem = fetch_problem_ans_info(problem_name, verbose=False)
        except Exception as e:
            err = "{0}: Exception encountered when fetching problem answer. Message: {1}".format(problem_name, str(e))
            alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
        try:
            alert_df, driver = test_page(url_prefix, problem, driver, alert_df)
            commit_hash = driver.execute_script("return document['oats-meta-site-hash']")
        except Exception as e:
            err = "Exception on problem {0}: {1}".format(problem_name, e)
            print(err)
            alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass

    final_time = time.time()
    print("Total time elapsed: {} s.".format(round(final_time - init_time, 2)))

    try:
        alert(alert_df)
    except:
        print("Error encounted when alerting error")

if __name__ == '__main__':
    if len(sys.argv) == 2:
        url_prefix = sys.argv[1]
    else:
        url_prefix = "https://cahlr.github.io/OATutor-Content-Staging/#/debug/"
    
    test_all_content(url_prefix)
