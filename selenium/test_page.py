from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

import time
import sys
import os

from generate_script import generate_script_arithmetic

URL_PREFIX = "https://matthew29tang.github.io/OpenITS/#/debug/"
CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"


def test_page(problem_name, ans_and_type, driver):
    url = URL_PREFIX + problem_name
    driver.get(url)

    problem_index = 2

    for correct_answer, problem_type in ans_and_type:
        test_step(problem_name, driver, problem_index, correct_answer, problem_type)
        problem_index += 1


def test_step(problem_name, driver, problem_index, correct_answer, problem_type):

    # Enter step answer
    if problem_type.split()[0] == "TextBox":
        enter_text_answer(problem_name, driver, problem_index, correct_answer, problem_type.split()[1])
    elif problem_type.split()[0] == "MultipleChoice":
        enter_mc_answer(problem_name, driver, problem_index, correct_answer)
    else:
        print('{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index - 1, problem_type))
        problem_index += 1

    # click submit and check correctness  
    try:
        submit_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[3]/center/button".format(problem_index)
        icon_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[4]/div/img".format(problem_index)
        submit = driver.find_element_by_xpath(submit_selector)
        submit.click()
        time.sleep(0.2)
        icon = driver.find_element_by_xpath(icon_selector)
        if icon.get_attribute("src") != CORRECT:
            print("{0}: Invalid answer for step {1}: {2}".format(problem_name, problem_index - 1, correct_answer))
    except NoSuchElementException:
        print("{0}: step {1} submit does not exist.".format(problem_name, problem_index - 1))

    # click through hints
    try:
        raise_hand_button_xpath = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[2]/div/div[2]/center/button".format(problem_index)
        raise_hand_button = driver.find_element_by_xpath(raise_hand_button_xpath)
        raise_hand_button.click()
        time.sleep(0.2)
        hint_idx = 1
        while True:
            hint_xpath = "//*[@id=\"root\"]/div[1]/div/div/div[{0}]/div/div[1]/div[2]/div/div[{1}]".format(problem_index, hint_idx)
            hint_expand_button = driver.find_element_by_xpath(hint_xpath)
            hint_expand_button.click()
            time.sleep(0.2)
            # try:
            #     scaffold_hint_xpath = "//*[@id=\"panel1a-content\"]/div/span/div/div/div[1]/div[2]/center/span"
            #     scaffold_hint = driver.find_element_by_xpath(scaffold_hint_xpath)

            
            # except NoSuchElementException:
            #     pass

            hint_idx += 1
            
    except Exception as e:
        if type(e) == NoSuchElementException:
            return
        print(e)

def enter_text_answer(problem_name, driver, problem_index, correct_answer, answer_type):
    """
    Enters type TextBox answers into text box.
    """
    if answer_type == "arithmetic":
        ans_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/center/span".format(problem_index)
        try:
            ans = driver.find_element_by_xpath(ans_selector)
            script = generate_script_arithmetic(ans_selector, correct_answer)
            driver.execute_script(script, ans)
        except NoSuchElementException:
            print(ans_selector)
            print("{0}: step {1} arithmetic answer box does not exist.".format(problem_name, problem_index - 1))
            return

    elif answer_type == "string":
        ans_selector = "//*[@id=\"root\"]/div[1]/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div/div/input".format(problem_index)
        try:
            ans = driver.find_element_by_xpath(ans_selector)
            ans.send_keys(correct_answer)
        except NoSuchElementException:
            print("{0}: step {1} string answer box does not exist.".format(problem_name, problem_index - 1))
            return

    else:
        print("{0}: step {1} answer box type not defined: {2}".format(problem_name, problem_index - 1, answer_type))

    


def enter_mc_answer(problem_name, driver, problem_index, correct_answer):
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
                print("{0}: Answer choice appears more than once: {1}".format(problem_name, ans))
            else:
                all_choices.append(ans)

            if ans == correct_answer:
                ans_choice = driver.find_element_by_xpath(ans_choice_selector)
                ans_choice.click()

        except NoSuchElementException:
            break
        
        choice_idx += 1


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
    test_page(problem_name, info_list, driver)

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


# python3 test_page.py real2 "\\frac{24}{5}" TextBox "\\frac{25}{6}" TextBox
# python3 test_page.py factor11 "(2x-5)(4x**2 + 10x + 25)" TextBox
