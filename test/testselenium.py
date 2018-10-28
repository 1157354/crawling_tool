#coding=utf-8
#select下拉框处理
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
#导入select方法
from selenium.webdriver.support.select import Select

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
# driver=webdriver.Chrome(chrome_options = chrome_options)
driver=webdriver.Chrome()
# driver.get("http://www.chinalaw.gov.cn/col/col12/index.html")
driver.get('http://www.chinalaw.gov.cn/col/col12/index.html?uid=1648&pageNum=1')
wait = WebDriverWait(driver, 8)

# next = wait.until(EC.element_to_be_clickable(
#                                 (By.XPATH, '//a[contains(text(), "下页") or contains(text(), "下一页")]')))
# # next = wait.until(EC.element_to_be_clickable(
# #                                 (By.XPATH, '/html/body/div[5]/div[1]/div[2]/div/div/a[3]')))
# # next = wait.until(EC.element_to_be_clickable(
# #                                 (By.XPATH, '//*[contains(text(), "下一页")]')))
# next.click()
# time.sleep(2)
input_xpath = '//*[@id="1648"]/table/tbody/tr/td/table'
try:
    _next = wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//a[contains(text(), "下页") or contains(text(), "下一页")]')))
    print(1)
    _next.click()
    print(2)
except Exception as e:
    print(3)
    try:
        print(4)
        input = wait.until(
            EC.presence_of_element_located((By.XPATH, input_xpath + "//input[@type='text']")))
        print(5)
        logging(input)
        print(6)
        input.clear()
        input.send_keys(str(2))
        input.send_keys(Keys.ENTER)  # 回车键(ENTER)
    except Exception as e:
        print('error:',e)

# input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath + "//input[@type='text']")))
# print(input)
# input.clear()
# input.send_keys(str(2))
# time.sleep(1)
# input.send_keys(Keys.ENTER)






#隐式等待10秒
# driver.implicitly_wait(10)
# #鼠标移动到"设置"按钮
# mouse=driver.find_element_by_link_text("设置")
# ActionChains(driver).move_to_element(mouse).perform()
# #点击"搜索设置"
# driver.find_element_by_link_text("搜索设置").click()
# #强制等待4秒，注意：这里使用隐式等待或显式等待都将无法获取元素
# time.sleep(4)
#分两步，先定位下拉框，再点击选项
# choice = driver.find_element_by_name("NR")
# Select(choice).select_by_index(2)
# time.sleep(2)
# driver.find_element_by_xpath("//div[@id='gxszButton']/a[1]").click()
# time.sleep(2)
# driver.switch_to.alert.accept()
# #跳转到百度首页后，进行搜索表
# driver.find_element_by_id('kw').send_keys("python")
# driver.find_element_by_id('su').click()