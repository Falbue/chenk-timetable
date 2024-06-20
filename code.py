bot_api = ''
folder = 'data'
id_admin = 1
# -----------------------------------------------------------


import os
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot
import re
from datetime import datetime
import pytz
import sys
import re
sys.path.append(folder)
import threading
bot = telebot.TeleBot(bot_api)


# пути
folder_path = f"{folder}"
db_name = "database.db"
db_path = os.path.join(folder_path, db_name)
texts_path = f"{folder}/texts"
menu_user_path = f'{folder}/user_menu'
menu_dev_path = f'{folder}/telegram_text_apps_menu'
error_path = f'{texts_path}/error_log.txt'
command_path = f'{folder}/command'

object_menu = {'Текст':'text', 'Кнопки':'buttons', 'Возврат':'back', 'Тип меню':'typemenu', 'Команда':'command'}
buttons_edit_menu = {key: f'admin_rename-object-{value}_[file-name]' for key, value in object_menu.items()}

dev_menu = [
    {"name": "admin", "text": 'Панель администратора', 'buttons': {'Настройка меню': 'admin_settings-menu', 'Управление командами': 'admin_control-command'}, 'back': 'main'},
    {"name": "settings-menu", "text": 'Найстройки меню', 'buttons': {'Редактировать': 'admin_list-edit-menu', '+ Создать': 'admin_create-menu', '× Удалить ': 'admin_delete-menu'}, 'back': 'admin'},
    {"name": "list-edit-menu", "text": 'Выберите меню, которое хотите отредактировать', 'buttons': {'[menu_lists]': 'admin_edit-menu'}, 'back': 'settings-menu'},
    {"name": "create-menu", "text": 'Введите название меню/n/nНазвание меню <u>не должно</u> содержать  <b>_</b> и <b>-</b> !', 'back': 'settings-menu', 'type_menu': 'insert_text', 'command': 'create_menu'},
    {"name": "delete-menu", "text": 'Выберите меню для удаления', 'buttons': {'[menu_lists]': 'admin_delete-menu'}, 'back': 'settings-menu'},
    {"name": "edit-menu", "text": '<b>Выбранное меню:</b> [file-name]/n/n[file-data]/n/nВыберите, что нужно изменить:', 'buttons': buttons_edit_menu, 'back': 'list-edit-menu'},
    {"name": "rename-object", "text": '<b>Введите:</b> [object-menu]', 'back': 'edit-menu_[file-name]', 'type_menu': 'insert_text', 'command': 'rename_menu'},
    {"name": "control-command", "text": 'Выберите, нужное действие', 'buttons':{'Список команд': 'admin_list-commands', 'Добавить команду': 'admin_add-command', 'Удалить команду': 'admin_list-delete-command'}, 'back': 'admin'},
    {"name": "add-command", "text": 'Введите команду либо загрузите python файл', 'back': 'control-command', 'type_menu': 'insert_text', 'command': 'create_command'},
    {"name": "list-delete-command", "text": 'Выберите, какую команду нужно удалить', 'buttons': {'[command_lists]': 'admin_delete-command'}, 'back': 'control-command'},
    {"name": "list-commands", "text": 'Все добавленные команды', 'buttons': {'[command_lists]': 'admin_open-command'},  'back': 'control-command'},
    {"name": "open-command", "text": '[file-code]', 'back': 'list-commands'},
]

# основные функции
def main_check(): # основные проверки
    if not os.path.exists(f"{folder}"):
        os.makedirs(f"{folder}")
        print("Папка библиотеки создана")
    if not os.path.exists(texts_path):
        os.makedirs(texts_path)
        print("Папка текстов создана")
    if not os.path.exists(menu_user_path):
        os.makedirs(menu_user_path)
        print("Папка с пользовательскими меню создана")
    if not os.path.exists(menu_dev_path):
        os.makedirs(menu_dev_path)
        print("Папка c меню приложения создана")   
    if not os.path.exists(command_path):
        os.makedirs(command_path)
        print("Папка с командами создана")   
    if not os.path.exists(error_path):
        with open(error_path, 'w'): 
            pass
        print("Файл с логами ошибок создан")
    if not os.path.exists(f'{menu_user_path}/main.txt'):
        create_menu('main', 'Главное меню') # создание главного меню
        print('Главное меню создано!')
    if not os.path.exists(db_path):
        conn = sqlite3.connect(f"{folder}/database.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                user_id INTEGER,
                time_registration INTEGER,
                id_message INTEGER);
            ''')
        conn.close()
        print("База данных создана")

    create_dev_menu()

def now_time(): # получение текущего времени
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M")
    current_date = now_moscow.strftime("%m.%d.%Y")
    date = f"{current_date} {current_time}"
    return date

def markdown_text(text, call): # mardown разметка 
    if '[file-name]' in text or '[object-menu]' in text:
        filename = call.data.split('_')[2]
        path = f'{menu_user_path}/{filename}.txt'
        if filename in [menu_item['name'] for menu_item in dev_menu]: path = f'{menu_dev_path}/{filename}.txt'
        with open(path, encoding='utf-8') as file:
            data = file.read()
        try:
            object_m = (call.data).split('-')[2].split('_')[0]
            for key, value in object_menu.items():
                if object_m in value:
                    object_m = key
                    text = text.replace('[object-menu]', object_m)
        except:pass
        text = text.replace('[file-name]', filename)
        text = text.replace('[file-data]', data)

    text = text.replace('/n', '\n')

    return(text)

def create_menu(name=None, text='Измените текст!', buttons=None, back='main', type_menu=None, command=None): # создание меню
    print(f'Создано меню: {name}')
    path = f'{menu_user_path}/{name}.txt'
    if name in [menu_item['name'] for menu_item in dev_menu]: 
        path = f'{menu_dev_path}/{name}.txt'
    if name == 'main':
        back = None

    with open(path, 'w+', encoding='utf-8') as file:
        file.write(f'text: {text}\nbuttons: {buttons}\nback: {back}\ntype-menu: {type_menu}\ncommand: {command}')

def create_dev_menu(): # создание меню программы
    for menu in dev_menu:
        create_menu(
            name=menu.get('name'), 
            text=menu.get('text'), 
            buttons=menu.get('buttons'), 
            back=menu.get('back'),
            type_menu=menu.get('type_menu'),
            command=menu.get('command'),
        )

def open_data_menu(name): # получение всех данных из файла
    path = f'{menu_user_path}/{name}.txt'
    if name in [menu_item['name'] for menu_item in dev_menu]: 
        path = f'{menu_dev_path}/{name}.txt'
    if os.path.exists(path):
        with open(path, encoding='utf-8') as file:
            file_data = file.read()
            data = {}
            for line in file_data.splitlines():
                key, value = line.split(': ', 1)
                data[key.strip()] = value.strip()
    else:data = None
    return data

def create_keyboard(buttons, back): # создание клавиатуры
    keyboard = InlineKeyboardMarkup(row_width = 2)
    row_buttons = []
    if buttons != None:
        num_buttons = 0
        for button_text in buttons.keys():
            button = InlineKeyboardButton(text = button_text, callback_data = buttons[button_text])
            row_buttons.append(button)
            num_buttons += 1
            if num_buttons == 2:
                keyboard.add(*row_buttons)
                row_buttons = []
                num_buttons = 0
        if num_buttons > 0:
            keyboard.add(*row_buttons)
    if back != None:
        btn_return = InlineKeyboardButton(text = '< Назад', callback_data = f'return_{back}')
        keyboard.add(btn_return)
    return keyboard

def open_menu(name = None, call = None): # открытие меню в чате из файла
    # получение данных для меню
    data = open_data_menu(name)        
    if data != None:
        text = None if isinstance(data['text'], str) and data['text'] == 'None' else data['text']
        buttons = None if data['buttons'] == 'None' else data['buttons']
        back = None if isinstance(data['back'], str) and data['back'] == 'None' else data['back']
        type_menu = None if isinstance(data['type-menu'], str) and data['type-menu'] == 'None' else data['type-menu']
        command = None if isinstance(data['command'], str) and data['command'] == 'None' else data['command']

        # работа с текстом
        text = markdown_text(text, call)

        # работа с клавиатурами
        if buttons is not None and buttons:
            buttons = eval(buttons)
            if '[menu_lists]' in buttons:
                files = os.listdir(menu_user_path)
                new_buttons = {}
                for filename in files:
                    if buttons['[menu_lists]'].split('_')[1] == 'delete-menu' and filename == 'main.txt': continue
                    file_key = filename.split('.')[0]
                    new_buttons[file_key] = buttons['[menu_lists]'] + '_' + file_key
                buttons = new_buttons

            if '[command_lists]' in buttons:
                files = os.listdir(command_path)
                new_buttons = {}
                for filename in files:
                    file_key = filename.split('.')[0]
                    new_buttons[file_key] = buttons['[command_lists]'] + '_' + file_key
                buttons = new_buttons

            new_buttons = {}
            for key, value in buttons.items():
                if '[file-name]' in value:
                    new_value = markdown_text(value, call)
                    new_buttons[key] = new_value
                else:
                    new_buttons[key] = value
            buttons = new_buttons

        if back != None:
            back = markdown_text(back, call)
        keyboard = create_keyboard(buttons, back)
        try:
            if name == 'main' and id_admin == (call.chat.id):
                keyboard.add(InlineKeyboardButton(text = 'Администратор', callback_data = 'admin_admin'))
        except:
            if name == 'main' and id_admin == (call.message.chat.id):
                keyboard.add(InlineKeyboardButton(text = 'Администратор', callback_data = 'admin_admin'))
    
        # работа с типом меню
        if type_menu == 'insert_text':
            print(f'Ожидание ввода')
            x = f'command_{command}'
            bot.register_next_step_handler(call.message, globals()[x], call)
    
        # изменение сообщения
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = text, reply_markup = keyboard, parse_mode = 'HTML')
        except AttributeError as e: # этот код должен срабатывать, если в чате вообще нет сообщений
            bot.send_message(call.chat.id, text, reply_markup = keyboard, parse_mode = 'HTML')
            bot.delete_message(chat_id=call.chat.id, message_id=call.message_id)
        
    else:
        print(f"Меню {name} не найдено!")

def delete_menu(name, call): # удаление меню
    os.remove(f'{menu_user_path}/{name}.txt')
    print(f'Меню {name}.txt удалено!')
    notification('Меню удалено!', 'delete-menu', call = call)

def delete_command(name, call): # удаление меню
    name = name.replace('admin_delete-command_', '')
    os.remove(f'{command_path}/{name}.py')
    print(f'Команда {name}.py удалена!')
    notification('Команда удалена!', 'list-delete-command', call = call)
    bot.answer_callback_query(callback_query_id=call.id, text="Команда удалена!")

def notification(text=None, back=None, all_users=None, call=None): # вставка меню (без создания)
    buttons={}
    keyboard = create_keyboard(buttons, back)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = text, reply_markup = keyboard, parse_mode = 'HTML')

def command_create_menu(user_call, call):
    bot.delete_message(chat_id=user_call.chat.id, message_id=user_call.message_id)
    name = user_call.text
    create_menu(name)
    bot.answer_callback_query(callback_query_id=call.id, text="Меню успешно создано!")
    notification('Меню создано!', 'settings-menu', call = call)

def command_rename_menu(user_call, call):
    bot.delete_message(chat_id=user_call.chat.id, message_id=user_call.message_id)
    rename = (call.data).split('-')[2]
    rename = rename.split('_')[0]
    name = (call.data).split('_')[2]
    text = (user_call.text).replace('\n', '/n')
    if text == '':
        text = None

    if rename == 'buttons':
        text = text.replace(' ','')
        buttons = {}
        if text.count(',') > 0:
            elements = text.split(',')
            for element in elements:
                button_text, button_call = element.split(':')
                buttons[button_text] = f'user_{button_call}'
        elif text.count(',') > 0:
            element = text.split(',')
            button_text, button_call = element.split(':')
            buttons[button_text] = f'user_{button_call}'
        text = str(buttons)

    data = open_data_menu(name)
    data[rename] = text
    path = f'{menu_user_path}/{name}.txt'
    if name in [menu_item['name'] for menu_item in dev_menu]: 
        path = f'{menu_dev_path}/{name}.txt'
    with open(path, 'w', encoding='utf-8') as file:
        for key, value in data.items():
            file.write(f"{key}: {value}\n")

    open_menu('edit-menu', call = call)

def command_create_command(message, call):
    if message.document: # Обработка документа
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(f'{command_path}/{message.document.file_name}', 'wb') as new_file:
            new_file.write(downloaded_file)
    elif message.text:
        text_content = message.text
        existing_files = os.listdir(command_path)
        max_number = 0
        for file in existing_files:
            if file.startswith('command_') and file.endswith('.py'):
                try:
                    number = int(file[len('command_'):-len('.py')])
                    if number > max_number:
                        max_number = number
                except ValueError:
                    continue

        new_number = max_number + 1
        file_name = f'{command_path}/command_{new_number}.py'

        with open(file_name, 'w', encoding='utf-8') as text_file:
            text_file.write(text_content)

    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    bot.answer_callback_query(callback_query_id=call.id, text="Команда добавлена!")
    notification('Команда добавлена!', 'control-command', call=call)

@bot.message_handler(commands=['start'])
def start(message): # обработка команды start
    message_id = message.id
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (message.chat.id,))
    result = c.fetchone()
    if result is None:
        registration = now_time()
        c.execute("INSERT INTO users (user_id, time_registration, id_message) VALUES (?, ?, ?)",
                  (message.chat.id, registration, message_id+1))
        conn.commit()
        print('Зарегистрирован новый пользователь', message.chat.id)
    else:
        c.execute(f"UPDATE users SET id_message = {(message_id)} WHERE user_id = {message.chat.id}")
        print('Пользователь' ,message.chat.id,'уже существует в базе')
        conn.commit()
        pass
    conn.close()

    open_menu('main', message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(f'{call.data} ({(call.data).count("_")})')

    if (call.data).split('_')[0] == 'admin' and (call.data).split('_')[1] == 'delete-menu':
        delete_menu((call.data).split('_')[2], call)
    elif (call.data).split('_')[0] == 'admin' and (call.data).split('_')[1] == 'delete-command':
        delete_command(call.data, call)

    if (call.data).split('_')[0] == 'return':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        open_menu(name = (call.data).split('_')[1], call = call)
    elif str((call.data)).count('_') <= 1:
        if (call.data).split('_')[0] == 'admin':
            open_menu(name = (call.data).split('_')[1], call = call)
        if (call.data).split('_')[0] == 'user':
            open_menu(name = (call.data).split('_')[1], call = call)


    elif str((call.data)).count('_') <= 2:
        if (call.data).split('_')[0] == 'admin' and (call.data).split('_')[1] == 'edit-menu':
            open_menu((call.data).split('_')[1], call = call)
        elif (call.data).split('_')[0] == 'admin' and ((call.data).split('_')[1].split('-')[0]) == 'rename':
            rename_object = (call.data).split('-')[2].split('_')[0]
            for y, x in object_menu.items():
                if x == rename_object:
                    open_menu('rename-object', call = call)
        elif (call.data).split('_')[0] == 'admin' and (call.data).split('_')[1] == 'open-command':
            open_menu((call.data).split('_')[1], call = call)

    
main_check()
print("Бот запущен...")

try:
    bot.polling()
except Exception as e:
    with open(error_path, 'w+', encoding='utf-8') as f:
        f.write(str(e) + "\n")
        goodbuy