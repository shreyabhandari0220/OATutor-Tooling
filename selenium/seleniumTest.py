from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

import time

def generate_script(selector, answer):
    script = "document = new Document();\n"
    script += "ans = document.querySelector(\"{}\");\n".format(selector)
    script += "var MQ = MathQuill.getInterface(2);\n"
    script += "mathField = MQ.MathField(ans);\n"
    script += "mathField.typedText('{}');\n".format(answer)
    return script


options = webdriver.ChromeOptions()
# options.headless = True
driver = webdriver.Chrome(ChromeDriverManager(version="92.0.4515.107").install(), 
    options=options)

CORRECT = "https://image.flaticon.com/icons/svg/148/148767.svg"
WRONG = "https://image.flaticon.com/icons/svg/148/148766.svg"

driver.get("https://matthew29tang.github.io/OpenITS/#/debug/real1")

ans1_selector = "#root > div > div > div > div:nth-child(2) > div > div.MuiCardContent-root > div.jss220 > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-9.MuiGrid-grid-md-3 > center > span"
submit1_selector = "#root > div > div > div > div:nth-child(2) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-4.MuiGrid-grid-md-2 > center > button"
icon1_selector = "#root > div > div > div > div:nth-child(2) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-3.MuiGrid-grid-md-1 > div > img"
ans1 = driver.find_element_by_css_selector(ans1_selector)
submit1 = driver.find_element_by_css_selector(submit1_selector)

script1 = generate_script(ans1_selector, "3")
driver.execute_script(script1, ans1)

submit1.click()
time.sleep(0.5)
icon1 = driver.find_element_by_css_selector(icon1_selector)
if icon1.get_attribute("src") != CORRECT:
    print("Invalid answer for part 1")


ans2_selector = "#root > div > div > div > div:nth-child(3) > div > div.MuiCardContent-root > div.jss220 > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-9.MuiGrid-grid-md-3 > center > span"
submit2_selector = "#root > div > div > div > div:nth-child(3) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-4.MuiGrid-grid-md-2 > center > button"
icon2_selector = "#root > div > div > div > div:nth-child(3) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-3.MuiGrid-grid-md-1 > div > img"
ans2 = driver.find_element_by_css_selector(ans2_selector)
submit2 = driver.find_element_by_css_selector(submit2_selector)

# script2 = generate_script(ans2_selector, "sqrt13")
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('^2');\n"
# script2 += "mathField.keystroke('Right');\n"
# script2 += "mathField.typedText('/25');"
script2 = generate_script(ans2_selector, "0.52")
driver.execute_script(script2, ans2)

submit2.click()
time.sleep(0.5)
icon2 = driver.find_element_by_css_selector(icon2_selector)
if icon2.get_attribute("src") != CORRECT:
    print("Invalid answer for part 2")


correct_ans3 = "-0.71"
for i in range(1, 5):
    ans3_selector = "#root > div > div > div > div:nth-child(4) > div > div.MuiCardContent-root > div.jss220 > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-9.MuiGrid-grid-md-11 > div > fieldset > div > label:nth-child({}) > span.MuiTypography-root.MuiFormControlLabel-label.MuiTypography-body1".format(str(i))
    ans3_choice_selector = "#root > div > div > div > div:nth-child(4) > div > div.MuiCardContent-root > div.jss220 > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-9.MuiGrid-grid-md-11 > div > fieldset > div > label:nth-child({}) > span.MuiButtonBase-root.MuiIconButton-root.jss269.MuiRadio-root.MuiRadio-colorSecondary.MuiIconButton-colorSecondary".format(str(i))
    try:
        ans3 = driver.find_element_by_css_selector(ans3_selector)
        if ans3.text == correct_ans3:
            ans3_choice = driver.find_element_by_css_selector(ans3_choice_selector)
            ans3_choice.click()
    except NoSuchElementException:
        break

submit3_selector = "#root > div > div > div > div:nth-child(4) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-4.MuiGrid-grid-md-2 > center > button"
icon3_selector = "#root > div > div > div > div:nth-child(4) > div > div.MuiCardActions-root.MuiCardActions-spacing > div > div.MuiGrid-root.MuiGrid-item.MuiGrid-grid-xs-4.MuiGrid-grid-sm-3.MuiGrid-grid-md-1 > div > img"
submit3 = driver.find_element_by_css_selector(submit3_selector)
submit3.click()
time.sleep(0.5)
icon3 = driver.find_element_by_css_selector(icon3_selector)
if icon3.get_attribute("src") != CORRECT:
    print("Invalid answer for part 3")


# driver.close()

