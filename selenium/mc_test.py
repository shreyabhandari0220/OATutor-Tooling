from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException
from selenium.webdriver.common.action_chains import ActionChains
import os


# sets up selenium driver with correct Chrome headless version
os.environ['WDM_LOG_LEVEL'] = '0'  # suppress logs from ChromeDriverManager install
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(ChromeDriverManager(version="96.0.4664.45").install(), options=options)
driver.get("https://cahlr.github.io/OATutor-Staging/#/debug/a7ea646graph1")

sel = "//*[@id=\"root\"]/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/div/fieldset/div/label[1]/span[2]"
choice = driver.find_element_by_xpath(sel)
print(choice.text)
