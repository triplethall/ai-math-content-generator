import asyncio
import json
import re

from alarm import alarm, info, debugin
from image_search import imageSearch
from latex_link import convertLatex, convertLatexTitle
from postgen import generateContent
from telegraph import create_telegraph_article

def planTelegraph(title, raw_text, image_list, n):
    info.put("Генерация TELEGRAPH статьи")
    tgrph = create_telegraph_article(title, raw_text, image_list, n)
    print(tgrph)
    return tgrph

def has_cyrillic(s):
    return bool(re.search(r'[а-яА-Я]', s))

#генерация поста
async def firstGen():
    dict_ready = await generateContent()
    info.put("Сгенерирован словарь RAW поста")
    if dict_ready["att_key"] == "search":
        pics = await imageSearch(dict_ready["att_link"])
        with open(r"C:\Bots\commonData\importmath\pics.json", "r", encoding="utf-8") as f:
            base = json.load(f)
        info.put("Для поста сгенерирован список изображений из поиска")
        dict_ready['pics'] = pics + base
    if dict_ready["att_key"] == "formula" or dict_ready["att_key"] == "graph":
        if has_cyrillic(dict_ready["att_link"]):
            debugin.put("Допустимая ошибка генерации: кириллица в LATEX выражении для изображения")
            try:
                with open(r"C:\Bots\commonData\importmath\pics.json", "r", encoding="utf-8") as f:
                    pics = json.load(f)
                dict_ready['pics'] = pics
            except:
                alarm.put("Ошибка чтения файла PICS")
        else:
            info.put("Формирование LATEX титульного изображения")
            pics = convertLatexTitle(dict_ready["att_link"].replace("$",''),dict_ready['title'])

            with open(r"C:\Bots\commonData\importmath\pics.json", "r", encoding="utf-8") as f:
                base = json.load(f)
            dict_ready['pics'] = [pics] + base

    if dict_ready["is_latex"] == True:
        info.put("Зафиксирована необходимость использования TELEGRAPH-статьи (наличие LATEX)")
        tgrph = planTelegraph(dict_ready["title"], dict_ready["raw_text"], dict_ready['pics'], 0)
        dict_ready['tgrph'] = tgrph
    elif dict_ready["is_latex"] == False:
        info.put("Зафиксировано отсутствие LATEX, пост без использования TELEGRAPH")

    else:
        alarm.put("Ошибка по проверке LATEX")
    info.put(f"Пост скомпилирован, тема {dict_ready['title']}")
    return dict_ready

