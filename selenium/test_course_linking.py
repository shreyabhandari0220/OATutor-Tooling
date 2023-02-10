from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from test_page import start_driver

def test_course_linking(driver):
    PROD_URL = "https://cahlr.github.io/OATutor/#/"
    driver.get(PROD_URL)

    idx = 1
    course_name_format = '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div[{}]/center/div/h2'
    course_button_format = '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div[{}]/center/div/button'
    while True:

        # Click into course
        course_name_xpath = course_name_format.format(idx)
        course_button_xpath = course_button_format.format(idx)
        try:
            course_name = driver.find_element(By.XPATH, course_name_xpath).text
            course_button = driver.find_element(By.XPATH, course_button_xpath)
            course_button.send_keys(Keys.SPACE)
        except NoSuchElementException:
            break

        # Click into the first lesson
        lesson_xpath = '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div/center/div/button'
        try:
            lesson_button = driver.find_element(By.XPATH, lesson_xpath)
            lesson_button.send_keys(Keys.SPACE)
        except NoSuchElementException:
            continue

        actual_course = driver.execute_script("return document['oats-meta-courseName']")
        actual_lesson = driver.execute_script("return document['oats-meta-textbookName']")
        print("expected: {}, course: {}, lesson: {}".format(course_name, actual_course, actual_lesson))

        driver.get(PROD_URL)

        idx += 1

if __name__ == '__main__':
    driver = start_driver()
    test_course_linking(driver)

