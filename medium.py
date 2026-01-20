import requests
import os
import mimetypes

from alarm import info, debugin

def deleteContext():
    file_path = r'C:\Bots\commonData\importmath\messages.json'

    if os.path.exists(file_path):
        os.remove(file_path)
        return(f"Файл {file_path} успешно удалён.")
    else:
        return(f"Файл {file_path} не найден.")

def download_temp_image(url: str) -> str:

    folder = r"C:\Bots\commonData\importmath\temp"

    # Создаем папку, если её нет
    os.makedirs(folder, exist_ok=True)

    try:
        # Скачиваем изображение
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Проверяем на HTTP-ошибки

        # Получаем MIME-тип
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError("URL не указывает на изображение")

        # Определяем расширение
        extension = mimetypes.guess_extension(content_type)
        if not extension:
            # Fallback для распространенных типов
            if 'jpeg' in content_type:
                extension = '.jpg'
            elif 'png' in content_type:
                extension = '.png'
            elif 'gif' in content_type:
                extension = '.gif'
            else:
                extension = '.jpg'  # По умолчанию

        # Имя файла
        filename = 'temp' + extension
        filepath = os.path.join(folder, filename)

        # Сохраняем
        with open(filepath, 'wb') as f:
            f.write(response.content)

        info.put(f"Изображение скачано: {filepath}")
        return filepath

    except requests.RequestException as e:
        debugin.put(f"Ошибка загрузки: {e}")
    except Exception as e:
        debugin.put(f"Общая ошибка: {e}")

    return r"https://cdn-icons-png.flaticon.com/512/5741/5741824.png"