from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

import time
import sys
import os
import re
import pandas as pd

from generate_script import generate_script_arithmetic
from alert_error import alert

URL_PREFIX = "https://cahlr.github.io/OATutor-Staging/#/debug/"
CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"


def test_page(problem_name, ans_and_type, driver, alert_df):
    url = URL_PREFIX + problem_name
    driver.get(url)

    problem_index = 2

    for correct_answer, problem_type in ans_and_type:
        alert_df = test_step(problem_name, driver, problem_index, correct_answer, problem_type, alert_df)
        problem_index += 1
    return alert_df


def test_step(problem_name, driver, problem_index, correct_answer, problem_type, alert_df):

    if problem_type.split()[0] == "MultipleChoice":
        return alert_df
    # Enter step answer
    if problem_type.split()[0] == "TextBox":
        alert_df = enter_text_answer(problem_name, driver, problem_index, correct_answer, problem_type.split()[1], alert_df)
    elif problem_type.split()[0] == "MultipleChoice":
        pass
        # enter_mc_answer(problem_name, driver, problem_index, correct_answer)
    else:
        err = '{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index - 1, problem_type)
        alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        # print('{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index - 1, problem_type))
        problem_index += 1

    # click submit and check correctness  
    try:
        submit_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[2]/div/div[3]/center/button".format(problem_index)
        icon_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[2]/div/div[4]/div/img".format(problem_index)
        submit = driver.find_element_by_xpath(submit_selector)
        submit.click()
        time.sleep(0.4)
        icon = driver.find_element_by_xpath(icon_selector)
        if icon.get_attribute("src") != CORRECT:
            err = "{0}: Invalid answer for step {1}: {2}".format(problem_name, problem_index - 1, correct_answer)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: Invalid answer for step {1}: {2}".format(problem_name, problem_index - 1, correct_answer))
    except NoSuchElementException:
        err = "{0}: step {1} submit does not exist.".format(problem_name, problem_index - 1)
        alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        # print("{0}: step {1} submit does not exist.".format(problem_name, problem_index - 1))

    # click through hints
    # try:
    #     raise_hand_button_xpath = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[2]/div/div[2]/center/button".format(problem_index)
    #     raise_hand_button = driver.find_element_by_xpath(raise_hand_button_xpath)
    #     raise_hand_button.click()
    #     time.sleep(0.2)
    #     hint_idx = 1
    #     while True:
    #         hint_xpath = "//*[@id=\"root\"]/div[1]/div/div/div[{0}]/div/div[1]/div[2]/div/div[{1}]".format(problem_index, hint_idx)
    #         hint_expand_button = driver.find_element_by_xpath(hint_xpath)
    #         hint_expand_button.click()
    #         time.sleep(0.2)
    #         # try:
    #         #     scaffold_hint_xpath = "//*[@id=\"panel1a-content\"]/div/span/div/div/div[1]/div[2]/center/span"
    #         #     scaffold_hint = driver.find_element_by_xpath(scaffold_hint_xpath)

            
    #         # except NoSuchElementException:
    #         #     pass

    #         hint_idx += 1

    # except Exception as e:
    #     if type(e) == NoSuchElementException:
    #         return
    #     print(e)
    return alert_df

def enter_text_answer(problem_name, driver, problem_index, correct_answer, answer_type, alert_df):
    """
    Enters type TextBox answers into text box.
    """
    
    if answer_type == "arithmetic" and "begin{bmatrix}" in correct_answer: 
        try:
            # Enter matrix dimension
            row_count = correct_answer.count('\\\\') + 1
            col_count = re.search(r'begin\{bmatrix\}([^\\]+)\\\\', correct_answer).group(1).count('&') + 1
            row_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div/form/div/div[1]/div[1]/div/input".format(problem_index)
            row = driver.find_element_by_xpath(row_selector)
            row.send_keys(row_count)
            col_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div/form/div/div[1]/div[2]/div/input".format(problem_index)
            col = driver.find_element_by_xpath(col_selector)
            col.send_keys(col_count)
            next_button_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div/form/div/div[2]/button".format(problem_index)
            next_button = driver.find_element_by_xpath(next_button_selector)
            next_button.click()
            # time.sleep(0.2)

            # Enter matrix elements
            matrix_latex = re.search(r"\\begin\{bmatrix\}.+\\end\{bmatrix\}", correct_answer).group(0)
            answer_iter = re.finditer(r"\s([^\s]+)\s", matrix_latex)
            matrix_elements = [elem.group(1) for elem in answer_iter]
            for i in range(1, row_count * col_count + 1):
                ans_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{0}]/div/div[1]/div[2]/div/div[2]/div/div/div[2]/div[2]/center[{1}]/span".format(problem_index, i)
                ans = driver.find_element_by_xpath(ans_selector)
                script = generate_script_arithmetic(ans_selector, matrix_elements[i - 1])
                driver.execute_script(script, ans)

        except NoSuchElementException:
            err = "{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index - 1)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} matrix dimension or answer input box does not exist.".format(problem_name, problem_index - 1))
        except AttributeError:
            err = "{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index - 1)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} matrix answer format wrong (likely does not contain matrix latex).".format(problem_name, problem_index - 1))
    
    elif answer_type == "arithmetic":
        ans_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/center/span".format(problem_index)
        try:
            ans = driver.find_element_by_xpath(ans_selector)
            script = generate_script_arithmetic(ans_selector, correct_answer)
            driver.execute_script(script, ans)
        except NoSuchElementException:
            err = "{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index - 1)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index - 1))

    elif answer_type == "string":
        ans_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div/div/input".format(problem_index)
        try:
            ans = driver.find_element_by_xpath(ans_selector)
            ans.send_keys(correct_answer)
        except NoSuchElementException:
            err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index - 1)
            alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
            # print("{0}: step {1} string answer box does not exist.".format(problem_name, problem_index - 1))

    else:
        err = "{0}: step {1} string answer box does not exist.".format(problem_name, problem_index - 1)
        alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
        # print("{0}: step {1} answer box type not defined: {2}".format(problem_name, problem_index - 1, answer_type))
    return alert_df

    


def enter_mc_answer(problem_name, driver, problem_index, correct_answer, alert_df):
    """
    Clicks the correct answer for multiple choice questions
    Note: within the function, correct_answer involving LaTeX are stripped of $$
    """

    choice_idx = 1
    all_choices = []  # checkes if the same answer appears multiple times
    correct_answer = correct_answer.replace("$$", "")
    while True:
        ans_selector = "//*[@id=\"root\"]/div/div/div/div[{0}]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{1}]/span[2]"\
            .format(problem_index, choice_idx)
        ans_choice_selector = "//*[@id=\"root\"]/div/div/div/div[{0}]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{1}]/span[1]"\
            .format(problem_index, choice_idx)
        try:
            # print('full answer:', driver.find_element_by_xpath(ans_selector).text)
            ans = driver.find_element_by_xpath(ans_selector).text.split('\n')[0]
            # ans = driver.find_element_by_xpath(ans_selector).text.replace('\n', '')
            # print('answer choice:', ans)

            if ans in all_choices:
                err = "{0}: Answer choice appears more than once: {1}".format(problem_name, ans)
                alert_df = alert_df.append({"Error Log": err, "Issue Type": "", "Status": "open", "Comment": ""}, ignore_index=True)
                # print("{0}: Answer choice appears more than once: {1}".format(problem_name, ans))
            else:
                all_choices.append(ans)

            if ans == correct_answer:
                ans_choice = driver.find_element_by_xpath(ans_choice_selector)
                ans_choice.click()

        except NoSuchElementException:
            break
        
        choice_idx += 1
    return alert_df


if __name__ == '__main__':
    # calling syntax:
    # python3 test_page.py <problem_name> <ans1> <type1> <ans2> <type2> ...
    # type is either TextBox or MultipleChoice
    problem_name = sys.argv[1]
    info_list = []
    i = 2
    while i < len(sys.argv) - 1:
        info_list.append([sys.argv[i], sys.argv[i + 1]])
        i += 2

    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    # options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager(version="94.0.4606.41").install(), options=options)
    alert_df = pd.DataFrame(columns=["Error Log", "Issue Type", "Status", "Comment"])
    alert_df = test_page(problem_name, info_list, driver, alert_df)
    alert(alert_df)


    # try:
    #     driver.close()
    # except InvalidSessionIdException:
    #     pass

    # # sets up selenium driver with correct Chrome headless version
    # os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    # options = webdriver.ChromeOptions()
    # # options.headless = True
    # driver = webdriver.Chrome(ChromeDriverManager(version="94.0.4606.41").install(), options=options)
    # url = URL_PREFIX + "real2"
    # driver.get(url)
    # # enter_text_answer("real1", driver, 2, "3", "arithmetic")
    # # test_step("real2", driver, 2, "\\frac{24}{5}", "arithmetic")


# python3 test_page.py real2 "\\frac{24}{5}" "TextBox arithmetic" "\\frac{25}{6}" "TextBox arithmetic"
# python3 test_page.py matrices3 "$$\\begin{bmatrix} 1 & 14 \\\\ 86 & 109 \\\\ 27 & 10 \\end{bmatrix}$$" "TextBox arithmetic"
# python3 test_page.py matrices4 "$$\\begin{bmatrix} -64 & -12 & -28 & -72 \\\\ -360 & -20 & -12 & -116 \\end{bmatrix}$$" "TextBox arithmetic"
# python3 test_page.py matrices14 "$$\\begin{bmatrix} a+e & b+f \\\\ c+g \\\\ d+h \\end{bmatrix}$$" "TextBox arithmetic"
# python3 test_page.py rates6 "2" "TextBox arithmetic" "-2" "TextBox arithmetic"
# python3 test_page.py whole2 "104,000" "TextBox arithmetic" "104,000" "TextBox arithmetic" "100000" "TextBox arithmetic"

