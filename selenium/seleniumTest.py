from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

import time
import re

def generate_script(selector, answer):
    selector = re.sub(r"\"", "\\\"", selector)
    script = "document = new Document();\n"
    script += "ans = document.evaluate(\"{}\", document, null, 9, null).singleNodeValue;\n".format(selector)
    script += "var MQ = MathQuill.getInterface(2);\n"
    script += "mathField = MQ.MathField(ans);\n"
    script += "mathField.typedText('{}');\n".format(answer)
    return script


options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome(ChromeDriverManager(version="92.0.4515.107").install(), 
    options=options)

CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"

driver.get("https://matthew29tang.github.io/OpenITS/#/debug/real1")

ans1_selector = "//*[@id=\"root\"]/div/div/div/div[2]/div/div[1]/div[2]/div/div[2]/center/span"
ans1 = driver.find_element_by_xpath(ans1_selector)
submit1_selector = "//*[@id=\"root\"]/div/div/div/div[2]/div/div[2]/div/div[3]/center/button"
icon1_selector = "//*[@id=\"root\"]/div/div/div/div[2]/div/div[2]/div/div[4]/div/img"
submit1 = driver.find_element_by_xpath(submit1_selector)
script1 = generate_script(ans1_selector, "3")
driver.execute_script(script1, ans1)

submit1.click()
time.sleep(0.5)
icon1 = driver.find_element_by_xpath(icon1_selector)
if icon1.get_attribute("src") != CORRECT:
    print("Invalid answer for part 1")


ans2_selector = "//*[@id=\"root\"]/div/div/div/div[3]/div/div[1]/div[2]/div/div[2]/center/span"
submit2_selector = "//*[@id=\"root\"]/div/div/div/div[3]/div/div[2]/div/div[3]/center/button"
icon2_selector = "//*[@id=\"root\"]/div/div/div/div[3]/div/div[2]/div/div[4]/div/img"
ans2 = driver.find_element_by_xpath(ans2_selector)
submit2 = driver.find_element_by_xpath(submit2_selector)

# script2 = generate_script(ans2_selector, "sqrt13")
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('^2');\n"
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('/25');"
script2 = generate_script(ans2_selector, "0.52")
driver.execute_script(script2, ans2)

submit2.click()
time.sleep(0.5)
icon2 = driver.find_element_by_xpath(icon2_selector)
if icon2.get_attribute("src") != CORRECT:
    print("Invalid answer for part 2")


correct_ans3 = "-0.71"
for i in range(1, 5):
    ans3_selector = "//*[@id=\"root\"]/div/div/div/div[4]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{}]/span[2]".format(str(i))
    ans3_choice_selector = "//*[@id=\"root\"]/div/div/div/div[4]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[{}]/span[1]".format(str(i))
    try:
        ans3 = driver.find_element_by_xpath(ans3_selector)
        if ans3.text == correct_ans3:
            ans3_choice = driver.find_element_by_xpath(ans3_choice_selector)
            ans3_choice.click()
    except NoSuchElementException:
        break

submit3_selector = "//*[@id=\"root\"]/div/div/div/div[4]/div/div[2]/div/div[3]/center/button"
icon3_selector = "//*[@id=\"root\"]/div/div/div/div[4]/div/div[2]/div/div[4]/div/img"
submit3 = driver.find_element_by_xpath(submit3_selector)
submit3.click()
time.sleep(0.5)
icon3 = driver.find_element_by_xpath(icon3_selector)
if icon3.get_attribute("src") != CORRECT:
    print("Invalid answer for part 3")


driver.close()