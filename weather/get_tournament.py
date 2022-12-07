import csv
import itertools
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome('/Users/lukaschagas/Documents/PyCharm/chromedriver')
wait = WebDriverWait(driver, 10)

tournaments = []
filepath = '/Users/lukaschagas/PycharmProjects/pythonProject/Tennis_Data/url_tournament'
with open(filepath, 'r+') as fi:  # Namens Liste wird eingelesen
    reader = csv.DictReader(fi, delimiter=',')
    for row in reader:
        url = row['URL']
        tournaments.append(url)

tournaments = [s for s in tournaments if s != 'NA']
tournaments = [s for s in tournaments if s != 'A']
tournaments = [s for s in tournaments if s != 'N']
tournaments = [s for s in tournaments if s != '']

urls = []
for i in tournaments:
    driver.get(i)
    try:
        titles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='tournamentprintabledrawsheets.aspx?tournamentid=']")))
        url = [title.get_attribute("href") for title in titles]
    except:
        url='NA'
    urls.append(url)
    print(len(urls))


file = open('tournament_urls.csv', 'w+', newline='')
with file:
    write = csv.writer(file)
    write.writerows(urls)


