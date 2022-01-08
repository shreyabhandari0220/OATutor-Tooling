from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import sys
import os
import re
import pandas as pd

from fetch_problem_ans import fetch_problem_ans_info
from generate_script import generate_script_arithmetic
from alert_error import alert
from wait_class import element_has_attribute

# URL_PREFIX = "https://cahlr.github.io/OATutor-Staging/#/debug/"
CORRECT = "https://cahlr.github.io/OATutor-Staging/static/images/icons/green_check.svg"
WRONG = "https://cahlr.github.io/OATutor-Staging/static/images/icons/error.svg"

def start_driver():
    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    # options.headless = True
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(ChromeDriverManager(version="96.0.4664.45").install(), options=options)
    return driver

def test_page(url_prefix, problem, driver, alert_df, test_hints=False):
    url = url_prefix + problem.problem_name
    driver.get(url)
    header_selector = "[data-selenium-target=problem-header]"
    # WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, header_selector)))
    try:
        driver.find_element_by_css_selector(header_selector)
    except NoSuchElementException:
        err = "{}: Cannot load problem page.".format(problem_name)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    problem_index = 0

    for step in problem.steps:
        alert_df = test_step(problem.problem_name, driver, problem_index, step, alert_df, problem.book_name, len(problem.steps), test_hints=test_hints)
        problem_index += 1

    return alert_df, driver


def test_step(problem_name, driver, problem_index, step, alert_df, book_name, step_len, test_hints):

    # if step.type == "MultipleChoice":
    #     return alert_df
    # Enter step answer
    if step.type.split()[0] == "TextBox":
        if type(step.answer) != list:
            alert_df = enter_text_answer(problem_name, driver, problem_index, step.answer, step.type.split()[1], alert_df, book_name, step_len)
            # click submit and check correctness  
            try:
                submit_selector = "[data-selenium-target=submit-button-{}]".format(problem_index)
                icon_selector = "[data-selenium-target=step-correct-img-{}]".format(problem_index)
                submit = driver.find_element_by_css_selector(submit_selector)
                ActionChains(driver).move_to_element(submit).click(submit).perform()
                WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                icon = driver.find_element_by_css_selector(icon_selector)
                if icon.get_attribute("src") != CORRECT:
                    err = "{0}: Invalid answer for step {1}: {2}".format(problem_name, problem_index + 1, step.answer)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            except NoSuchElementException:
                err = "{0}: step {1} submit does not exist.".format(problem_name, problem_index + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
        # if using variablization
        else:
            correct = False
            for answer in step.answer:
                alert_df = enter_text_answer(problem_name, driver, problem_index, answer, step.type.split()[1], alert_df, book_name, step_len)
                # click submit and check correctness  
                try:
                    submit_selector = "[data-selenium-target=submit-button-{}]".format(problem_index)
                    icon_selector = "[data-selenium-target=step-correct-img-{}]".format(problem_index)
                    submit = driver.find_element_by_css_selector(submit_selector)
                    ActionChains(driver).move_to_element(submit).click(submit).perform()
                    WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                    icon = driver.find_element_by_css_selector(icon_selector)
                    if icon.get_attribute("src") == CORRECT:
                        correct = True
                        break
                except NoSuchElementException:
                    err = "{0}: step {1} submit does not exist.".format(problem_name, problem_index + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            if not correct:
                err = "{0}: Invalid answer for step {1} with variabilization: {2}".format(problem_name, problem_index + 1, step.answer)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
    elif step.type.split()[0] == "MultipleChoice":
        pass
        # enter_mc_answer(problem_name, driver, problem_index, correct_answer)
    
    else:
        err = '{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index + 1, step.type)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        problem_index += 1

    # click through hints
    if test_hints and len(step.hints) > 0:
        alert_df = check_hints(problem_name, problem_index, driver, step.hints, alert_df, book_name, step_len)

    return alert_df

def enter_text_answer(problem_name, driver, problem_index, correct_answer, answer_type, alert_df, book_name, step_len):
    """
    Enters type TextBox answers into text box.
    """
    
    if answer_type == "arithmetic" and "begin{bmatrix}" in correct_answer: 
        try:
            # Enter matrix dimension
            row_count = correct_answer.count('\\\\') + 1
            col_count = re.search(r'begin\{bmatrix\}(.*?)\\\\', correct_answer).group(1).count('&') + 1
            row_selector = "[data-selenium-target=grid-answer-row-input-{}] > div > input".format(problem_index)
            row = driver.find_element_by_css_selector(row_selector)
            row.send_keys(row_count)
            col_selector = "[data-selenium-target=grid-answer-col-input-{}] > div > input".format(problem_index)
            col = driver.find_element_by_css_selector(col_selector)
            col.send_keys(col_count)
            next_button_selector = "[data-selenium-target=grid-answer-next-{}]".format(problem_index)
            next_button = driver.find_element_by_css_selector(next_button_selector)
            ActionChains(driver).move_to_element(next_button).click(next_button).perform()

            # Enter matrix elements
            matrix_latex = re.search(r"\\begin\{bmatrix\}.+\\end\{bmatrix\}", correct_answer).group(0)
            answer_iter = re.finditer(r"\s([^\s]+)\s", matrix_latex)
            matrix_elements = [elem.group(1) for elem in answer_iter]
            for i in range(row_count * col_count):
                ans_selector = "[data-selenium-target=grid-answer-cell-{0}-{1}] > span".format(i, problem_index)
                ans = driver.find_element_by_css_selector(ans_selector)
                script = generate_script_arithmetic(ans_selector, matrix_elements[i])
                driver.execute_script(script, ans)

        except NoSuchElementException:
            err = "{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index - 1))
        except AttributeError:
            err = "{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index - 1))
    
    elif answer_type == "arithmetic":
        ans_selector = "[data-selenium-target=arithmetic-answer-{}] > span".format(problem_index)
        try:
            ans = driver.find_element_by_css_selector(ans_selector)
            script = generate_script_arithmetic(ans_selector, correct_answer)
            driver.execute_script(script, ans)
        except NoSuchElementException:
            err = "{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index))

    elif answer_type == "string":
        ans_selector = "[data-selenium-target=string-answer-{}] > div > input".format(problem_index)
        print(1, ans_selector)
        try:
            ans = driver.find_element_by_css_selector(ans_selector)
            ans.send_keys(correct_answer)
        except NoSuchElementException:
            err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} string answer box does not exist.".format(problem_name, problem_index))

    else:
        err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index + 1)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        # print("{0}: step {1} answer box type not defined: {2}".format(problem_name, problem_index, answer_type))
    return alert_df


def check_hints(problem_name, problem_index, driver, hints, alert_df, book_name, step_len):
    try:
        raise_hand_selector = "[data-selenium-target=hint-button-{}]".format(problem_index)
        raise_hand_button = driver.find_element_by_css_selector(raise_hand_selector)
        # raise_hand_button.click()
        ActionChains(driver).move_to_element(raise_hand_button).click(raise_hand_button).perform()
        try: 
            hint_selector = "[data-selenium-target=hint-expand-0-{0}]".format(problem_index)
            WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, hint_selector)))
        except TimeoutException:
            try:
                raise_hand_button.click()
                WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, hint_selector)))
            except TimeoutException:
                err = "{0}: step {1} raise hand button not clickable".format(problem_name, problem_index + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                return alert_df

    except NoSuchElementException:
        err = "{0}: step {1} raise hand button not found.".format(problem_name, problem_index + 1)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        return alert_df
    hint_idx = 0

    while hint_idx <= len(hints):
        try:
            hint_selector = "[data-selenium-target=hint-expand-{0}-{1}]".format(hint_idx, problem_index)

            # check if hint is clickable/expandable
            try:
                WebDriverWait(driver, 0.2).until(element_has_attribute((By.CSS_SELECTOR, hint_selector), "aria-disabled", "false"))
            except Exception as e:
                err = "{0}: step {1} hint {2} expand button not clickable.".format(problem_name, problem_index + 1, hint_idx + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                return alert_df
            
            hint_expand_button = driver.find_element_by_css_selector(hint_selector)

            ActionChains(driver).move_to_element(hint_expand_button).click(hint_expand_button).perform()

        except NoSuchElementException:
            err = "{0}: step {1} hint {2} expand button not found.".format(problem_name, problem_index + 1, hint_idx + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            return alert_df

        if hint_idx == len(hints) or hints[hint_idx] == "hint":
            hint_idx += 1
        else:
            correct_answer, answer_type = hints[hint_idx]

            if answer_type == "MultipleChoice":
                return alert_df

            if answer_type != "MultipleChoice":
                answer_type = answer_type.split()[1]

            # matrix answer type
            if answer_type == "arithmetic" and "begin{bmatrix}" in correct_answer:
                try:
                    # Enter matrix dimension
                    row_count = correct_answer.count('\\\\') + 1
                    col_count = re.search(r'begin\{bmatrix\}(.*?)\\\\', correct_answer).group(1).count('&') + 1
                    row_selector = "[data-selenium-target=grid-answer-row-input-{0}-{1}] > div > input".format(hint_idx, problem_index)
                    WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, row_selector)))
                    row = driver.find_element_by_css_selector(row_selector)
                    row.send_keys(row_count)
                    col_selector = "[data-selenium-target=grid-answer-col-input-{0}-{1}] > div > input".format(hint_idx, problem_index)
                    col = driver.find_element_by_css_selector(col_selector)
                    col.send_keys(col_count)
                    next_button_selector = "[data-selenium-target=grid-answer-next-{0}-{1}]".format(hint_idx, problem_index)
                    next_button = driver.find_element_by_css_selector(next_button_selector)
                    ActionChains(driver).move_to_element(next_button).click(next_button).perform()

                    # Enter matrix elements
                    matrix_latex = re.search(r"\\begin\{bmatrix\}.+\\end\{bmatrix\}", correct_answer).group(0)
                    answer_iter = re.finditer(r"\s([^\s]+)\s", matrix_latex)
                    matrix_elements = [elem.group(1) for elem in answer_iter]
                    for i in range(row_count * col_count):
                        ans_selector = "[data-selenium-target=grid-answer-cell-{0}-{1}-{2}] > span".format(i, hint_idx, problem_index)
                        ans = driver.find_element_by_css_selector(ans_selector)
                        script = generate_script_arithmetic(ans_selector, matrix_elements[i])
                        driver.execute_script(script, ans)

                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} matrix dimension or answer input box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    # print("{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index))
                    return alert_df
                except AttributeError:
                    err = "{0}: step {1} hint {2} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    # print("{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index))
                    return alert_df


            elif answer_type == "arithmetic":
                scaffold_answer_selector = "[data-selenium-target=arithmetic-answer-{0}-{1}] > span".format(hint_idx, problem_index)
                WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, scaffold_answer_selector)))
                try:
                    ans = driver.find_element_by_css_selector(scaffold_answer_selector)
                    script = generate_script_arithmetic(scaffold_answer_selector, correct_answer)
                    driver.execute_script(script, ans)
                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} arithmetic answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df
            
            elif answer_type == "string":
                scaffold_answer_selector = "[data-selenium-target=string-answer-{0}-{1}] > div > input".format(hint_idx, problem_index)
                WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, scaffold_answer_selector)))
                try:
                    ans = driver.find_element_by_css_selector(scaffold_answer_selector)
                    ans.send_keys(correct_answer)
                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} string answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df

            # click submit
            try:
                submit_selector = "[data-selenium-target=submit-button-{0}-{1}]".format(hint_idx, problem_index)
                icon_selector = "[data-selenium-target=step-correct-img-{0}-{1}]".format(hint_idx, problem_index)
                submit = driver.find_element_by_css_selector(submit_selector)
                ActionChains(driver).move_to_element(submit).click(submit).perform()
                WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                icon = driver.find_element_by_css_selector(icon_selector)
                if icon.get_attribute("src") != CORRECT:
                    err = "{0}: Invalid answer for step {1} hint {2}: {3}".format(problem_name, problem_index + 1, hint_idx + 1, correct_answer)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df
            except NoSuchElementException:
                err = "{0}: step {1} hint {2} submit does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)     
                return alert_df

            hint_idx += 1
    
    return alert_df



# def enter_mc_answer(problem_name, driver, problem_index, correct_answer, alert_df):
#     """
#     Clicks the correct answer for multiple choice questions
#     Note: within the function, correct_answer involving LaTeX are stripped of $$
#     """

#     choice_idx = 1
#     all_choices = []  # checkes if the same answer appears multiple times
#     correct_answer = correct_answer.replace("$$", "")
#     while True:
#         ans_selector = "//*[@id=\"root\"]/div/div/div/div[{0}]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{1}]/span[2]"\
#             .format(problem_index, choice_idx)
#         ans_choice_selector = "//*[@id=\"root\"]/div/div/div/div[{0}]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{1}]/span[1]"\
#             .format(problem_index, choice_idx)
#         try:
#             # print('full answer:', driver.find_element_by_xpath(ans_selector).text)
#             ans = driver.find_element_by_xpath(ans_selector).text.split('\n')[0]
#             # ans = driver.find_element_by_xpath(ans_selector).text.replace('\n', '')
#             # print('answer choice:', ans)

#             if ans in all_choices:
#                 err = "{0}: Answer choice appears more than once: {1}".format(problem_name, ans)
#                 alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
#                 # print("{0}: Answer choice appears more than once: {1}".format(problem_name, ans))
#             else:
#                 all_choices.append(ans)

#             if ans == correct_answer:
#                 ans_choice = driver.find_element_by_xpath(ans_choice_selector)
#                 ans_choice.click()

#         except NoSuchElementException:
#             break
        
#         choice_idx += 1
#     return alert_df


if __name__ == '__main__':
    # calling syntax:
    # python3 test_page.py <problem_name> <(optional) url_prefix>
    problem_name = sys.argv[1]
    if len(sys.argv) == 3:
        url_prefix = sys.argv[2]
    else:
        url_prefix = "https://cahlr.github.io/OATutor-Staging/#/debug/"
    
    problem = fetch_problem_ans_info(problem_name)
    driver = start_driver()
    alert_df = pd.DataFrame(columns=["Book Name", "Error Log", "Issue Type", "Status", "Comment"])
    alert_df = test_page(url_prefix, problem, driver, alert_df, test_hints=True)[0]
    alert(alert_df)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass


