import json
import queue
import re

import requests

from alarm import alarm, debugin, info

from latex_link import convertLatex

def has_cyrillic(s):
    return bool(re.search(r'[а-яА-Я]', s))



with open(r"C:\Bots\commonData\importmath\telegraph_t.madata", "r") as f:
    tph_token = f.read()


def create_telegraph_article(title, raw_text, image_list, n):
    #Подготовка контента
    dumper = []
    dumper.append(title)
    article_content = []

    # Добавляем первое изображение
    if image_list:
        dumper.append(image_list)
        article_content.append({
            'tag': 'img',
            'attrs': {'src': image_list[n]}
        })

    # Обрабатываем raw_text
    lines = raw_text.split('\n')

    for line in lines:
        if line.count("$")%2 == 0:
            if line.count("$") == 0:
                article_content.append({'tag': 'p', 'children': [line]}) #проверь на практике, надо ли line в список совать
            else:
                tag_line = line.split("$")
                blank = 0
                pos = 0
                for i, item in enumerate(tag_line):
                    if i%2 == 0:
                        if blank == 0 and pos != i-1:
                            if len(item) == 1 and ("," or "-" in item or '.' in item):
                                item = ''
                            if len(item) >= 1:
                                if item[0] == "." or item[0] == ",":
                                    item = item[1:]
                            article_content.append({'tag': 'p', 'children': [item]})
                        if blank == 1 and pos == i-1:
                            blank = 0
                            article_content[-1]["children"][0] = article_content[-1]["children"][0] + item
                    if i%2 == 1 and not ((item.isupper() and re.fullmatch(r'[A-ZA-ЯЁ0-9]+', item)) or (len(item) == 1 and (item.isalpha() or item.isdigit()))):
                        if has_cyrillic(item):
                            alarm.put(f"Кириллица во внутренней функции: {item}")
                        item = convertLatex(item)
                        article_content.append({
                            'tag': 'img',
                            'attrs': {'src': item }
                        })
                    if i % 2 == 1 and ((item.isupper() and re.fullmatch(r'[A-ZA-ЯЁ0-9]+', item)) or (len(item) == 1 and (item.isalpha() or item.isdigit()))):
                        #article_content[-1]["children"][0] = article_content[-1]["children"][0] + " **" + item + "**"
                        article_content[-1]["children"].append({"tag": "b", "children": [item]})
                        blank = 1
                        pos = i
        else:
            alarm.put("Нечетное количество $ в генерации!")
            break

    dumper.append(article_content)
    #Создание статьи в Telegraph
    create_article_response = requests.post(
        'https://api.telegra.ph/createPage',
        json={
            'access_token': tph_token,
            'title': title,
            'content': article_content,
            'return_content': True
        }
    )
    with open("tempdump.json", "w", encoding='utf-8') as f:
        json.dump(dumper, f, ensure_ascii=False, indent=4)
        info.put("Создан временный дамп-файл")
    if create_article_response.status_code != 200:
        raise Exception('Ошибка создания статьи в Telegraph: {}'.format(create_article_response.text))
    article_data = create_article_response.json()
    return article_data['result']['url']

def changepic(n):
    debugin.put(f"Начало функции смены изображения TELEGRAPH")
    with open("tempdump.json", "r", encoding='utf-8') as f:
        dumper = json.load(f)
        info.put("Выгружен временный дамп из файла")
    tit = dumper[0]
    imgs = dumper[1]
    article_content = dumper[2]
    debugin.put(f"Приняты данные из дампа")
    article_content[0] = {
        'tag': 'img',
        'attrs': {'src': imgs[n]}
    }
    debugin.put(f"Отправка запроса")
    create_article_response = requests.post(
        'https://api.telegra.ph/createPage',
        json={
            'access_token': tph_token,
            'title': tit,
            'content': article_content,
            'return_content': True
        }
    )
    if create_article_response.status_code != 200:
        raise Exception('Ошибка создания статьи в Telegraph: {}'.format(create_article_response.text))
    article_data = create_article_response.json()
    return article_data['result']['url']
