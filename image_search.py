import asyncio
import base64
import re
import requests

#query = 'правильная четырёхугольная пирамида стереометрия рисунок'

def decode_yandex_search_response(base64_response):
    # Декодирование Base64
    xml_bytes = base64.b64decode(base64_response)
    xml_str = xml_bytes.decode('utf-8')
    return xml_str

def send_yandex_image_request(iam_token, body_json):
    url = "https://searchapi.api.cloud.yandex.net/v2/image/search"
    headers = {
        "Authorization": f"Bearer {iam_token}"
    }
    response = requests.post(url, headers=headers, json=body_json)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при отправке запроса: {response.status_code}")
        return None

def urlList(response):
    pattern = r'<url>(.*?)</url>'
    # Находим все совпадения в тексте
    url_list = re.findall(pattern, response)
    # Возвращаем список ссылок
    return url_list


async def imageSearch(query):
    with open(r'C:\Bots\commonData\importmath\folderid.madata', 'r', encoding='utf-8') as file:
        folder_id = file.read()
    with open(r'C:\Bots\commonData\importmath\yapiid_admin.madata', 'r', encoding='utf-8') as file:
        iam_token = file.read()
    body_json = {
      "query": {
        "searchType": "SEARCH_TYPE_RU",
        "queryText": query
      },
      "docsOnPage": 10,
      "folderId": folder_id
    }
    base64_response = send_yandex_image_request(iam_token, body_json)
    response = decode_yandex_search_response(base64_response["rawData"])
    url_list = urlList(response)
    print(url_list)
    return url_list

#asyncio.run(imageSearch(query))