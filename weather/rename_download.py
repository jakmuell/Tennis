import os
import glob
import csv

filepath = '/Users/lukaschagas/PycharmProjects/weather_selenium/seleniumproject/URLs/url_panama.csv'

def rename_download(country,number):
    path = 'Users/lukaschagas/Desktop/weather_python/{}{}'.format(country, number)  # Ordner mit den Downloads aus Chrome(in Chrome festlegen)
    files = glob.glob('Users/lukaschagas/Desktop/weather_python/{}{}/*.gz'.format(country,number))
    files.sort(key=os.path.getmtime)  # Sortieren der Files nach Download Zeit
    print("\n".join(files))
    filepath = '/Users/lukaschagas/PycharmProjects/pythonProject/weather/urlwetter/url_{}.csv'.format(country)
    with open(filepath, 'r') as fi:   # In der Reihenfolge der Urls umbenennung der gedownloadeten files
        reader = csv.DictReader(fi, delimiter=';')
        for f,row in zip(files,reader):
            url = row['URL']
            file_name, file_ext = os.path.splitext(f)
            new_name = 'Users/lukaschagas/Desktop/weather_python/{}{}/{}.xls{}'.format(country,number,url, file_ext)
            os.renames(f,new_name)
    return

rename_download('australia','1')
