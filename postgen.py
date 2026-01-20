import asyncio
import json
import os
import random
import string

from yandex_cloud_ml_sdk import YCloudML
from alarm import alarm, info

global dict_ready

def generate_random_promt():
    # Определяем набор символов: буквы (строчные и прописные), цифры и некоторые специальные символы
    characters = string.ascii_letters + string.digits + string.punctuation
    # Генерируем случайную длину строки в диапазоне от 1 до 150
    length = random.randint(1, 150)
    # Генерируем случайную строку
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def check_history():
    file_path = r"C:\Bots\commonData\importmath\messages.json"
    if os.path.isfile(file_path):
        return True
    else:
        return False

def getMessages():
    if check_history() == True:

        with open(r"C:\Bots\commonData\importmath\messages.json", "r", encoding='utf-8') as read_file:
            messages = json.load(read_file)

    else:
        with open(r"C:\Bots\commonData\importmath\promt.madata", "r", encoding='utf-8') as read_file:
            serv_promt = read_file.read()
        with open(r"C:\Bots\commonData\importmath\firstpromt.json", "r", encoding='utf-8') as read_file:
            messages = json.load(read_file)
            if messages[1]["text"] == "{{generate_random_promt()}}":
                messages[0]["text"] = serv_promt
                messages[1]["text"] = "Темы, которые нужно избегать: "
                info.put(f"Запущено новое формирование списка пропускаемых тем")
    return messages



async def newTextPost():
    try:
        with open(r'C:\Bots\commonData\importmath\folderid.madata', 'r', encoding='utf-8') as file:
            folder_id = file.read()
        with open(r'C:\Bots\commonData\importmath\yapiid.madata', 'r', encoding='utf-8') as file:
            yapiid = file.read()
    except:
        alarm.put("Ошибка в блоке чтения промт и Яндекс данных")

    try:
        info.put("Запуск генерации ИИ")
        sdk = YCloudML(folder_id=folder_id, auth=yapiid)
        model = sdk.models.completions("yandexgpt", model_version="rc")
        model = model.configure(temperature=0.3)
    except:
        alarm.put("Ошибка Яндекс авторизации")
    try:
        messages = getMessages()
    except:
        alarm.put("Ошибка подгрузки промта")
    try:
        result = model.run(messages)
        info.put("Успешно получен результат генерации")
    except:
        alarm.put("Ошибка получения генерации")

    try:
        for alternative in result:
            text = alternative.text

            return text

    except:
        alarm.put("Ошибка обработки результата генерации")

def addNewBlock(text:str = None):
    if text is not None:
        with open(r"C:\Bots\commonData\importmath\messages.json", "r", encoding='utf-8') as read_file:
            messages = json.load(read_file)
        messages[1]["text"] = messages[1]["text"] + " " + text + "; "
        with open(r"C:\Bots\commonData\importmath\messages.json", "w", encoding='utf-8') as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)

def RawToDict(raw_post):
    #with open(r"C:\Bots\commonData\importmath\testresult.madata", "r", encoding='utf-8') as file:
        #raw_post = file.read()
    lines = raw_post.split('\n')
    result = {}

    # Поиск строки для ключа "title"
    for line in lines:
        if line.startswith('^^^'):
            result['title'] = line.replace('^', '')
            title_index = lines.index(line)
            break
        else:
            alarm.put("Ошибка генерации RAW - title")
            result['title'] = None  # Если строка с "^^^" не найдена

    addNewBlock(result['title'])

    # Получение "raw_text"
    try:
        raw_text_start = title_index + 1
        raw_text_end = next(i for i, line in enumerate(lines) if 'elements:' in line)
        result['raw_text'] = '\n'.join(lines[raw_text_start:raw_text_end])
        if "{осн}" in result['raw_text']:
            result['raw_text'] = result['raw_text'].replace("{осн}", "{OCH}")


    except StopIteration:
        alarm.put("Ошибка генерации RAW - raw_text")
        result['raw_text'] = None  # Если строка с "elements:" не найдена

    # Получение "att_key" и "att_link"
    try:
        # Поиск строки, содержащей "elements:"
        elements_line_index = next(i for i, line in enumerate(lines) if 'elements:' in line)
        elements_line = lines[elements_line_index]
        try:
            for line in lines[elements_line_index:len(lines)]:
                if "=" in line:
                    result['att_key'], result['att_link'] = line.split('=', maxsplit=1)
                    if "и" in result['att_link']:
                        result['att_link'] = result['att_link'].replace("и", "")
                    break
        except:
            alarm.put(r"Ошибка генерации RAW - внутренняя att_key/att_link")

    except:

        result['att_key'] = None
        result['att_link'] = None

    # Проверка на наличие двух символов "$" для "is_latex"
    result['is_latex'] = any(line.count('$') >= 2 for line in result['raw_text'].split('\n')) or len(result["raw_text"])>900 if result[
        'raw_text'] else False

    info.put(f"Результат генерации:\n{result}")
    return result


#оживи это и начнется магия
async def generateContent():
    raw_text_post = await newTextPost()
    global dict_ready
    dict_ready = RawToDict(raw_text_post) #для оживления добавь аргумент
    if dict_ready['raw_text'] is None or dict_ready['is_latex'] is None or not dict_ready['att_key'] or not dict_ready['att_link'] or not dict_ready['title']:
        alarm.put(r"Ошибка генерации RAW - не хватает ключа")
    else:
        return dict_ready



#asyncio.run(generateContent())