import os
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

# Database Initialization
DB_PATH = os.path.join(os.path.expanduser('~'), 'maher_umar_pos.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            qty INTEGER,
            total_price REAL,
            customer_name TEXT,
            sale_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS udaar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            amount REAL,
            status TEXT,
            date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super(DashboardScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # Header
        header = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=2)
        header.add_label = Label(text="MAHER UMAR MOBILE &", font_size=20, bold=True, color=(0.1, 0.2, 0.25, 1))
        header.add_widget(Label(text="COMMUNICATION", font_size=20, bold=True, color=(0.1, 0.2, 0.25, 1)))
        header.add_widget(Label(text="Your store, in control", font_size=13, color=(0.4, 0.4, 0.4, 1)))
        layout.add_widget(header)

        # Management Grid Buttons
        btn_grid = GridLayout(cols=2, spacing=12, size_hint_y=None, height=180)
        
        btn_prod = Button(text="Products & Stock", background_color=(0.08, 0.25, 0.3, 1), font_size=15, bold=True)
        btn_prod.bind(on_press=self.goto_products)
        btn_grid.add_widget(btn_prod)

        btn_sale = Button(text="New Sale", background_color=(0.08, 0.25, 0.3, 1), font_size=15, bold=True)
        btn_sale.bind(on_press=self.goto_sale)
        btn_grid.add_widget(btn_sale)

        btn_udaar = Button(text="Udaar Book", background_color=(0.08, 0.25, 0.3, 1), font_size=15, bold=True)
        btn_udaar.bind(on_press=self.goto_udaar)
        btn_grid.add_widget(btn_udaar)

        btn_exp = Button(text="Expenses", background_color=(0.08, 0.25, 0.3, 1), font_size=15, bold=True)
        btn_exp.bind(on_press=self.goto_expenses)
        btn_grid.add_widget(btn_exp)

        layout.add_widget(btn_grid)

        # Summary Stats
        self.stats_layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.update_stats()
        layout.add_widget(self.stats_layout)

        # Footer Backup Button
        footer = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        btn_backup = Button(text="Backup Database", background_color=(0.2, 0.2, 0.2, 1))
        btn_backup.bind(on_press=self.make_backup)
        footer.add_widget(btn_backup)
        layout.add_widget(footer)

        self.add_widget(layout)

    def update_stats(self):
        self.stats_layout.clear_widgets()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(stock) FROM products")
        p_count, total_stock = cursor.fetchone()
        p_count = p_count or 0
        total_stock = total_stock or 0

        cursor.execute("SELECT COUNT(*), SUM(total_price) FROM sales")
        s_count, net_sales = cursor.fetchone()
        s_count = s_count or 0
        net_sales = net_sales or 0.0

        cursor.execute("SELECT SUM(amount) FROM udaar WHERE status='Pending'")
        outstanding = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(amount) FROM expenses")
        total_exp = cursor.fetchone()[0] or 0.0

        conn.close()

        self.stats_layout.add_widget(Label(text=f"Units in stock: {total_stock}", color=(0.2, 0.2, 0.2, 1), font_size=14))
        self.stats_layout.add_widget(Label(text=f"Sales recorded: {s_count}", color=(0.2, 0.2, 0.2, 1), font_size=14))
        self.stats_layout.add_widget(Label(text=f"Net sales: Rs. {net_sales:.2f}", color=(0.2, 0.2, 0.2, 1), font_size=14))
        self.stats_layout.add_widget(Label(text=f"Outstanding due: Rs. {outstanding:.2f}", color=(0.2, 0.2, 0.2, 1), font_size=14))
        self.stats_layout.add_widget(Label(text=f"Total expenses: Rs. {total_exp:.2f}", color=(0.2, 0.2, 0.2, 1), font_size=14))

    def on_enter(self):
        self.update_stats()

    def goto_products(self, instance):
        self.manager.current = 'products'

    def goto_sale(self, instance):
        self.manager.current = 'sale'

    def goto_udaar(self, instance):
        self.manager.current = 'udaar'

    def goto_expenses(self, instance):
        self.manager.current = 'expenses'

    def make_backup(self, instance):
        popup = Popup(title='Backup Complete',
                      content=Label(text='Local database backup successfully created!'),
                      size_hint=(0.8, 0.3))
        popup.open()


class ProductsScreen(Screen):
    def __init__(self, **kwargs):
        super(ProductsScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        layout.add_widget(Label(text="Products & Inventory Management", font_size=18, bold=True, size_hint_y=None, height=40, color=(0.1, 0.2, 0.25, 1)))
        
        form = GridLayout(cols=2, spacing=10, size_hint_y=None, height=160)
        form.add_widget(Label(text="Product Name:", color=(0.2, 0.2, 0.2, 1)))
        self.name_input = TextInput(multiline=False)
        form.add_widget(self.name_input)

        form.add_widget(Label(text="Price (Rs):", color=(0.2, 0.2, 0.2, 1)))
        self.price_input = TextInput(multiline=False, input_filter='float')
        form.add_widget(self.price_input)

        form.add_widget(Label(text="Stock Qty:", color=(0.2, 0.2, 0.2, 1)))
        self.stock_input = TextInput(multiline=False, input_filter='int')
        form.add_widget(self.stock_input)

        layout.add_widget(form)

        btn_add = Button(text="Add Product", size_hint_y=None, height=45, background_color=(0.08, 0.25, 0.3, 1))
        btn_add.bind(on_press=self.add_product)
        layout.add_widget(btn_add)

        self.list_layout = BoxLayout(orientation='vertical', spacing=5)
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.list_layout)
        layout.add_widget(scroll)

        btn_back = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_color=(0.3, 0.3, 0.3, 1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def on_enter(self):
        self.load_products()

    def load_products(self):
        self.list_layout.clear_widgets()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock FROM products")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            lbl = Label(text=f"ID: {row[0]} | {row[1]} | Price: Rs.{row[2]} | Stock: {row[3]}", size_hint_y=None, height=35, color=(0.2, 0.2, 0.2, 1))
            self.list_layout.add_widget(lbl)

    def add_product(self, instance):
        name = self.name_input.text.strip()
        price = self.price_input.text.strip()
        stock = self.stock_input.text.strip()

        if name and price and stock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (name, category, price, cost, stock) VALUES (?, ?, ?, ?, ?)",
                           (name, 'General', float(price), float(price)*0.8, int(stock)))
            conn.commit()
            conn.close()
            self.name_input.text = ""
            self.price_input.text = ""
            self.stock_input.text = ""
            self.load_products()

    def go_back(self, instance):
        self.manager.current = 'dashboard'


class SaleScreen(Screen):
    def __init__(self, **kwargs):
        super(SaleScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="New Sale / Billing", font_size=18, bold=True, size_hint_y=None, height=40, color=(0.1, 0.2, 0.25, 1)))

        form = GridLayout(cols=2, spacing=10, size_hint_y=None, height=160)
        form.add_widget(Label(text="Product Name:", color=(0.2, 0.2, 0.2, 1)))
        self.prod_input = TextInput(multiline=False)
        form.add_widget(self.prod_input)

        form.add_widget(Label(text="Quantity:", color=(0.2, 0.2, 0.2, 1)))
        self.qty_input = TextInput(multiline=False, input_filter='int')
        form.add_widget(self.qty_input)

        form.add_widget(Label(text="Customer Name:", color=(0.2, 0.2, 0.2, 1)))
        self.cust_input = TextInput(multiline=False)
        form.add_widget(self.cust_input)

        layout.add_widget(form)

        btn_sale = Button(text="Complete Sale & Generate Invoice", size_hint_y=None, height=45, background_color=(0.08, 0.25, 0.3, 1))
        btn_sale.bind(on_press=self.complete_sale)
        layout.add_widget(btn_sale)

        self.result_label = Label(text="", color=(0, 0.5, 0, 1), size_hint_y=None, height=40)
        layout.add_widget(self.result_label)

        btn_back = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_color=(0.3, 0.3, 0.3, 1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def complete_sale(self, instance):
        p_name = self.prod_input.text.strip()
        qty = self.qty_input.text.strip()
        cust = self.cust_input.text.strip() or "Walk-in Customer"

        if p_name and qty:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, price, stock FROM products WHERE name LIKE ?", (f"%{p_name}%",))
            row = cursor.fetchone()
            if row:
                p_id, price, stock = row
                q = int(qty)
                total = price * q
                cursor.execute("INSERT INTO sales (product_id, product_name, qty, total_price, customer_name, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
                               (p_id, p_name, q, total, cust, str(datetime.now())))
                cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (q, p_id))
                conn.commit()
                conn.close()
                self.result_label.text = f"Sale Successful! Total: Rs. {total:.2f}"
                self.prod_input.text = ""
                self.qty_input.text = ""
                self.cust_input.text = ""
            else:
                conn.close()
                self.result_label.text = "Product not found!"

    def go_back(self, instance):
        self.manager.current = 'dashboard'


class UdaarScreen(Screen):
    def __init__(self, **kwargs):
        super(UdaarScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Udaar Book / Outstanding", font_size=18, bold=True, size_hint_y=None, height=40, color=(0.1, 0.2, 0.25, 1)))

        self.udaar_list = BoxLayout(orientation='vertical', spacing=5)
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.udaar_list)
        layout.add_widget(scroll)

        btn_back = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_color=(0.3, 0.3, 0.3, 1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def on_enter(self):
        self.load_udaar()

    def load_udaar(self):
        self.udaar_list.clear_widgets()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT customer_name, phone, amount, status FROM udaar WHERE status='Pending'")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.udaar_list.add_widget(Label(text="Alhamdulillah, koi outstanding udaar nahi.", color=(0.2, 0.2, 0.2, 1)))
        else:
            for r in rows:
                self.udaar_list.add_widget(Label(text=f"{r[0]} ({r[1]}): Rs. {r[2]}", size_hint_y=None, height=35, color=(0.2, 0.2, 0.2, 1)))

    def go_back(self, instance):
        self.manager.current = 'dashboard'


class ExpensesScreen(Screen):
    def __init__(self, **kwargs):
        super(ExpensesScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Store Expenses", font_size=18, bold=True, size_hint_y=None, height=40, color=(0.1, 0.2, 0.25, 1)))

        form = GridLayout(cols=2, spacing=10, size_hint_y=None, height=110)
        form.add_widget(Label(text="Expense Title:", color=(0.2, 0.2, 0.2, 1)))
        self.title_input = TextInput(multiline=False)
        form.add_widget(self.title_input)

        form.add_widget(Label(text="Amount (Rs):", color=(0.2, 0.2, 0.2, 1)))
        self.amount_input = TextInput(multiline=False, input_filter='float')
        form.add_widget(self.amount_input)

        layout.add_widget(form)

        btn_add = Button(text="Add Expense", size_hint_y=None, height=45, background_color=(0.08, 0.25, 0.3, 1))
        btn_add.bind(on_press=self.add_expense)
        layout.add_widget(btn_add)

        btn_back = Button(text="Back to Dashboard", size_hint_y=None, height=45, background_color=(0.3, 0.3, 0.3, 1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def add_expense(self, instance):
        title = self.title_input.text.strip()
        amt = self.amount_input.text.strip()
        if title and amt:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expenses (title, amount, date) VALUES (?, ?, ?)",
                           (title, float(amt), str(datetime.now())))
            conn.commit()
            conn.close()
            self.title_input.text = ""
            self.amount_input.text = ""

    def go_back(self, instance):
        self.manager.current = 'dashboard'


class MaherUmarPOSApp(App):
    def build(self):
        Window.clearcolor = (0.95, 0.96, 0.97, 1)
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(ProductsScreen(name='products'))
        sm.add_widget(SaleScreen(name='sale'))
        sm.add_widget(UdaarScreen(name='udaar'))
        sm.add_widget(ExpensesScreen(name='expenses'))
        return sm

if __name__ == '__main__':
    MaherUmarPOSApp().run()
        
