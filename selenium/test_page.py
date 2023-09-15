from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException, TimeoutException, ElementNotInteractableException, MoveTargetOutOfBoundsException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import sys
import os
import re
import pandas as pd

from fetch_problem_ans import fetch_problem_ans_info, fetch_step_name_as_answer
from alert_error import alert
from wait_class import element_has_attribute

CORRECT = "https://cahlr.github.io/OATutor-Content-Staging/static/images/icons/green_check.svg"
WRONG = "https://cahlr.github.io/OATutor-Content-Staging/static/images/icons/error.svg"
SCROLL_LENGTH = 500
page_breaks = False
last_katex_time = None

def start_driver():
    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="107.0.5304.62").install()), options=options)
    driver.maximize_window()
    return driver


def generate_script_arithmetic(selector, answer):
    answer = re.sub(r'\\', r'\\\\', answer)
    answer = re.sub('\'', '\\\'', answer)
    answer = re.sub('\$', '', answer)
    selector = re.sub(r"\"", "\\\"", selector)
    script = "document = new Document();\n"
    script += "ans = document.querySelector(\"{}\");\n".format(selector)
    script += "var MQ = MathQuill.getInterface(2);\n"
    script += "mathField = MQ.MathField(ans);\n"
    script += "mathField.focus();\n"
    script += "mathField.latex(\"\");\n"
    script += "mathField.write('{}');\n".format(answer)
    return script


def test_page(url_prefix, problem, driver, alert_df, test_hints=True, step_title_as_ans=False):
    global page_breaks
    global last_katex_time
    url = url_prefix + problem.problem_name
    driver.get(url)
    header_selector = "[data-selenium-target=problem-header]"
    commit_hash = driver.execute_script("return document['oats-meta-site-hash']")

    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, header_selector)))
        driver.find_element(By.CSS_SELECTOR, header_selector)
    except Exception as err:
        print(err)
        err = "{}: Cannot load problem page.".format(problem.problem_name)
        alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        try:
            driver.close()
            driver = start_driver()
        except InvalidSessionIdException:
            driver = start_driver()
        return alert_df, driver

    problem_index = 0
    page_breaks = False

    for step in problem.steps:
        if page_breaks:
            break
        alert_df, driver = test_step(problem.problem_name, driver, problem_index, step, alert_df, problem.book_name, len(problem.steps), test_hints, step_title_as_ans)
        problem_index += 1

    katex_error_msg = "ParseError: KaTeX parse error"
    for log in driver.get_log('browser'): 
        if katex_error_msg in log["message"] and (last_katex_time == None or log["timestamp"] > last_katex_time + 2000):
            last_katex_time = log["timestamp"]
            err = "{}: Katex parser error".format(problem.problem_name)
            alert_df = alert_df.append({"Book Name": problem.book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            break

    driver.execute_script('console.clear()')

    return alert_df, driver


def test_step(problem_name, driver, problem_index, step, alert_df, book_name, step_len, test_hints, step_title_as_ans):

    # if checking step title, skip matrix problems
    if step_title_as_ans and step.type.split()[1] == "arithmetic" and "begin{bmatrix}" in step.answer:
        return alert_df, driver
    
    commit_hash = driver.execute_script("return document['oats-meta-site-hash']")

    # Enter step answer
    if step.type.split()[0] == "TextBox":
        if type(step.answer) != list: # if not using variabilization
            if not step_title_as_ans:
                alert_df = enter_text_answer(problem_name, driver, problem_index, step.answer, step.type.split()[1], alert_df, book_name, step_len)
            else:
                enter_text_answer(problem_name, driver, problem_index, step.answer, step.type.split()[1], None, book_name, step_len)
            # click submit and check correctness  
            try:
                submit_selector = "[data-selenium-target=submit-button-{}]".format(problem_index)
                icon_selector = "[data-selenium-target=step-correct-img-{}]".format(problem_index)
                submit = driver.find_element(By.CSS_SELECTOR, submit_selector)

                # Click Submit button
                try:
                    submit.send_keys(Keys.SPACE)
                except MoveTargetOutOfBoundsException:
                    driver.execute_script("arguments[0].scrollIntoView();", submit)
                    driver.execute_script("arguments[0].click();", submit)
                    print('text step submit button')

                # Check correctness
                try:
                    WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                except TimeoutException:
                    submit.click()
                    WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                icon = driver.find_element(By.CSS_SELECTOR, icon_selector)
                if not step_title_as_ans and icon.get_attribute("src") != CORRECT:
                    err = "{0}: Invalid answer for step {1}: {2}".format(problem_name, problem_index + 1, step.answer)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                elif step_title_as_ans and icon.get_attribute("src") == CORRECT:
                    err = "{0} step {1}, answer entered: {2}".format(problem_name, problem_index + 1, step.answer)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            
            except NoSuchElementException:
                if not step_title_as_ans:
                    err = "{0}: step {1} submit does not exist.".format(problem_name, problem_index + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
        else:  # if using variablization, need to check every possible answer
            correct = False
            for answer in step.answer:
                if not step_title_as_ans:
                    alert_df = enter_text_answer(problem_name, driver, problem_index, answer, step.type.split()[1], alert_df, book_name, step_len)
                else:
                    enter_text_answer(problem_name, driver, problem_index, answer, step.type.split()[1], None, book_name, step_len)
                # click submit and check correctness  
                try:
                    submit_selector = "[data-selenium-target=submit-button-{}]".format(problem_index)
                    icon_selector = "[data-selenium-target=step-correct-img-{}]".format(problem_index)
                    submit = driver.find_element(By.CSS_SELECTOR, submit_selector)

                    # Click Submit button
                    try:
                        submit.send_keys(Keys.SPACE)
                    except MoveTargetOutOfBoundsException:
                        driver.execute_script("arguments[0].scrollIntoView();", submit)
                        driver.execute_script("arguments[0].click();", submit)
                        print ('text step var submit button')

                    # Check correctness
                    WebDriverWait(driver, 0.45).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                    icon = driver.find_element(By.CSS_SELECTOR, icon_selector)
                    if icon.get_attribute("src") == CORRECT:
                        correct = True
                        if step_title_as_ans:
                            err = "{0} step {1}, answer entered: {2}".format(problem_name, problem_index + 1, step.answer)
                            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                        break

                except NoSuchElementException:
                    err = "{0}: step {1} submit does not exist.".format(problem_name, problem_index + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            if not correct and not step_title_as_ans:
                err = "{0}: Invalid answer for step {1} with variabilization: {2}".format(problem_name, problem_index + 1, step.answer)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        
    elif step.type.split()[0] == "MultipleChoice":
        pass # MC check not supported
    
    else:
        if not step_title_as_ans:
            err = '{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index + 1, step.type)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        problem_index += 1

    # click through hints
    if test_hints and not step_title_as_ans:
        alert_df, driver = check_hints(problem_name, problem_index, driver, step.hints, alert_df, book_name, step_len)

    return alert_df, driver

def enter_text_answer(problem_name, driver, problem_index, correct_answer, answer_type, alert_df, book_name, step_len):
    """
    Enters type TextBox answers into text box.
    """

    commit_hash = driver.execute_script("return document['oats-meta-site-hash']")

    # Matrix type
    if answer_type == "arithmetic" and "begin{bmatrix}" in correct_answer: 
        # Enter matrix dimension
        row_count = correct_answer.count('\\\\') + 1
        col_count = re.search(r'begin\{bmatrix\}(.*?)\\\\', correct_answer).group(1).count('&') + 1
        row_selector = "[data-selenium-target=grid-answer-row-input-{}] > div > input".format(problem_index)
        row = driver.find_element(By.CSS_SELECTOR, row_selector)
        row.send_keys(row_count)
        col_selector = "[data-selenium-target=grid-answer-col-input-{}] > div > input".format(problem_index)
        col = driver.find_element(By.CSS_SELECTOR, col_selector)
        col.send_keys(col_count)
        next_button_selector = "[data-selenium-target=grid-answer-next-{}]".format(problem_index)
        next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
        try:
            next_button.send_keys(Keys.SPACE)
        except MoveTargetOutOfBoundsException:
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            driver.execute_script("arguments[0].click();", next_button)
            print ('matrix step next button')

        # Enter matrix elements
        matrix_latex = re.search(r"\\begin\{bmatrix\}.+\\end\{bmatrix\}", correct_answer).group(0)
        answer_iter = re.finditer(r"\s([^\s]+)\s", matrix_latex)
        matrix_elements = [elem.group(1) for elem in answer_iter]
        for i in range(row_count * col_count):
            ans_selector = "[data-selenium-target=grid-answer-cell-{0}-{1}] > span".format(i, problem_index)
            ans = driver.find_element(By.CSS_SELECTOR, ans_selector)
            script = generate_script_arithmetic(ans_selector, matrix_elements[i])
            driver.execute_script(script, ans)

        # except NoSuchElementException:
        #     err = "{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index + 1)
        #     alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        # except AttributeError:
        #     err = "{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index + 1)
        #     alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
    
    elif answer_type == "arithmetic":
        ans_selector = "[data-selenium-target=arithmetic-answer-{}] > span".format(problem_index)
        try:
            ans = driver.find_element(By.CSS_SELECTOR, ans_selector)
            script = generate_script_arithmetic(ans_selector, correct_answer)
            driver.execute_script(script, ans)
        except NoSuchElementException:
            if alert_df:
                err = "{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    elif answer_type == "string" or answer_type == "short-essay":
        ans_selector = "[data-selenium-target=string-answer-{}] > div > input".format(problem_index)
        try:
            ans = driver.find_element(By.CSS_SELECTOR, ans_selector)
            ans.send_keys(correct_answer)
        except NoSuchElementException:
            if alert_df:
                err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)

    elif alert_df:
        err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index + 1)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
    return alert_df


def check_hints(problem_name, problem_index, driver, hints, alert_df, book_name, step_len):
    global page_breaks

    commit_hash = driver.execute_script("return document['oats-meta-site-hash']")

    try:
        raise_hand_selector = "[data-selenium-target=hint-button-{}]".format(problem_index)
        raise_hand_button = driver.find_element(By.CSS_SELECTOR, raise_hand_selector)
        try:
            raise_hand_button.send_keys(Keys.SPACE)
        except MoveTargetOutOfBoundsException:
            driver.execute_script("arguments[0].scrollIntoView();", raise_hand_button)
            driver.execute_script("arguments[0].click();", raise_hand_button)
            print ('raise hand button')
        
        # checks if clicking on raise hand button breaks the page
        try:
            header_selector = "[data-selenium-target=problem-header]"
            driver.find_element(By.CSS_SELECTOR, header_selector)
        except Exception:
            page_breaks = True
            err = "{0}: Clicking on step {1} raise hand button breaks the page.".format(problem_name, problem_index + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            print(err)
            try:
                driver.close()
                driver = start_driver()
            except InvalidSessionIdException:
                driver = start_driver()
            
            return alert_df, driver

        try: 
            hint_selector = "[data-selenium-target=hint-expand-0-{0}]".format(problem_index)
            WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, hint_selector)))
        except TimeoutException:
            try:
                raise_hand_button.click()
                WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, hint_selector)))
            except TimeoutException:
                err = "{0}: step {1} raise hand button not clickable".format(problem_name, problem_index + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                return alert_df, driver

    except NoSuchElementException:
        err = "{0}: step {1} raise hand button not found.".format(problem_name, problem_index + 1)
        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        return alert_df, driver
    
    hint_idx = 0

    while hint_idx <= len(hints):
        try:
            hint_selector = "[data-selenium-target=hint-expand-{0}-{1}]".format(hint_idx, problem_index)

            # check if hint is clickable/expandable
            try:
                WebDriverWait(driver, 0.5).until(element_has_attribute((By.CSS_SELECTOR, hint_selector), "aria-disabled", "false"))
            except Exception as e:
                err = "{0}: step {1} hint {2} expand button not clickable.".format(problem_name, problem_index + 1, hint_idx + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                return alert_df, driver
            
            hint_expand_button = driver.find_element(By.CSS_SELECTOR, hint_selector)
            try:
                hint_expand_button.send_keys(Keys.SPACE)
            except (MoveTargetOutOfBoundsException, ElementClickInterceptedException):
                driver.execute_script("arguments[0].scrollIntoView();", hint_expand_button)
                driver.execute_script("arguments[0].click();", hint_expand_button)
                print('hint expand button', hint_selector)

        except NoSuchElementException:
            err = "{0}: step {1} hint {2} expand button not found.".format(problem_name, problem_index + 1, hint_idx + 1)
            alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            return alert_df, driver

        # if is hint, proceed to the next hint
        if hint_idx == len(hints) or hints[hint_idx] == "hint":
            hint_idx += 1

        # if is scaffold, check scaffold answer
        else:
            correct_answer, answer_type = hints[hint_idx]

            if answer_type == "MultipleChoice":
                return alert_df, driver

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
                    row = driver.find_element(By.CSS_SELECTOR, row_selector)
                    try:
                        row.send_keys(row_count)
                    except ElementNotInteractableException:
                        time.sleep(0.1)
                        row.send_keys(row_count)
                    col_selector = "[data-selenium-target=grid-answer-col-input-{0}-{1}] > div > input".format(hint_idx, problem_index)
                    col = driver.find_element(By.CSS_SELECTOR, col_selector)
                    try:
                        col.send_keys(col_count)
                    except ElementNotInteractableException:
                        time.sleep(0.1)
                        col.send_keys(col_count)
                    next_button_selector = "[data-selenium-target=grid-answer-next-{0}-{1}]".format(hint_idx, problem_index)
                    next_button = driver.find_element(By.CSS_SELECTOR, next_button_selector)
                    try:
                        next_button.send_keys(Keys.SPACE)
                    except MoveTargetOutOfBoundsException:
                        driver.execute_script("arguments[0].scrollIntoView();", next_button)
                        driver.execute_script("arguments[0].click();", next_button)
                        print ('hint matrix next button')

                    # Enter matrix elements
                    matrix_latex = re.search(r"\\begin\{bmatrix\}.+\\end\{bmatrix\}", correct_answer).group(0)
                    answer_iter = re.finditer(r"\s([^\s]+)\s", matrix_latex)
                    matrix_elements = [elem.group(1) for elem in answer_iter]
                    for i in range(row_count * col_count):
                        ans_selector = "[data-selenium-target=grid-answer-cell-{0}-{1}-{2}] > span".format(i, hint_idx, problem_index)
                        ans = driver.find_element(By.CSS_SELECTOR, ans_selector)
                        script = generate_script_arithmetic(ans_selector, matrix_elements[i])
                        driver.execute_script(script, ans)

                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} matrix dimension or answer input box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver
                except AttributeError:
                    err = "{0}: step {1} hint {2} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver

            elif answer_type == "arithmetic":
                scaffold_answer_selector = "[data-selenium-target=arithmetic-answer-{0}-{1}] > span".format(hint_idx, problem_index)
                try:
                    WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, scaffold_answer_selector)))
                except TimeoutException:
                    err = "{0}: step {1} hint {2} arithmetic answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver
                try:
                    ans = driver.find_element(By.CSS_SELECTOR, scaffold_answer_selector)
                    script = generate_script_arithmetic(scaffold_answer_selector, correct_answer)
                    driver.execute_script(script, ans)
                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} arithmetic answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver
            
            elif answer_type == "string" or answer_type == "short-essay":
                scaffold_answer_selector = "[data-selenium-target=string-answer-{0}-{1}] > div > input".format(hint_idx, problem_index)
                WebDriverWait(driver, 0.2).until(EC.presence_of_element_located((By.CSS_SELECTOR, scaffold_answer_selector)))
                try:
                    ans = driver.find_element(By.CSS_SELECTOR, scaffold_answer_selector)
                    ans.send_keys(correct_answer)
                except NoSuchElementException:
                    err = "{0}: step {1} hint {2} string answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver
                except ElementNotInteractableException:
                    time.sleep(0.1)
                    try:
                        ans.send_keys(correct_answer)
                    except NoSuchElementException:
                        err = "{0}: step {1} hint {2} string answer box does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                        alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                        return alert_df, driver

            # click submit
            try:
                submit_selector = "[data-selenium-target=submit-button-{0}-{1}]".format(hint_idx, problem_index)
                icon_selector = "[data-selenium-target=step-correct-img-{0}-{1}]".format(hint_idx, problem_index)
                submit = driver.find_element(By.CSS_SELECTOR, submit_selector)
                try:
                    submit.send_keys(Keys.SPACE)
                except MoveTargetOutOfBoundsException:
                    driver.execute_script("arguments[0].scrollIntoView();", submit)
                    driver.execute_script("arguments[0].click();", submit)
                    print('submit button')
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].scrollIntoView();", submit)
                    driver.execute_script("arguments[0].click();", submit)
                    print('submit button 1')
                WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, icon_selector)))
                icon = driver.find_element(By.CSS_SELECTOR, icon_selector)
                if icon.get_attribute("src") != CORRECT:
                    err = "{0}: Invalid answer for step {1} hint {2}: {3}".format(problem_name, problem_index + 1, hint_idx + 1, correct_answer)
                    alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                    return alert_df, driver
            except NoSuchElementException:
                err = "{0}: step {1} hint {2} submit does not exist.".format(problem_name, problem_index + 1, hint_idx + 1)
                alert_df = alert_df.append({"Book Name": book_name, "Error Log": err, "Commit Hash": commit_hash, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)     
                return alert_df, driver

            hint_idx += 1
    
    return alert_df, driver


if __name__ == '__main__':
    # calling syntax:
    # python3 test_page.py <problem_name> <(optional) url_prefix>
    problem_name = sys.argv[1]
    if len(sys.argv) == 3:
        url_prefix = sys.argv[2]
    else:
        url_prefix = "https://cahlr.github.io/OATutor-Content-Staging/#/debug/"

    step_title_as_ans = True
    
    if step_title_as_ans:
        problem = fetch_step_name_as_answer(problem_name)
    else:
        problem = fetch_problem_ans_info(problem_name)
    
    driver = start_driver()
    alert_df = pd.DataFrame(columns=["Book Name", "Error Log", "Commit Hash", "Issue Type", "Status", "Comment"])
    alert_df = test_page(url_prefix, problem, driver, alert_df, test_hints=True, step_title_as_ans=step_title_as_ans)[0]
    alert(alert_df, step_title_as_ans=step_title_as_ans)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass


