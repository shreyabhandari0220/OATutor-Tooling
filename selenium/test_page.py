from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

import time
import sys
import os

from generate_script import generate_script

URL_PREFIX = "https://matthew29tang.github.io/OpenITS/#/debug/"
CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"


def test_page(problem_name, ans_and_type, driver):
    url = URL_PREFIX + problem_name

    # # sets up selenium driver with correct Chrome headless version
    # os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    # options = webdriver.ChromeOptions()
    # options.headless = True
    # driver = webdriver.Chrome(ChromeDriverManager(version="92.0.4515.107").install(), options=options)
    driver.get(url)

    problem_index = 2

    for correct_answer, problem_type in ans_and_type:
        # enter/select answer
        if problem_type == "TextBox":
            enter_text_answer(problem_name, driver, problem_index, correct_answer)
        elif problem_type == "MultipleChoice":
            enter_mc_answer(problem_name, driver, problem_index, correct_answer)
        else:
            print('{0}: Wrong answer type for step {1}: {2}'.format(problem_name, problem_index - 1, problem_type))
            problem_index += 1
            continue

        # click submit and check correctness
        submit_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[3]/center/button".format(problem_index)
        icon_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[4]/div/img".format(problem_index)
        try:
            submit = driver.find_element_by_xpath(submit_selector)
            submit.click()
            time.sleep(0.5)
            icon = driver.find_element_by_xpath(icon_selector)
            if icon.get_attribute("src") != CORRECT:
                print("{0}: Invalid answer for step {1}".format(problem_name, problem_index - 1))
        except NoSuchElementException:
            print("{0}: step {1} submit does not exist.".format(problem_name, problem_index - 1))

        problem_index += 1
    
    # try:
    #     driver.close()
    # except InvalidSessionIdException:
    #     pass


def enter_text_answer(problem_name, driver, problem_index, correct_answer):
    """
    Enters type TextBox answers into text box.
    """
    ans_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/center/span".format(problem_index)
    try:
        ans = driver.find_element_by_xpath(ans_selector)
    except NoSuchElementException:
        try:
            ans_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/div".format(problem_index)
            ans = driver.find_element_by_xpath(ans_selector)
        except NoSuchElementException:
            print("{0}: step {1} answer box does not exist.".format(problem_name, problem_index - 1))
            return

    script = generate_script(ans_selector, correct_answer)
    driver.execute_script(script, ans)


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
    driver = webdriver.Chrome(ChromeDriverManager(version="92.0.4515.107").install(), options=options)
    
    test_page(problem_name, info_list, driver)

    try:
        driver.close()
    except InvalidSessionIdException:
        pass
