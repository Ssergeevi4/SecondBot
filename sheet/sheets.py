from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from config.config import SHEET_NAME, CREDENTIALS_PATH

# Настройка авторизации
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = "/root/stazh/sergey/SecondBot/TelegramBot.json"
creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet = client.open(SHEET_NAME)
products_sheet = spreadsheet.worksheet("Products")
cart_sheet = spreadsheet.worksheet("Cart")
orders_sheet = spreadsheet.worksheet("Orders")


REMOVE_T = "TGmag"

def remove_from_cart(user_id, product_id=None):
    """Удаляет товары из корзины пользователя. Если product_id=None, удаляет все товары пользователя."""
    try:
        cart_sheet = client.open(REMOVE_T).worksheet("Cart")
        cart = cart_sheet.get_all_records()
        rows_to_delete = []

        # Находим все строки для удаления
        for i, row in enumerate(cart, start=2):  # Начинаем с 2, так как 1-я строка — заголовки
            if str(row.get('User_ID')) == str(user_id):
                if product_id is None or str(row.get('Product_ID')) == str(product_id):
                    rows_to_delete.append(i)

        if not rows_to_delete:
            print(f"Для пользователя не найдено ни одного товара в корзине {user_id}")
            return

        # Сортируем индексы в обратном порядке, чтобы удаление не сбило индексы
        rows_to_delete.sort(reverse=True)

        # Удаляем строки по одной (gspread не поддерживает удаление диапазона одним запросом, но мы минимизируем логику)
        for row_index in rows_to_delete:
            cart_sheet.delete_rows(row_index)
            print(f"Удаление продукта {product_id if product_id else 'all'} Из корзины пользователя {user_id} с втроке {row_index}")

    except gspread.exceptions.SpreadsheetNotFound as e:
        print(f"Таблица '{REMOVE_T}' не найдена: {e}")
        raise Exception(f"Не удалось найти таблицу '{REMOVE_T}'. Проверьте название таблицы и права доступа.")
    except Exception as e:
        print(f"Ошибка удаления корзины: {e}")
        raise

def add_product(name, description, price, availability, image_url):
    """Добавляет новый товар в лист Products."""
    try:
        sheet = client.open("TGmag").worksheet("Products")
        # Получаем все записи, чтобы определить новый ID
        products = sheet.get_all_records()
        new_id = len(products) + 1  # Простой способ генерации ID
        sheet.append_row([
            str(new_id),  # ID
            name,
            description,
            availability,
            str(price),
            image_url if image_url else "",  # Если поле пустое, записываем пустую строку
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Дата добавления
        ])
        print(f"Product {name} added with ID {new_id}")
    except Exception as e:
        print(f"Error adding product: {e}")
        raise


# def add_product(name, description, price, availability, sizes, image_url):
#     """Добавить новый товар (для администратора)."""
#     products = get_products()
#     new_id = max([int(p.get('ID', 0)) for p in products], default=0) + 1
#     products_sheet.append_row([str(new_id), name, description, availability, str(price), sizes, image_url])
#     return new_id


def create_invite_code(invite_code, role):
    """Создаёт код """
    sheet = client.open("TGmag").worksheet("Invites")
    sheet.append_row([str(invite_code), role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


def get_invite_code(invite_code):
    """Получает информацию о коде приглашения."""
    sheet = client.open("TGmag").worksheet("Invites")
    invite_code = sheet.get_all_records()
    return next((invite for invite in invite_code if str(invite.get('Invite_Code')) == str(invite_code)), None)


def register_user(user_id, role):
    sheet = client.open("TGmag").worksheet("Users")
    users = sheet.get_all_records()
    if any(str(user.get('User_ID')) == str(user_id) for user in users):
        return
    sheet.append_row([str(user_id), role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


def get_user_role(user_id):
    sheet = client.open("TGmag").worksheet("Users")
    users = sheet.get_all_records()
    user = next((user for user in users if user.get('User_ID') == str(user_id)), None)
    return user.get('Role') if user else None


def is_admin(user_id):
    """Проверяет, является ли пользователь администратором."""
    try:
        sheet = spreadsheet.worksheet("Users")
        admins = sheet.get_all_records()
        for admin in admins:
            if str(admin.get('User_ID')) == str(user_id) and admin.get('Role') == 'admin':
                return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке администратора: {e}")
        return False


def is_seller(user_id):
    """Проверяет, является ли пользователь продавцом."""
    try:
        sheet = spreadsheet.worksheet("Users")
        admins = sheet.get_all_records()
        for admin in admins:
            if str(admin.get('User_ID')) == str(user_id) and admin.get('Role') == 'seller':
                return True
        return False
    except Exception as e:
        print(f"Ошибка при проверке продавца: {e}")
        return False


def get_user_role(user_id):
    """Возвращает роль пользователя: admin, seller или buyer."""
    try:
        sheet = spreadsheet.worksheet("Users")
        admins = sheet.get_all_records()
        for admin in admins:
            if str(admin.get('User_ID')) == str(user_id):
                return admin.get('Role', 'buyer')
        return 'buyer'  # По умолчанию — покупатель
    except Exception as e:
        print(f"Ошибка при получении роли: {e}")
        return 'buyer'


def get_products():
    """Получить все товары."""
    return products_sheet.get_all_records()


def get_cart():
    """Получить все записи корзины."""
    return cart_sheet.get_all_records()


def add_to_cart(user_id, product_id, quantity=1):
    """Добавить товар в корзину."""
    cart = get_cart()
    for row in cart:
        if row['User_ID'] == user_id and row['Product_ID'] == product_id:
            new_quantity = row['Quantity'] + quantity
            cart_sheet.update_cell(cart.index(row) + 2, 3, + quantity)
            return new_quantity
    cart_sheet.append_row([user_id, product_id, quantity])
    return quantity


def remove_from_cart(user_id, product_id):
    """Удаляет товар из корзины пользователя."""
    try:
        cart_sheet = client.open("TGmag").worksheet("Cart")
        cart = cart_sheet.get_all_records()

        # Находим индекс строки для удаления
        for i, row in enumerate(cart, start=2):  # Начинаем с 2, так как 1-я строка — заголовки
            if str(row.get('User_ID')) == str(user_id) and str(row.get('Product_ID')) == str(product_id):
                cart_sheet.delete_rows(i)  # Удаляем строку
                print(f"Removed product {product_id} from cart for user {user_id}")
                return
        print(f"Product {product_id} not found in cart for user {user_id}")
    except Exception as e:
        print(f"Error removing from cart: {e}")
        raise


def update_cart(user_id, product_id, change):
    """Обновление кол-во товара в корзине"""
    cart = get_cart()
    for row in cart:
        if row['User_ID'] == user_id and row['Product_ID'] == product_id:
            new_quantity = max(1, row['Quantity'] + change)
            cart_sheet.update_cell(cart.index(row) + 2, 3, new_quantity)
            return new_quantity
        return None


def get_orders():
    """Получить все заказы."""
    return orders_sheet.get_all_records()


def create_order(user_id, product_id, quantity, order_number):
    sheet = client.open("TGmag").worksheet("Orders")
    sheet.append_row(
        [str(user_id), str(product_id), str(quantity), str(order_number), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


def update_order_status(order_id, new_status):
    """Обновить статус заказа (для продавца)."""
    orders = get_orders()
    for i, order in enumerate(orders, start=2):
        if str(order.get('Order_ID')) == str(order_id):
            orders_sheet.update_cell(i, 5, new_status)
            return True
    return False
