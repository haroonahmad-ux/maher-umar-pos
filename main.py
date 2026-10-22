"""
Maher-Umar-POS Android starter app.
Kivy mobile UI + local SQLite persistence.
Supabase cloud sync is intentionally not enabled until auth/session handling is wired in.
"""
import os
import sqlite3
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

KV = r"""
<NavButton@Button>:
    size_hint_y: None
    height: dp(46)
    background_normal: ""
    background_color: (0.08, 0.36, 0.48, 1)
    color: (1, 1, 1, 1)
    font_size: "15sp"

<MainScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: (0.95, 0.97, 0.98, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[b]MAHER UMAR POS[/b]\\nInventory • Sales • Expenses"
            markup: True
            font_size: "22sp"
            color: (0.08, 0.20, 0.25, 1)
            size_hint_y: None
            height: dp(76)
        GridLayout:
            cols: 2
            spacing: dp(8)
            size_hint_y: None
            height: dp(156)
            NavButton:
                text: "Products"
                on_release: app.root.current = "products"
            NavButton:
                text: "New Sale"
                on_release: app.root.current = "sale"
            NavButton:
                text: "Expenses"
                on_release: app.root.current = "expenses"
            NavButton:
                text: "Reports"
                on_release: app.root.current = "reports"
        Label:
            id: summary
            text: root.summary_text
            color: (0.12, 0.18, 0.20, 1)
            halign: "left"
            valign: "top"
            text_size: self.width, None
            font_size: "16sp"
        Widget:
        NavButton:
            text: "Refresh dashboard"
            on_release: root.refresh_summary()
        Label:
            text: "Local SQLite mode • Cloud sync not connected yet"
            font_size: "12sp"
            color: (0.35, 0.40, 0.42, 1)
            size_hint_y: None
            height: dp(28)

<ProductsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "[b]Products & Inventory[/b]"
            markup: True
            size_hint_y: None
            height: dp(42)
            font_size: "20sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: pname
            hint_text: "Product name"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: pcategory
            hint_text: "Category (e.g. CHARGER, MOBILE)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        GridLayout:
            cols: 2
            spacing: dp(6)
            size_hint_y: None
            height: dp(88)
            TextInput:
                id: purchase
                hint_text: "Purchase price (Rs.)"
                input_filter: "float"
                multiline: False
            TextInput:
                id: saleprice
                hint_text: "Sale price (Rs.)"
                input_filter: "float"
                multiline: False
            TextInput:
                id: stock
                hint_text: "Opening stock"
                input_filter: "int"
                multiline: False
            NavButton:
                text: "Add product"
                on_release: root.add_product()
        ScrollView:
            do_scroll_x: False
            Label:
                id: listing
                text: root.listing_text
                size_hint_y: None
                height: self.texture_size[1] + dp(20)
                text_size: self.width, None
                halign: "left"
                valign: "top"
                color: (0.12, 0.18, 0.20, 1)
                font_size: "14sp"
        NavButton:
            text: "Back to dashboard"
            on_release: app.root.current = "home"

<SaleScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "[b]Record Sale[/b]"
            markup: True
            size_hint_y: None
            height: dp(42)
            font_size: "20sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: customer
            hint_text: "Customer name"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: phone
            hint_text: "Customer phone (optional)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: product_id
            hint_text: "Product ID (see Products screen)"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: quantity
            hint_text: "Quantity"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: paid
            hint_text: "Amount received (Rs.)"
            input_filter: "float"
            multiline: False
            size_hint_y: None
            height: dp(44)
        NavButton:
            text: "Save sale & update stock"
            on_release: root.save_sale()
        Label:
            id: result
            text: root.result_text
            color: (0.12, 0.18, 0.20, 1)
            halign: "left"
            valign: "top"
            text_size: self.width, None
        Widget:
        NavButton:
            text: "Back to dashboard"
            on_release: app.root.current = "home"

<ExpensesScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "[b]Expenses[/b]"
            markup: True
            size_hint_y: None
            height: dp(42)
            font_size: "20sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: title
            hint_text: "Expense title"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: amount
            hint_text: "Amount (Rs.)"
            input_filter: "float"
            multiline: False
            size_hint_y: None
            height: dp(44)
        TextInput:
            id: category
            hint_text: "Category (e.g. Utility, Transport)"
            multiline: False
            size_hint_y: None
            height: dp(44)
        NavButton:
            text: "Save expense"
            on_release: root.add_expense()
        ScrollView:
            do_scroll_x: False
            Label:
                id: listing
                text: root.listing_text
                size_hint_y: None
                height: self.texture_size[1] + dp(20)
                text_size: self.width, None
                halign: "left"
                valign: "top"
                color: (0.12, 0.18, 0.20, 1)
        NavButton:
            text: "Back to dashboard"
            on_release: app.root.current = "home"

<ReportsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(8)
        Label:
            text: "[b]Reports[/b]"
            markup: True
            size_hint_y: None
            height: dp(42)
            font_size: "20sp"
            color: (0.08, 0.20, 0.25, 1)
        Label:
            text: root.report_text
            halign: "left"
            valign: "top"
            text_size: self.width, None
            color: (0.12, 0.18, 0.20, 1)
        NavButton:
            text: "Refresh reports"
            on_release: root.refresh()
        Widget:
        NavButton:
            text: "Back to dashboard"
            on_release: app.root.current = "home"
"""

def popup(message):
    Popup(title="Maher Umar POS", content=Label(text=message), size_hint=(0.88, 0.35)).open()

class Store:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
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
            p = self.conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not p:
                raise ValueError("Product ID not found.")
            if quantity <= 0 or quantity > p["stock"]:
                raise ValueError("Quantity must be positive and cannot exceed available stock.")
            total = round(p["sale_price"] * quantity, 2)
            if paid < 0 or paid > total:
                raise ValueError("Payment must be between Rs. 0 and the total.")
            balance = round(total - paid, 2)
            cur = self.conn.execute(
                "INSERT INTO sales(customer_name,customer_phone,total_amount,paid_amount,balance,sale_date) VALUES(?,?,?,?,?,?)",
                (customer.strip() or "Walk-in", phone.strip(), total, paid, balance, datetime.now().isoformat(timespec="seconds"))
            )
            sale_id = cur.lastrowid
            self.conn.execute(
                "INSERT INTO sale_items(sale_id,product_id,quantity,price,purchase_price) VALUES(?,?,?,?,?)",
                (sale_id, product_id, quantity, p["sale_price"], p["purchase_price"])
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
    def on_pre_enter(self, *args): self.refresh_summary()
    def refresh_summary(self):
        t = App.get_running_app().store.totals()
        self.summary_text = (
            f"Products: {t['products']}\\nUnits in stock: {t['units']}\\n"
            f"Sales recorded: {t['sales']}\\nSales total: Rs. {t['revenue']:,.2f}\\n"
            f"Outstanding: Rs. {t['due']:,.2f}\\nExpenses: Rs. {t['expenses']:,.2f}"
        )

class ProductsScreen(Screen):
    listing_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        rows = App.get_running_app().store.products()
        self.listing_text = "\\n".join(
            f"ID {r['id']} • {r['name']} ({r['category']})\\n"
            f"Stock: {r['stock']} | Cost: Rs. {r['purchase_price']:.2f} | Sale: Rs. {r['sale_price']:.2f}\\n"
            for r in rows
        ) or "No products added yet."
    def add_product(self):
        try:
            name = self.ids.pname.text.strip()
            category = self.ids.pcategory.text.strip() or "GENERAL"
            purchase, sale = float(self.ids.purchase.text), float(self.ids.saleprice.text)
            stock = int(self.ids.stock.text)
            if not name or purchase < 0 or sale < 0 or stock < 0: raise ValueError("Enter valid product details.")
            App.get_running_app().store.add_product(name, category, purchase, sale, stock)
            for key in ("pname", "pcategory", "purchase", "saleprice", "stock"): self.ids[key].text = ""
            self.refresh()
            popup("Product saved.")
        except (ValueError, KeyError) as e: popup(str(e) or "Check all product fields.")

class SaleScreen(Screen):
    result_text = StringProperty("")
    def save_sale(self):
        try:
            sale_id, total, due = App.get_running_app().store.make_sale(
                self.ids.customer.text, self.ids.phone.text,
                int(self.ids.product_id.text), int(self.ids.quantity.text),
                float(self.ids.paid.text)
            )
            self.result_text = f"Sale #{sale_id} saved.\\nTotal: Rs. {total:,.2f}\\nDue: Rs. {due:,.2f}\\nStock updated."
            for key in ("customer", "phone", "product_id", "quantity", "paid"): self.ids[key].text = ""
        except (ValueError, KeyError) as e:
            popup(str(e) or "Please check sale details.")

class ExpensesScreen(Screen):
    listing_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        rows = App.get_running_app().store.conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 100").fetchall()
        self.listing_text = "\\n".join(f"{r['expense_date']} • {r['title']} — Rs. {r['amount']:,.2f} ({r['category']})" for r in rows) or "No expenses recorded."
    def add_expense(self):
        try:
            title, amount = self.ids.title.text.strip(), float(self.ids.amount.text)
            category = self.ids.category.text.strip() or "General"
            if not title or amount <= 0: raise ValueError("Enter a title and amount greater than zero.")
            App.get_running_app().store.add_expense(title, amount, category)
            for key in ("title", "amount", "category"): self.ids[key].text = ""
            self.refresh()
            popup("Expense saved.")
        except (ValueError, KeyError) as e: popup(str(e) or "Check expense fields.")

class ReportsScreen(Screen):
    report_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        t = App.get_running_app().store.totals()
        self.report_text = (
            f"Sales count: {t['sales']}\\nGross sales: Rs. {t['revenue']:,.2f}\\n"
            f"Outstanding balance: Rs. {t['due']:,.2f}\\n"
            f"Recorded expenses: Rs. {t['expenses']:,.2f}\\n"
            f"Net after expenses (before cost of goods): Rs. {t['revenue']-t['expenses']:,.2f}"
        )

class MaherUmarPOSApp(App):
    def build(self):
        self.title = APP_TITLE
        db_path = os.path.join(self.user_data_dir, DB_NAME)
        self.store = Store(db_path)
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="home"))
        sm.add_widget(ProductsScreen(name="products"))
        sm.add_widget(SaleScreen(name="sale"))
        sm.add_widget(ExpensesScreen(name="expenses"))
        sm.add_widget(ReportsScreen(name="reports"))
        return sm
    def on_stop(self):
        if hasattr(self, "store"): self.store.conn.close()

if __name__ == "__main__":
    MaherUmarPOSApp().run()
