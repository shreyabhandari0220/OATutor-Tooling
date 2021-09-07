from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

import time
import os

from generate_script import generate_script

URL_PREFIX = "https://matthew29tang.github.io/OpenITS/#/debug/"
CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"


def test_page(problem_name, ans_and_type):
    url = URL_PREFIX + problem_name

    # sets up selenium driver with correct Chrome headless version
    os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(ChromeDriverManager(version="92.0.4515.107").install(), options=options)
    driver.get(url)

    problem_index = 2

    for correct_answer, problem_type in ans_and_type:
        # enter/select answer
        if problem_type == "TextBox":
            enter_text_answer(driver, problem_index, correct_answer)
        elif problem_type == "MultipleChoice":
            enter_mc_answer(driver, problem_index, correct_answer)

        # click submit and check correctness
        submit_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[3]/center/button".format(problem_index)
        icon_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[2]/div/div[4]/div/img".format(problem_index)
        try:
            submit = driver.find_element_by_xpath(submit_selector)
            submit.click()
            time.sleep(0.5)
            icon = driver.find_element_by_xpath(icon_selector)
            if icon.get_attribute("src") != CORRECT:
                print("Invalid answer for part: {}".format(str(problem_index - 1)))
        except NoSuchElementException:
            print("Problem {} does not exist.".format(problem_index - 1))

        problem_index += 1
    
    try:
        driver.close()
    except InvalidSessionIdException:
        pass


def enter_text_answer(driver, problem_index, correct_answer):
    """
    Enters type TextBox answers into text box.
    """
    ans_selector = "//*[@id=\"root\"]/div/div/div/div[{}]/div/div[1]/div[2]/div/div[2]/center/span".format(problem_index)
    try:
        ans = driver.find_element_by_xpath(ans_selector)
    except NoSuchElementException:
        print("Problem {} does not exist.".format(problem_index - 1))
    script = generate_script(ans_selector, correct_answer)
    driver.execute_script(script, ans)


def enter_mc_answer(driver, problem_index, correct_answer):
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
            ans = driver.find_element_by_xpath(ans_selector).text.split('\n')[0]

            if ans in all_choices:
                print("Answer choice appears more than once: {}".format(ans))
            else:
                all_choices.append(ans)

            if ans == correct_answer:
                ans_choice = driver.find_element_by_xpath(ans_choice_selector)
                ans_choice.click()

        except NoSuchElementException:
            break
        
        choice_idx += 1


if __name__ == '__main__':
    test_page("real3", [["0", "MultipleChoice"], ["$$\\frac{0}{4}$$", "MultipleChoice"], ["Set of Irrational Numbers", "MultipleChoice"]])
