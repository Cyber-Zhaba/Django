import asyncio
import os
import sys
from datetime import datetime

import django
from django.contrib.auth import get_user_model
from django.db import DatabaseError

proj = os.path.dirname(os.path.abspath('manage.py'))
sys.path.append(proj)
os.environ["DJANGO_SETTINGS_MODULE"] = "scraping_service.settings"
django.setup()

from scraping.parser import *
from scraping.models import Vacancy, Error, Url

User = get_user_model()

parsers = (
    (hh, 'hh'),
    (rabota, 'rabota'),
)

jobs, errors = [], []


def get_settings():
    qs = User.objects.filter(send_email=True).values()
    settings_lst = set((q['city_id'], q['language_id']) for q in qs if q['city_id'] and q['language_id'])
    return settings_lst


def get_urls(_settings):
    qs = Url.objects.all().values()  # noqa
    url_dict = {(q['city_id'], q['language_id']): q['url_data'] for q in qs}
    urls = []
    for pair in _settings:
        if pair in url_dict:
            tmp = {
                'city': pair[0],
                'language': pair[1],
                'url_data': url_dict[pair]
            }
            urls.append(tmp)
    return urls


async def main(value):
    func, url_, city, language = value
    job_, err = await loop.run_in_executor(None, func, url_, city, language)
    jobs.extend(job_)
    errors.extend(err)


settings = get_settings()
url_list = get_urls(settings)

loop = asyncio.get_event_loop()
tmp_task = [(func, data['url_data'][key], data['city'], data['language'])
            for data in url_list
            for func, key in parsers]
tasks = asyncio.wait([loop.create_task(main(f)) for f in tmp_task])

# for data in url_list:
#     for func, key in parsers:
#         url = data['url_data'][key]
#         j, e = func(url, city=data['city'], language=data['language'])
#         jobs += j
#         errors += e

loop.run_until_complete(tasks)
loop.close()

for job in jobs:
    v = Vacancy(**job)
    try:
        v.save()
    except DatabaseError:
        pass

if errors:
    qs = Error.objects.filter(timestamp=datetime.today())
    if qs.exists():
        err = qs.first()
        err.data.update({'errors': errors})
        err.save()
    else:
        er = Error(data=f'errors:{errors}').save()
