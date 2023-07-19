import requests
from bs4 import BeautifulSoup as BS
from user_agent import generate_user_agent

__all__ = ('hh', 'rabota')


def hh(url, city=None, language=None):
    headers = {'User-Agent': generate_user_agent(device_type="desktop", os=('mac', 'linux')),
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    jobs = []
    errors = []
    if url:
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            main_div = soup.find('div', attrs={'data-qa': 'vacancy-serp__results'})
            if main_div:
                div_list = main_div.find_all('div', attrs={'class': 'serp-item'})
                for div in div_list:
                    title = div.find('a', attrs={'class': 'serp-item__title', 'data-qa': 'serp-item__title'}).text
                    href = div.find('a', attrs={'class': 'serp-item__title', 'data-qa': 'serp-item__title'})['href']

                    content_exp = div.find('div', attrs={'data-qa': 'vacancy-serp__vacancy-work-experience'})
                    content_respons = div.find('div', attrs={'data-qa': 'vacancy-serp__vacancy_snippet_responsibility'})
                    content_req = div.find('div', attrs={'data-qa': 'vacancy-serp__vacancy_snippet_requirement'})

                    conten_l = []
                    if content_exp:
                        conten_l.append(content_exp.text)
                    if content_respons:
                        conten_l.append(content_respons.text)
                    if content_req:
                        conten_l.append(content_req.text)
                    content = '\n'.join(conten_l)

                    company = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'})
                    if company:
                        company = company.text.replace('ООО\xa0', '')

                    jobs.append(dict(title=title, url=href, description=content, company=company, city_id=city,
                        language_id=language))
            else:
                errors.append({'url': url, 'title': 'Div do not response'})
        else:
            errors.append({'url': url, 'title': 'Page do not response'})

    return jobs, errors


def rabota(url, city=None, language=None):
    headers = {'User-Agent': generate_user_agent(device_type="desktop", os=('mac', 'linux')),
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    jobs = []
    errors = []
    domain = 'https://www.rabota.ru'
    if url:
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            soup = BS(resp.content, 'html.parser')
            main_div = soup.find('main', attrs={'class': 'page__main vacancy-search-page__main'})
            if main_div:
                div_list = main_div.find_all('div', attrs={'class': 'r-serp__item r-serp__item_vacancy'})
                for div in div_list:
                    title = div.find('a', attrs={'class': 'vacancy-preview-card__title_border'}).text.replace('\n',
                                                                                                              '').strip(
                        ' ')
                    href = div.find('a', attrs={'class': 'vacancy-preview-card__title_border'})['href']
                    content = div.find('div', attrs={'class': 'vacancy-preview-card__short-description'}).text

                    company_span = div.find('span', attrs={'class': 'vacancy-preview-card__company-name'})
                    company = (company_span.find('a').text if company_span else 'No name').replace('\n', '').strip(' ')

                    jobs.append(dict(title=title, url=domain + href, description=content, company=company, city_id=city,
                        language_id=language))  # noqa
            else:
                errors.append({'url': url, 'title': 'Div do not response'})
        else:
            errors.append({'url': url, 'title': 'Page do not response'})

    return jobs, errors


if __name__ == '__main__':
    from pprint import pprint

    pprint(hh('https://hh.ru/search/vacancy?text=Python&area=1&enable_snippets=True&customDomain=1')[0])
