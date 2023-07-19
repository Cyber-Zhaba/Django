import os
import sys
from datetime import datetime

import django
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

proj = os.path.dirname(os.path.abspath('manage.py'))
sys.path.append(proj)
os.environ["DJANGO_SETTINGS_MODULE"] = "scraping_service.settings"
django.setup()

from scraping.models import Vacancy, Error, Url
from scraping_service.settings import EMAIL_HOST_USER

subject = f'Рассылка вакансий за {datetime.today().strftime("%Y-%m-%d")}'
text_content = 'Рассылка вакансий'
from_email = EMAIL_HOST_USER
empty = '<h2>К сожалению на сегодня по Вашим предпочтениям данных нет.</h2>'
User = get_user_model()
qs = User.objects.filter(send_email=True).exclude(city__isnull=True).exclude(
    language__isnull=True).values('city', 'language', 'email')
users_dct = {}
for i in qs:
    users_dct.setdefault((i['city'], i['language']), [])  # noqa
    users_dct[(i['city'], i['language'])].append(i['email'])
if users_dct:
    params = {'city_id__in': [], 'language_id__in': []}
    for pair in users_dct.keys():
        params['city_id__in'].append(pair[0])
        params['language_id__in'].append(pair[1])
    qs = Vacancy.objects.filter(**params, timestamp=datetime.today()).values()
    vacancies = {}
    for i in qs:
        vacancies.setdefault((i['city_id'], i['language_id']), [])  # noqa
        vacancies[(i['city_id'], i['language_id'])].append(i)
    for keys, emails in users_dct.items():
        rows = vacancies.get(keys, [])
        html = ''
        for row in rows:
            if row['url']:
                html += f'<h5><a href="{row["url"]}">{row["title"]}</a></h5>'
                html += f'<p>{row["description"]}</p>'
                html += f'<p>{row["company"]}</p><br><hr>'
        html = html if html else empty
        for email in emails:
            ...
            # to = email
            # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            # msg.attach_alternative(html, "text/html")
            # msg.send()

qs = Error.objects.filter(timestamp=datetime.today())
subject = ''
text_content = ''
html = ''
to = get_user_model().objects.filter(is_admin=True).values('email')[0]['email']
if qs.exists():
    html += '<h2>Ошибки</h2>'
    error = qs.first()
    data = error.data.get('errors', [])
    for i in data:
        html += f'<p><a href="{i["url"]}">Error: {i["title"]}</a></p><br>'
    subject = f'Ошибки скрапинга {datetime.today().strftime("%Y-%m-%d")} '
    text_content = 'Ошибки скрапинга'
    data = error.data.get('user_data', [])
    if data:
        html += '<hr>'
        html += '<h2>Пожелания пользователей</h2>'
        for i in data:
            html += f'<p>Город: {i["city"]}, Специальность: {i["language"]}, Email: {i["email"]}</p><br>'
        subject += 'Пожелания пользователей '
        text_content += 'Пожелания пользователей '

qs = Url.objects.all().values('city', 'language')

urls_dct = {(i['city'], i['language']): True for i in qs}
urls_err = ''
for keys in users_dct.keys():
    if keys not in urls_dct:
        urls_err += f'<p>Для города: {keys[0]} и языка программирования: {keys[1]} отсутствуют урлы</p><br>'
if urls_err:
    subject += 'Отсутствующие урлы'
    html += urls_err

if subject:
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html, "text/html")
    msg.send()
