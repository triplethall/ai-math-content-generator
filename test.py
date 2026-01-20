import json

with open(r"C:\Bots\commonData\importmath\messages.json", "r", encoding='utf-8') as read_file:
    messages = json.load(read_file)
print(messages)