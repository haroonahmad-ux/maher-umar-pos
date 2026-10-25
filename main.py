"""Maher Umar POS - mobile-first Kivy POS with local SQLite storage."""
import os
import sqlite3
import sys
import traceback
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

APP_TITLE = "Maher Umar POS"
DB_NAME = "maher_umar_pos.db"

KV = r'''
#:import dp kivy.metrics.dp
<PrimaryButton@Button>:
    size_hint_y: None
    height: dp(50)
    background_normal: ''
    background_down: ''
    background_color: (0.055, 0.34, 0.42, 1)
    color: (1, 1, 1, 1)
    font_size: '15sp'
    bold: True
<SecondaryButton@Button>:
    size_hint_y: None
    height: dp(46)
    background_normal: ''
    background_down: ''
    background_color: (0.88, 0.94, 0.95, 1)
    color: (0.07, 0.26, 0.31, 1)
    font_size: '14sp'
<Field@TextInput>:
    size_hint_y: None
    height: dp(50)
    multiline: False
    padding: [dp(12), dp(14), dp(12), dp(10)]
    font_size: '15sp'
    foreground_color: (0.10, 0.17, 0.19, 1)
    hint_text_color: (0.42, 0.49, 0.51, 1)
    cursor_color: (0.05, 0.40, 0.48, 1)
    background_normal: ''
    background_active: ''
    background_color: (0.93, 0.96, 0.97, 1)
<PageHeading@Label>:
    size_hint_y: None
    height: dp(42)
    font_size: '21sp'
    bold: True
    color: (0.07, 0.19, 0.23, 1)
    halign: 'left'
    valign: 'middle'
    text_size: self.size
<HintText@Label>:
    size_hint_y: None
    height: dp(25)
    font_size: '13sp'
    color: (0.39, 0.47, 0.50, 1)
    halign: 'left'
    valign: 'middle'
    text_size: self.size

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(14)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: (0.955, 0.972, 0.978, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                Label:
                    text: '[b]MAHER UMAR POS[/b]\n[size=13sp]Your store, in control[/size]'
                    markup: True
                    size_hint_y: None
                    height: dp(78)
                    font_size: '23sp'
                    color: (0.07, 0.19, 0.23, 1)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(86)
                    padding: dp(14)
                    spacing: dp(4)
                    canvas.before:
                        Color:
                            rgba: (0.055, 0.34, 0.42, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(15)]
                    Label:
                        text: 'BUSINESS MANAGEMENT'
                        font_size: '11sp'
                        bold: True
                        color: (0.76, 0.90, 0.92, 1)
                        halign: 'left'
                        text_size: self.size
                    Label:
                        text: 'Inventory  •  Sales  •  Expenses'
                        font_size: '17sp'
                        bold: True
                        color: (1, 1, 1, 1)
                        halign: 'left'
                        text_size: self.size
                GridLayout:
                    cols: 2
                    spacing: dp(9)
                    size_hint_y: None
                    height: dp(116)
                    PrimaryButton:
                        text: 'Products & Stock'
                        on_release: app.root.current = 'products'
                    PrimaryButton:
                        text: 'New Sale'
                        on_release: app.root.current = 'sale'
                    SecondaryButton:
                        text: 'Expenses'
                        on_release: app.root.current = 'expenses'
                    SecondaryButton:
                        text: 'Reports'
                        on_release: app.root.current = 'reports'
                Label:
                    text: '[b]BUSINESS SNAPSHOT[/b]'
                    markup: True
                    size_hint_y: None
                    height: dp(26)
                    font_size: '14sp'
                    color: (0.20, 0.31, 0.35, 1)
                    halign: 'left'
                    text_size: self.size
                BoxLayout:
                    size_hint_y: None
                    height: dp(176)
                    padding: dp(14)
                    canvas.before:
                        Color:
                            rgba: (1, 1, 1, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(13)]
                    Label:
                        text: root.summary_text
                        color: (0.13, 0.21, 0.24, 1)
                        halign: 'left'
                        valign: 'top'
                        text_size: self.width, None
                        font_size: '15sp'
                PrimaryButton:
                    text: 'Refresh dashboard'
                    on_release: root.refresh_summary()
                Label:
                    text: 'LOCAL DATABASE  •  Cloud sync not connected'
                    font_size: '11sp'
                    color: (0.42, 0.49, 0.51, 1)
                    size_hint_y: None
                    height: dp(22)

<ProductsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(13)
        spacing: dp(9)
        canvas.before:
            Color:
                rgba: (0.955, 0.972, 0.978, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        PageHeading:
            text: 'Products & Inventory'
        HintText:
            text: 'Add products and manage available stock.'
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(9)
                padding: [0, dp(3), 0, dp(8)]
                Field:
                    id: pname
                    hint_text: 'Product name'
                Field:
                    id: pcategory
                    hint_text: 'Category (e.g. CHARGER, MOBILE)'
                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: dp(108)
                    Field:
                        id: purchase
                        hint_text: 'Purchase price (Rs.)'
                        input_filter: 'float'
                    Field:
                        id: saleprice
                        hint_text: 'Sale price (Rs.)'
                        input_filter: 'float'
                    Field:
                        id: stock
                        hint_text: 'Opening stock'
                        input_filter: 'int'
                    PrimaryButton:
                        text: 'Add product'
                        on_release: root.add_product()
                Label:
                    text: '[b]SAVED PRODUCTS[/b]'
                    markup: True
                    size_hint_y: None
                    height: dp(28)
                    font_size: '14sp'
                    color: (0.12, 0.25, 0.29, 1)
                    halign: 'left'
                    text_size: self.size
                BoxLayout:
                    size_hint_y: None
                    height: max(dp(90), listing.texture_size[1] + dp(26))
                    padding: dp(12)
                    canvas.before:
                        Color:
                            rgba: (1, 1, 1, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(12)]
                    Label:
                        id: listing
                        text: root.listing_text
                        size_hint_y: None
                        height: self.texture_size[1] + dp(8)
                        text_size: self.width, None
                        halign: 'left'
                        valign: 'top'
                        color: (0.14, 0.22, 0.25, 1)
                        font_size: '14sp'
        SecondaryButton:
            text: 'Back to dashboard'
            on_release: app.root.current = 'home'

<SaleScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(13)
        spacing: dp(9)
        canvas.before:
            Color:
                rgba: (0.955, 0.972, 0.978, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        PageHeading:
            text: 'Record a Sale'
        HintText:
            text: 'Record the customer purchase and payment.'
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(9)
                Field:
                    id: customer
                    hint_text: 'Customer name (optional)'
                Field:
                    id: phone
                    hint_text: 'Customer phone (optional)'
                Field:
                    id: product_id
                    hint_text: 'Product ID'
                    input_filter: 'int'
                GridLayout:
                    cols: 2
                    spacing: dp(8)
                    size_hint_y: None
                    height: dp(108)
                    Field:
                        id: quantity
                        hint_text: 'Quantity'
                        input_filter: 'int'
                    Field:
                        id: paid
                        hint_text: 'Amount received (Rs.)'
                        input_filter: 'float'
                PrimaryButton:
                    text: 'Save sale & update stock'
                    on_release: root.save_sale()
                Label:
                    text: root.result_text
                    size_hint_y: None
                    height: max(dp(30), self.texture_size[1] + dp(8))
                    color: (0.055, 0.34, 0.42, 1)
                    halign: 'left'
                    valign: 'top'
                    text_size: self.width, None
                    font_size: '15sp'
        Widget:
        SecondaryButton:
            text: 'Back to dashboard'
            on_release: app.root.current = 'home'

<ExpensesScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(13)
        spacing: dp(9)
        canvas.before:
            Color:
                rgba: (0.955, 0.972, 0.978, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        PageHeading:
            text: 'Expenses'
        HintText:
            text: 'Track the operating costs of your store.'
        Field:
            id: title
            hint_text: 'Expense title'
        Field:
            id: amount
            hint_text: 'Amount (Rs.)'
            input_filter: 'float'
        Field:
            id: category
            hint_text: 'Category (e.g. Utility, Transport)'
        PrimaryButton:
            text: 'Save expense'
            on_release: root.add_expense()
        ScrollView:
            do_scroll_x: False
            Label:
                text: root.listing_text
                size_hint_y: None
                height: self.texture_size[1] + dp(24)
                text_size: self.width, None
                halign: 'left'
                valign: 'top'
                color: (0.14, 0.22, 0.25, 1)
                font_size: '14sp'
        Widget:
        SecondaryButton:
            text: 'Back to dashboard'
            on_release: app.root.current = 'home'

<ReportsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(13)
        spacing: dp(9)
        canvas.before:
            Color:
                rgba: (0.955, 0.972, 0.978, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        PageHeading:
            text: 'Business Reports'
        HintText:
            text: 'A clear overview of recorded business activity.'
        BoxLayout:
            padding: dp(13)
            canvas.before:
                Color:
                    rgba: (1, 1, 1, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(13)]
            Label:
                text: root.report_text
                halign: 'left'
                valign: 'top'
                text_size: self.width, None
                color: (0.14, 0.22, 0.25, 1)
                font_size: '15sp'
        PrimaryButton:
            text: 'Refresh reports'
            on_release: root.refresh()
        SecondaryButton:
            text: 'Back to dashboard'
            on_release: app.root.current = 'home'
'''


def popup(message, title=APP_TITLE):
    body = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    label = Label(text=str(message), color=(0.12, 0.18, 0.20, 1), halign="left", valign="middle")
    label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
    body.add_widget(label)
    close = __import__("kivy.uix.button", fromlist=["Button"]).Button(
        text="OK", size_hint_y=None, height=dp(44), background_normal="",
        background_color=(0.055, 0.34, 0.42, 1), color=(1, 1, 1, 1)
    )
    body.add_widget(close)
    dialog = Popup(title=title, content=body, size_hint=(0.88, None), height=dp(210), auto_dismiss=False)
    close.bind(on_release=dialog.dismiss)
    dialog.open()


class Store:
    def __init__(self, path):
        db_path = path if os.path.isabs(path) else os.path.join(App.get_running_app().user_data_dir, path)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'GENERAL',
            purchase_price REAL NOT NULL CHECK(purchase_price >= 0),
            sale_price REAL NOT NULL CHECK(sale_price >= 0),
            stock INTEGER NOT NULL CHECK(stock >= 0),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            paid_amount REAL NOT NULL CHECK(paid_amount >= 0),
            balance REAL NOT NULL CHECK(balance >= 0),
            sale_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sale_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL REFERENCES sales(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            price REAL NOT NULL CHECK(price >= 0),
            purchase_price REAL NOT NULL CHECK(purchase_price >= 0)
        );
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL DEFAULT 'General',
            expense_date TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def products(self):
        return self.conn.execute("SELECT * FROM products ORDER BY name").fetchall()

    def add_product(self, name, category, purchase, sale, stock):
        with self.conn:
            self.conn.execute(
                "INSERT INTO products(name,category,purchase_price,sale_price,stock,created_at) VALUES(?,?,?,?,?,?)",
                (name, category or "GENERAL", purchase, sale, stock, datetime.now().isoformat(timespec="seconds"))
            )

    def make_sale(self, customer, phone, product_id, quantity, paid):
        with self.conn:
            product = self.conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not product:
                raise ValueError("Product ID not found. Check the ID in Products & Inventory.")
            if quantity <= 0 or quantity > product["stock"]:
                raise ValueError("Quantity must be positive and cannot exceed available stock.")
            total = round(product["sale_price"] * quantity, 2)
            if paid < 0 or paid > total:
                raise ValueError("Payment must be between Rs. 0 and the sale total.")
            balance = round(total - paid, 2)
            cur = self.conn.execute(
                "INSERT INTO sales(customer_name,customer_phone,total_amount,paid_amount,balance,sale_date) VALUES(?,?,?,?,?,?)",
                (customer.strip() or "Walk-in", phone.strip(), total, paid, balance, datetime.now().isoformat(timespec="seconds"))
            )
            sale_id = cur.lastrowid
            self.conn.execute(
                "INSERT INTO sale_items(sale_id,product_id,quantity,price,purchase_price) VALUES(?,?,?,?,?)",
                (sale_id, product_id, quantity, product["sale_price"], product["purchase_price"])
            )
            self.conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
        return sale_id, total, balance

    def add_expense(self, title, amount, category):
        with self.conn:
            self.conn.execute(
                "INSERT INTO expenses(title,amount,category,expense_date) VALUES(?,?,?,?)",
                (title.strip(), amount, category.strip() or "General", datetime.now().isoformat(timespec="seconds"))
            )

    def totals(self):
        return {
            "products": self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "units": self.conn.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0],
            "sales": self.conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
            "revenue": self.conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales").fetchone()[0],
            "due": self.conn.execute("SELECT COALESCE(SUM(balance),0) FROM sales").fetchone()[0],
            "expenses": self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0],
        }


class MainScreen(Screen):
    summary_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh_summary()

    def refresh_summary(self):
        t = App.get_running_app().store.totals()
        self.summary_text = (
            f"Products listed       {t['products']}\n"
            f"Units in stock         {t['units']}\n"
            f"Sales recorded        {t['sales']}\n"
            f"Total sales             Rs. {t['revenue']:,.2f}\n"
            f"Outstanding due      Rs. {t['due']:,.2f}\n"
            f"Total expenses       Rs. {t['expenses']:,.2f}"
        )


class ProductsScreen(Screen):
    listing_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        rows = App.get_running_app().store.products()
        self.listing_text = "\n\n".join(
            f"ID {r['id']}  •  {r['name']}\n"
            f"{r['category']}  |  Stock: {r['stock']}\n"
            f"Cost Rs. {r['purchase_price']:,.2f}  •  Sale Rs. {r['sale_price']:,.2f}"
            for r in rows
        ) or "No products added yet.\nYour saved products will appear here."

    def add_product(self):
        try:
            name = self.ids.pname.text.strip()
            category = self.ids.pcategory.text.strip() or "GENERAL"
            if not name:
                raise ValueError("Enter a product name.")
            purchase = float(self.ids.purchase.text)
            sale = float(self.ids.saleprice.text)
            stock = int(self.ids.stock.text)
            if purchase < 0 or sale < 0 or stock < 0:
                raise ValueError("Prices and stock cannot be negative.")
            App.get_running_app().store.add_product(name, category, purchase, sale, stock)
            for key in ("pname", "pcategory", "purchase", "saleprice", "stock"):
                self.ids[key].text = ""
            self.refresh()
            App.get_running_app().root.get_screen("home").refresh_summary()
            popup("Product saved successfully.", "Saved")
        except (ValueError, KeyError) as exc:
            popup(str(exc) or "Please check all product fields.", "Check details")


class SaleScreen(Screen):
    result_text = StringProperty("")

    def save_sale(self):
        try:
            sale_id, total, due = App.get_running_app().store.make_sale(
                self.ids.customer.text, self.ids.phone.text,
                int(self.ids.product_id.text), int(self.ids.quantity.text),
                float(self.ids.paid.text)
            )
            self.result_text = f"Sale #{sale_id} saved\nTotal: Rs. {total:,.2f}\nOutstanding: Rs. {due:,.2f}\nStock updated successfully."
            for key in ("customer", "phone", "product_id", "quantity", "paid"):
                self.ids[key].text = ""
            App.get_running_app().root.get_screen("home").refresh_summary()
            popup(self.result_text, "Sale completed")
        except (ValueError, KeyError) as exc:
            popup(str(exc) or "Please check the sale details.", "Unable to save sale")


class ExpensesScreen(Screen):
    listing_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        rows = App.get_running_app().store.conn.execute(
            "SELECT * FROM expenses ORDER BY id DESC LIMIT 100"
        ).fetchall()
        self.listing_text = "\n\n".join(
            f"{r['title']}  •  Rs. {r['amount']:,.2f}\n{r['category']}  |  {r['expense_date']}"
            for r in rows
        ) or "No expenses recorded yet."

    def add_expense(self):
        try:
            title = self.ids.title.text.strip()
            amount = float(self.ids.amount.text)
            category = self.ids.category.text.strip() or "General"
            if not title or amount <= 0:
                raise ValueError("Enter an expense title and an amount greater than zero.")
            App.get_running_app().store.add_expense(title, amount, category)
            for key in ("title", "amount", "category"):
                self.ids[key].text = ""
            self.refresh()
            App.get_running_app().root.get_screen("home").refresh_summary()
            popup("Expense saved successfully.", "Saved")
        except (ValueError, KeyError) as exc:
            popup(str(exc) or "Please check expense details.", "Check details")


class ReportsScreen(Screen):
    report_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        t = App.get_running_app().store.totals()
        self.report_text = (
            f"Sales count                 {t['sales']}\n\n"
            f"Gross sales                 Rs. {t['revenue']:,.2f}\n\n"
            f"Outstanding balance    Rs. {t['due']:,.2f}\n\n"
            f"Recorded expenses      Rs. {t['expenses']:,.2f}\n\n"
            f"Net before stock cost   Rs. {t['revenue'] - t['expenses']:,.2f}"
        )


class MaherUmarPOSApp(App):
    def build(self):
        self.title = APP_TITLE
        self.store = Store(os.path.join(self.user_data_dir, DB_NAME))
        Builder.load_string(KV)
        manager = ScreenManager()
        manager.add_widget(MainScreen(name="home"))
        manager.add_widget(ProductsScreen(name="products"))
        manager.add_widget(SaleScreen(name="sale"))
        manager.add_widget(ExpensesScreen(name="expenses"))
        manager.add_widget(ReportsScreen(name="reports"))
        return manager

    def on_stop(self):
        if hasattr(self, "store"):
            self.store.conn.close()


if __name__ == "__main__":
    try:
        MaherUmarPOSApp().run()
    except Exception:
        error_text = traceback.format_exc()
        try:
            app = App.get_running_app()
            log_dir = app.user_data_dir if app and app.user_data_dir else os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(log_dir, "crash_log.txt"), "a", encoding="utf-8") as log:
                log.write(f"\n\n--- CRASH: {datetime.now()} ---\n{error_text}")
        except Exception:
            print("Could not save crash log.")
        print(error_text, file=sys.stderr)
        raise
