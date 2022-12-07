import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import os
import time

options = webdriver.ChromeOptions()
options.add_argument("headless") #Alle Befehle in einem Fenster ausführen
driver = webdriver.Chrome('/Users/lukaschagas/Documents/PyCharm/chromedriver')
os.chdir('/Users/lukaschagas/Desktop/weather_python')

def weather_downloader(Start,End,country):
    filepath = '/Users/lukaschagas/Desktop/urlwetter/url_{}.csv'.format(country)  # URL Liste der Stationen

    with open(filepath,'r') as fi:
        reader = csv.DictReader(fi,delimiter =';')
        for row in reader:
            url = row['URL']
            print(url)
            driver.implicitly_wait(7)  # Wartet bis Download Button erscheint
            driver.get(url)
            try:
                driver.find_element_by_id('tabSynopDLoad').click()  # Tab wechseln
            except NoSuchElementException:
                driver.find_element_by_id('tabMetarDLoad').click()


            ArchDate1 = driver.find_element_by_name('ArchDate1')  # Datum aendern
            ArchDate2 = driver.find_element_by_name('ArchDate2')
            ArchDate1.clear()
            ArchDate2.clear()
            ArchDate1.send_keys(Start) #Startdatum

            ArchDate2.send_keys(End) # Enddatum
            ArchDate2.send_keys(Keys.ENTER)
            ArchDate2.clear()
            ArchDate2.send_keys(End) # Enddatum

            try:
                driver.find_element_by_xpath("//div[text()='Select to file GZ (archive)']").click() # Download vorbereiten druecken
            except NoSuchElementException:
                driver.find_element_by_xpath("//div[text()='In eine Datei holen GZ (Archiv)']").click() # Falls Sprache Deutsch eingestellt ist
            try:
               driver.find_element_by_xpath("//a[text()='Download']").click()  # Download klicken
            except NoSuchElementException:
               time.sleep(5)
               driver.refresh()
               driver.find_element_by_xpath("//div[text()='Select to file GZ (archive)']").click()
               time.sleep(5)
               driver.find_element_by_xpath("//a[text()='Download']").click()  # Download
    return

weather_downloader('01.07.2020','17.03.2021','sanmarino')

