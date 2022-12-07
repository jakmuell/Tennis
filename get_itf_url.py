import csv
import itertools
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time


 #Holt sich die Urls von allen Turnieren über die Jahre in years und holt sich danach von
# den Turnieren, die 'Print' Version URLs speichert diese in einer csv Datei

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome('/Users/lukaschagas/Documents/PyCharm/chromedriver')
links = []
years = [2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021]
wait = WebDriverWait(driver, 10)

for i in years:
    for j in range(1,13):
        url = 'https://www.itftennis.com/en/tournament-calendar/mens-world-tennis-tour-calendar/?startdate={}-{}'.format(i,j)
        try:
            driver.get(url)
            titles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/en/tournament/m']")))
            link = [title.get_attribute("href") for title in titles]  # URL der Overview Seite des Spielers
        except:
            link = 'NA'
        links.append(link)

links = list(itertools.chain(*links))  #Wandele Liste von Liste in normale Liste um
print(links)


tournaments = []

for i in links:
    try:
        driver.get('i')
        titles = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='event.itftennis']")))
        tournament = [title.get_attribute("href") for title in titles]
    except:
        tournaments='NA'
    tournaments.append(tournament)

print()
file = open('tournament_names_output.csv', 'w+', newline='')
with file:
    write = csv.writer(file)
    write.writerows([tournaments])





