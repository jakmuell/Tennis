import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import os
import time

options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome('/Users/ursulamachtel/PycharmProjects/weather_selenium/chromedriver')
links = []
filepath = '/Users/ursulamachtel/Downloads/players.csv' # Spieler Namen Liste
with open(filepath,'r+') as fi: #Namens Liste wird eingelesen
        reader = csv.DictReader(fi,delimiter =';')
        for row in reader:
            First = row['First']
            Last  = row['Last']
            driver.implicitly_wait(5)  # Wartet falls nächstes Element noch nicht verfügbar
            url = 'https://www.atptour.com/en/search-results/players?searchTerm={}%20{}'.format(First,Last) #First und Last Name in URL einfügen
            try:
                driver.get(url)
                elems = driver.find_elements_by_css_selector(".result-name [href]")
                link = [elem.get_attribute('href') for elem in elems]  # URL der Overview Seite des Spielers
            except:
                link = 'NA'

            links.append(link)

file = open('player_names_output.csv', 'w+', newline='')

# writing the data into the file
with file:
    write = csv.writer(file)
    write.writerows(links)
    
