import json
import os
import shutil
from io import BytesIO

from PIL import Image
from alarm import alarm, debugin, info
import requests
import sympy


#formlat = r"f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}"
def LatexTitleBytes(formlat, ismath):
    buf = BytesIO()
    # Генерируем изображение с помощью sympy.preview
    # Для этого сначала сохраняем в временный файл, а затем читаем его в буфер
    temp_filename = 'temp_image.png'
    try:
        sympy.preview(f"$${formlat}$$", viewer='file', filename=temp_filename, dvioptions=['-D', '1000'])
    except:
        alarm.put("Ошибка при рендеринге титульной формулы")
    image = Image.open('temp_image.png').convert('RGBA')
    # Удаляем временный файл
    try:
        os.remove(temp_filename)
    except:
        debugin.put("Ошибка при удалении временного файла титульной формулы")

    if ismath == True:
        im2 = Image.open(r'C:\Bots\commonData\importmath\math2.png').convert('RGBA')
    else:
        im2 = Image.open(r'C:\Bots\commonData\importmath\code2.png').convert('RGBA')

    data = image.getdata()

    # Создаём новый список данных с прозрачным фоном
    new_data = []
    for item in data:
        # Проверяем, является ли пиксель белым
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            # Заменяем белый пиксель на прозрачный
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    # Обновляем изображение новыми данными
    image.putdata(new_data)
    width, height = image.size

    border_width = 4

    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    new_image = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 0))
    add_im = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 0))
    add_im.paste(image, (border_width, border_width), image)
    image = add_im
    del add_im
    # Проходим по пикселям и определяем границы
    for y in range(new_height):
        for x in range(new_width):
            pixel = image.getpixel((x, y))
            if pixel[3] > 0:  # Если пиксель непрозрачный
                # Проверяем соседние пиксели на прозрачность
                for dx in range(-border_width, border_width + 1):
                    for dy in range(-border_width, border_width + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < new_width and 0 <= ny < new_height:
                            neighbor_pixel = image.getpixel((nx, ny))
                            if neighbor_pixel[3] == 0:  # Если соседний пиксель прозрачный
                                new_image.putpixel((nx, ny), (255, 255, 255, 255))  # Закрашиваем белым

    # Вставляем исходное изображение поверх обводки
    new_image.paste(image, (0, 0), image)
    image = new_image
    del new_image

    width_image, height_image = image.size

    new_width = width_image + 20
    width_im2, height_im2 = im2.size
    aspect_ratio = height_im2 / width_im2
    new_height = int(new_width * aspect_ratio)
    if new_height < height_image + 20:
        new_height = height_image + 20
        new_width = int(new_height / aspect_ratio)

    im2_resized = im2.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Рассчитать координаты для вставки image по центру
    x = (new_width - width_image) // 2
    y = (new_height - height_image) // 2

    im2_resized.paste(image, (x, y), image)
    ar = new_width / new_height
    if new_width > 1200 or new_height > 1200:
        if new_width > new_height:
            new_width = 1200
            new_height = int(1200 / ar)
        else:
            new_height = 1200
            new_width = int(1200 * ar)

        final_image = im2_resized.resize((new_width, new_height), Image.Resampling.LANCZOS)
    else:
        final_image = im2_resized

    final_image.save(buf, format="PNG")
    buf.seek(0)

    return buf

#Делаем изображение BYTESIO из LATEX формулы (без $$)
def latexBytes(formlat):
    buf = BytesIO()
    # Генерируем изображение с помощью sympy.preview
    # Для этого сначала сохраняем в временный файл, а затем читаем его в буфер
    temp_filename = 'temp_image.png'
    sympy.preview(f"$${formlat}$$", viewer='file', filename=temp_filename, dvioptions=['-D', '200'])
    # Читаем изображение в буфер BytesIO
    with open(temp_filename, 'rb') as f:
        shutil.copyfileobj(f, buf)
    # Устанавливаем курсор в начало буфера
    buf.seek(0)
    # Удаляем временный файл
    os.remove(temp_filename)
    return buf



#в этом файле данные для входа в IMAGEBAN
with open(r"C:\Bots\commonData\importmath\imageban.json", "r", encoding='utf-8') as file:
    imgban = json.load(file)
    client_id, secret_key = imgban["client_id"], imgban["secret_key"]
    del imgban

#грузим наш BYTESIO в IMAGEBAN (с авторизацией) и выдаем ссылку
def upload_image_to_imageban(image_bytes, client_id, secret_key):
    url = 'https://api.imageban.ru/v1'
    headers = {
        'Authorization': f'Bearer {secret_key}'
    }
    files = {
        'image': image_bytes
    }
    params = {
        'secret_key': secret_key
    }
    for i in range(0,5):
        response = requests.post(url, headers=headers, files=files, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'success' in data:
                if data['success']:
                    info.put("Изображение загружено на IMAGEBAN успешно")
                    return data["data"]["link"] #def upload_image_to_imageban(image_bytes, client_id, secret_key):
                else:
                    debugin.put(f"Ошибка загрузки изображения на IMAGEBAN. Попытка {i + 1}/5")
            else:
                debugin.put(f"Ошибка загрузки изображения на IMAGEBAN. Попытка {i+1}/5")
        else:
            alarm.put("Ошибка загрузки LATEX " + str(response.status_code))
            return 0

#основная функция запуска модуля, подаем LATEX функцию без $$, получаем ссылку
def convertLatex(func):
    bytes_image = latexBytes(func)
    link = upload_image_to_imageban(bytes_image, client_id, secret_key)
    return link

def convertLatexTitle(func,title):
    if "математ" in title.lower():
        ismath = True
    else:
        ismath = False
    bytes_image = LatexTitleBytes(func, ismath)
    link = upload_image_to_imageban(bytes_image, client_id, secret_key)
    return link
