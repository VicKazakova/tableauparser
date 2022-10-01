import re
from pprint import pprint

from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests
from pymongo.errors import DuplicateKeyError

url = 'https://hh.ru/search/vacancy'

client = MongoClient('127.0.0.1', 27017)
db = client['hh_jobs']

vacancies = db.vacancies
# job = input('Enter the job position: ')
job = 'HR'

headers = \
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/96.0.4664.110 Safari/537.36'}
params = {'clusters': 'true',
          'area': 1,
          'ored_clusters': 'true',
          'enable_snippets': 'true',
          'salary': None,
          'text': job,
          'page': 1,
          'hhtmFrom': 'vacancy_search_list'}

while True:
    response = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    if not soup.find('a', {'data-qa': 'pager-next'}):
        break

    jobs = soup.find_all('div', {'class': 'vacancy-serp-item'})
    for job in jobs:
        job_data = {}
        info = job.find('a')
        name = info.text
        link = info.get('href')
        salary = job.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if salary is not None:
            new_salary = str(salary.text)
            if 'от' in new_salary:
                min_salary = int(re.sub("[^a-z0-9а-яА-Я]+", "", new_salary.split(' ')[1], flags=re.IGNORECASE))
                max_salary = None
                currency = new_salary.split(' ')[2]
            elif 'до' in new_salary:
                min_salary = None
                max_salary = int(re.sub("[^a-z0-9а-яА-Я]+", "", new_salary.split(' ')[1], flags=re.IGNORECASE))
                currency = new_salary.split(' ')[2]
            else:
                min_salary = int(re.sub("[^a-z0-9а-яА-Я]+", "", new_salary.split(' ')[0], flags=re.IGNORECASE))
                max_salary = int(re.sub("[^a-z0-9а-яА-Я]+", "", new_salary.split(' ')[2], flags=re.IGNORECASE))
                currency = new_salary.split(' ')[3]
        else:
            min_salary = None
            max_salary = None
            currency = None
        try:
            company = job.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).text
            print(company)
            new_company = re.sub("[^a-z0-9а-яА-Я]+", " ", company, flags=re.IGNORECASE)
        except AttributeError:
            new_company = None
        location = job.find('div', {'data-qa': 'vacancy-serp__vacancy-address'}).text

        job_data['_id'] = link[22:30]
        job_data['name'] = name
        job_data['link'] = link
        job_data['company'] = new_company
        job_data['location'] = location
        job_data['min_salary'] = min_salary
        job_data['max_salary'] = max_salary
        job_data['currency'] = currency

        try:
            vacancies.insert_one(job_data)
        except DuplicateKeyError:
            pass
            # print('already in the base') -- for double-check

    params['page'] += 1

for doc in vacancies.find({}):
    pprint(doc)
