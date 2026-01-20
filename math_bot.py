import json
import asyncio
import concurrent.futures
import queue  # Для совместимости с API multiprocessing.Queue
from telethon import TelegramClient, events, Button
import PIL
from alarm import info, debugin, alarm, set_log_queue
from content_manager import firstGen
from medium import download_temp_image, deleteContext
from telegraph import create_telegraph_article, changepic

with open(r"C:\Bots\commonData\importmath\channel.madata", "r", encoding='utf-8') as f:
    channel_id = int(f.readline())

migration = asyncio.Queue()
CONFIG_PATH = r"C:\Bots\commonData\importmath\bot.madata"
APPROVED_IDS_PATH = r"C:\Bots\commonData\importmath\idsapprove.json"


# Функция для загрузки конфига
def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_approved_ids():
    with open(APPROVED_IDS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return set(data)
    else:
        return set(data.get('approved_ids', []))



def compose_message(item):
    if item['is_latex'] == False:
        item["caption"] = f"**{item["title"]}**\n{item['raw_text']}\n\n **Готовимся к экзаменам вместе на [import math](https://t.me/panichkaexam)🎯**"
    if item['is_latex'] == True:
        item["caption"] = f"**{item['title']}**\n\n**Читать в [telegraph]({item['tgrph']})** (лучше открывать в браузере)\n\n **Готовимся к экзаменам вместе на [import math](https://t.me/panichkaexam)🎯**"

def recompose_telegraph(msg, n):
    debugin.put(f"Запущена рекомпозиция статьи")
    msg["tgrph"] = changepic(n)
    debugin.put(f"Рекомпозиция сообщения")
    compose_message(msg)

async def create_client():
    config = load_config()
    api_id = config['api_id']
    api_hash = config['api_hash']
    bot_token = config['token']

    client = TelegramClient('bot_session', api_id, api_hash)
    await client.start(bot_token=bot_token)
    return client



async def main(broadcast_queue):
    approved_ids = load_approved_ids()
    client = await create_client()

    info.put("Бот запущен.")

    @client.on(events.CallbackQuery)
    async def callback_handler(event):
        await event.answer()


        try:
            orig = await event.get_message()
            await orig.delete()
        except:
            pass


        data = event.data.decode('utf-8') if event.data else ''


        chatid = event.chat_id
        if data == "nextimg":
            debugin.put("Зафиксирована команда на смену изображения")
            msg,imgnum = await migration.get()
            if len(msg['pics']) == 1:
                return
            if imgnum < len(msg['pics'])-1:
                imgnum = imgnum + 1
            else:
                imgnum = 0

            buttons = []
            if len(msg['pics']) > 1:
                buttons.append(Button.inline(f"Смена 🌄 {imgnum + 1}/{len(msg['pics'])}", data="nextimg"))
            buttons.append(Button.inline(f"Следующая генерация", data="newgen"))
            buttons.append(Button.inline(f"Готово", data="post"))
            debugin.put(f"Проверка новой позиции изображения: {imgnum}")
            if msg['is_latex'] == True:
                debugin.put(f"Начало рекомпозиции TELEGRAPH статьи")
                recompose_telegraph(msg,imgnum)

            await migration.put((msg, imgnum))
            link = download_temp_image(msg["pics"][imgnum])
            debugin.put(f"Сборка и отправка обновленного сообщения")
            for user_id in approved_ids:
                for i in range (0,5):
                    try:
                        await client.send_file(
                            user_id,
                            link,
                            caption=msg["caption"],
                            parse_mode='markdown',
                            disable_web_page_preview=True,
                            buttons=buttons
                        )
                        info.put(f"Отправлено {user_id}: {msg['title']}")
                        break
                    except Exception as e:
                        debugin.put(f"Ошибка отправки {user_id}: {e}")
                        await client.send_message(user_id, f"Ошибка отправки {user_id}: {e}\nImg url: {msg["pics"][imgnum]} ", buttons=Button.inline(f"Смена 🌄 {imgnum + 1}/{len(msg['pics'])}", data="nextimg"))
        elif data == "newgen":
            info.put("Получена команда на создание нового поста")
            new_post = await firstGen()
            info.put(f"Замена поста: {new_post["title"]}")
            compose_message(new_post)
            imgnum=0
            buttons = []
            if len(new_post['pics']) > 1:
                buttons.append(Button.inline(f"Смена 🌄 {imgnum + 1}/{len(new_post['pics'])}", data="nextimg"))
            buttons.append(Button.inline(f"Следующая генерация", data="newgen"))
            buttons.append(Button.inline(f"Готово", data="post"))
            if not migration.empty():
                while not migration.empty():
                    hole = await migration.get()
                del hole

            await migration.put((new_post, imgnum))
            sent=False
            link = download_temp_image(new_post["pics"][imgnum])
            for user_id in approved_ids:
                try:
                    await client.send_file(
                        user_id,
                        link,
                        caption=new_post["caption"],
                        parse_mode='markdown',
                        disable_web_page_preview=True,
                        buttons=buttons
                    )
                    info.put(f"Отправлено {user_id}: {new_post['title']}")
                    sent = True
                except Exception as e:
                    debugin.put(f"Ошибка отправки {user_id}: {e}")
                    await client.send_message(user_id,f"Ошибка отправки {user_id}: {e}\nImg url: {new_post["pics"][imgnum]} ", buttons = Button.inline(f"Следующая генерация", data="newgen"))
                    debugin.put(f"Img url: {new_post["pics"][imgnum]}")
                    sent = False
                if sent == True:
                    break
            return
        elif data == "post":
            info.put("Отправка поста на канал")
            msg, imgnum = await migration.get()
            if not migration.empty():
                while not migration.empty():
                    hole = await migration.get()
                del hole
            link = download_temp_image(msg["pics"][imgnum])
            for i in range(0, 5):
                try:
                    await client.send_file(
                        channel_id,
                        link,
                        caption=msg["caption"],
                        parse_mode='markdown',
                        disable_web_page_preview=False
                    )
                    info.put(f"Отправлено в import math: {msg['title']}")
                    break
                except Exception as e:
                    debugin.put(f"Ошибка отправки в канал: {e}")
        elif data == "delcont":
            mess = deleteContext()
            for user_id in approved_ids:
                await client.send_message(user_id, mess,
                                      buttons=Button.inline(f"Следующая генерация", data="newgen"))

        else:
            await client.send_message(chatid, "Нажата неизвестная кнопка")

    @client.on(events.NewMessage)
    async def handler(event):

        sender_id = event.sender_id
        if sender_id is None:
            return
        if sender_id == channel_id:
            return
        message_text = event.raw_text or ""
        await event.delete()
        if sender_id not in approved_ids:
            reply_msg = await event.reply("Go away. This bot is not for you. Forget you were here. You are not welcome here. You are not wanted here.")
            await asyncio.sleep(5)
            await reply_msg.delete()
            return

        if message_text.startswith('/start'):
            button = [Button.inline(f"Новая генерация", data="newgen")]
            button.append(Button.inline(f"Очистить контекст", data="delcont"))
            reply_msg = await event.reply("Бот запущен, можно сгенерировать пост. \nКонтекст удалять только в самом крайнем случае.", buttons=button)
            await asyncio.sleep(60)
            await reply_msg.delete()
        else:
            reply_msg = await event.reply("Этот бот не принимает сообщения.")
            await asyncio.sleep(5)
            await reply_msg.delete()

    async def broadcast_loop():
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        while True:
            try:

                def get_from_queue():
                    try:
                        msg = broadcast_queue.get_nowait()
                        info.put(f"Размер очереди после get: {broadcast_queue.qsize()}")  # Отладка
                        return msg
                    except queue.Empty:
                        return None

                msg = await loop.run_in_executor(executor, get_from_queue)
                imgnum = 0
                if msg is not None:
                    info.put(f"Получено из очереди для рассылки: {msg["title"]}")
                    compose_message(msg)
                    buttons = []
                    if len(msg['pics']) > 1:
                        buttons.append(Button.inline(f"Смена 🌄 {imgnum + 1}/{len(msg['pics'])}", data = "nextimg"))
                    buttons.append(Button.inline(f"Следующая генерация", data="newgen"))
                    buttons.append(Button.inline(f"Готово", data="post"))
                    await migration.put((msg, imgnum))
                    link = download_temp_image(msg["pics"][imgnum])
                    sent = False
                    for i in range (0,5):
                        for user_id in approved_ids:
                            try:
                                await client.send_file(
                                    user_id,
                                    link,  # URL изображения как photo
                                    caption=msg["caption"],  # Текст как подпись (caption)
                                    parse_mode='markdown',
                                    disable_web_page_preview= True,
                                    buttons = buttons
                                )
                                info.put(f"Отправлено {user_id}: {msg['title']}")
                                sent = True
                            except Exception as e:
                                debugin.put(f"Ошибка отправки {user_id}: {e}")
                                debugin.put(f"Img url: {msg["pics"][imgnum]}")
                                await client.send_message(user_id, f"Ошибка отправки {user_id}: {e}", buttons = Button.inline(f"Следующая генерация", data="newgen"))
                        if sent == True:
                            break
                        #broadcast_queue.task_done()
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                alarm.put(f"Ошибка в broadcast_loop: {e}")
                await asyncio.sleep(1)

    broadcast_task = asyncio.create_task(broadcast_loop())

    await client.run_until_disconnected()
    broadcast_task.cancel()


def run_main_sync(broadcast_queue,l_queue):
    set_log_queue(l_queue)

    # Теперь все вызовы info.put() из этого процесса пойдут куда надо
    info.put("Процесс бота успешно запущен и настроил логирование.")
    asyncio.run(main(broadcast_queue))