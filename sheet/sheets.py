from idlelib.configdialog import changes

import gspread
from google.oauth2.service_account import Credentials
from config.config import SHEET_NAME, CREDENTIALS_PATH


# Настройка авторизации
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet = client.open(SHEET_NAME)
products_sheet = spreadsheet.worksheet("Products")
cart_sheet = spreadsheet.worksheet("Cart")

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
    """Удалить товары из корзины"""
    cart = get_cart()
    for i, row in enumerate(cart, start=2):
        if row['User_ID'] == user_id and row['Product_ID'] == product_id:
            cart_sheet.delete_cell(i)
            return True
        return False

def update_cart(user_id, product_id, change):
    """Обновление кол-во товара в корзине"""
    cart = get_cart()
    for row in cart:
        if row['User_ID'] == user_id and row['Product_ID'] == product_id:
            new_quantity = max(1, row['Quantity'] + change)
            cart_sheet.update_cell(cart.index(row) + 2, 3, new_quantity)
            return new_quantity
        return None
