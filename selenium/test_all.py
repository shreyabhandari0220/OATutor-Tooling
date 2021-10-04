import sys
import os

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

from test_page import test_page
from fetch_problem_ans import *


def test_all_content():
    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager(version="94.0.4606.41").install(), options=options)

    all_files = get_all_content_filename()
    for problem_name in all_files:
        try:
            problem_ans_info = fetch_problem_ans_info(problem_name, verbose=False)
            test_page(problem_name, problem_ans_info, driver=driver)
        except Exception as e:
            print("Exception on problem {0}: {1}".format(problem_name, e))

    try:
        driver.close()
    except InvalidSessionIdException:
        pass

if __name__ == '__main__':
    test_all_content()
