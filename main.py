"""
Maher Umar POS - Android Mobile App
Integrated with full inventory, automated category discounts, sales, Udaar book, expenses, and ReportLab PDF invoices.
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

# ReportLab imports for PDF Generation on Android/Desktop
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

APP_TITLE = "Maher Umar Mobile & Communication"
DB_NAME = "maher_umar_pos.db"

# =========================================================
# DISCOUNT & CATEGORY RULES
# =========================================================
ENABLE_SPECIAL_DISCOUNTS = True
DISCOUNT_RULES = {
    "MOBILE": {"min_qty": 3, "discount_pct": 5.0},
    "FAST CHARGER": {"min_qty": 50, "discount_pct": 5.0},
    "CHARGER": {"min_qty": 150, "discount_pct": 5.0},
    "HANDSFREE": {"min_qty": 150, "discount_pct": 5.0},
    "AIRBUS": {"min_qty": 10, "discount_pct": 5.0},
}

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
            text: "[b]MAHER UMAR POS[/b]\nInventory • Sales • Udaar • Expenses"
            markup: True
            font_size: "20sp"
            color: (0.08, 0.20, 0.25, 1)
            size_hint_y: None
            height: dp(68)
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
                text: "Udaar Book"
                on_release: app.root.current = "udaar"
            NavButton:
                text: "Expenses"
                on_release: app.root.current = "expenses"
        Label:
            id: summary
            text: root.summary_text
            color: (0.12, 0.18, 0.20, 1)
            halign: "left"
            valign: "top"
            text_size: self.width, None
            font_size: "15sp"
        Widget:
        NavButton:
            text: "Refresh Dashboard"
            on_release: root.refresh_summary()
        Label:
            text: "Local SQLite + PDF Invoice Mode"
            font_size: "12sp"
            color: (0.35, 0.40, 0.42, 1)
            size_hint_y: None
            height: dp(26)

<ProductsScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(7)
        Label:
            text: "[b]Products & Inventory[/b]"
            markup: True
            size_hint_y: None
            height: dp(40)
            font_size: "18sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: pname
            hint_text: "Product name (e.g. Oppo A38)"
            multiline: False
            size_hint_y: None
            height: dp(42)
        TextInput:
            id: pcategory
            hint_text: "Category (MOBILE, CHARGER, etc.)"
            multiline: False
            size_hint_y: None
            height: dp(42)
        GridLayout:
            cols: 2
            spacing: dp(6)
            size_hint_y: None
            height: dp(84)
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
                hint_text: "Stock qty"
                input_filter: "int"
                multiline: False
            NavButton:
                text: "Add/Update"
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
                font_size: "13sp"
        NavButton:
            text: "Back to Dashboard"
            on_release: app.root.current = "home"

<SaleScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(6)
        Label:
            text: "[b]POS Billing & PDF Invoice[/b]"
            markup: True
            size_hint_y: None
            height: dp(38)
            font_size: "18sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: customer
            hint_text: "Customer Name (Alphabetic)"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: phone
            hint_text: "Customer Phone (11 digits)"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: product_id
            hint_text: "Product ID"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: quantity
            hint_text: "Quantity"
            input_filter: "int"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: paid
            hint_text: "Payment Received (Rs.)"
            input_filter: "float"
            multiline: False
            size_hint_y: None
            height: dp(40)
        NavButton:
            text: "Complete Sale & Generate PDF"
            on_release: root.save_sale()
        Label:
            id: result
            text: root.result_text
            color: (0.12, 0.18, 0.20, 1)
            halign: "left"
            valign: "top"
            text_size: self.width, None
            font_size: "13sp"
        Widget:
        NavButton:
            text: "Back to Dashboard"
            on_release: app.root.current = "home"

<UdaarScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(8)
        Label:
            text: "[b]Udaar Book (Credit Customers)[/b]"
            markup: True
            size_hint_y: None
            height: dp(40)
            font_size: "18sp"
            color: (0.08, 0.20, 0.25, 1)
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
                font_size: "13sp"
        NavButton:
            text: "Back to Dashboard"
            on_release: app.root.current = "home"

<ExpensesScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(6)
        Label:
            text: "[b]Expense Tracker (Kharcha Book)[/b]"
            markup: True
            size_hint_y: None
            height: dp(38)
            font_size: "18sp"
            color: (0.08, 0.20, 0.25, 1)
        TextInput:
            id: title
            hint_text: "Expense Title"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: amount
            hint_text: "Amount (Rs.)"
            input_filter: "float"
            multiline: False
            size_hint_y: None
            height: dp(40)
        TextInput:
            id: category
            hint_text: "Category (Utility/Transport)"
            multiline: False
            size_hint_y: None
            height: dp(40)
        NavButton:
            text: "Save Expense"
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
                font_size: "13sp"
        NavButton:
            text: "Back to Dashboard"
            on_release: app.root.current = "home"
"""

def popup(message):
    Popup(title="Maher Umar POS", content=Label(text=message), size_hint=(0.88, 0.35)).open()

# =========================================================
# STORE / DATABASE MANAGER
# =========================================================
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
            discount REAL DEFAULT 0.0,
            net_amount REAL NOT NULL,
            paid_amount REAL NOT NULL CHECK(paid_amount >= 0),
            balance REAL NOT NULL CHECK(balance >= 0),
            status TEXT NOT NULL,
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
        return self.conn.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE").fetchall()

    def add_product(self, name, category, purchase, sale, stock):
        clean_name = name.strip().upper()
        cat = category.strip().upper() or "GENERAL"
        with self.conn:
            existing = self.conn.execute("SELECT * FROM products WHERE LOWER(name)=LOWER(?)", (clean_name,)).fetchone()
            if existing:
                new_stock = existing["stock"] + stock
                self.conn.execute(
                    "UPDATE products SET stock=?, purchase_price=?, sale_price=?, category=? WHERE id=?",
                    (new_stock, purchase, sale, cat, existing["id"])
                )
            else:
                self.conn.execute(
                    "INSERT INTO products(name,category,purchase_price,sale_price,stock,created_at) VALUES(?,?,?,?,?,?)",
                    (clean_name, cat, purchase, sale, stock, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )

    def make_sale(self, customer, phone, product_id, quantity, paid):
        with self.conn:
            p = self.conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not p:
                raise ValueError("Product ID not found.")
            if quantity <= 0 or quantity > p["stock"]:
                raise ValueError("Invalid quantity or insufficient stock.")
            
            subtotal = round(p["sale_price"] * quantity, 2)
            
            # Calculate category discount if applicable
            discount = 0.0
            if ENABLE_SPECIAL_DISCOUNTS and p["category"] in DISCOUNT_RULES:
                rule = DISCOUNT_RULES[p["category"]]
                if quantity >= rule["min_qty"]:
                    discount = round(subtotal * rule["discount_pct"] / 100, 2)
            
            net_amount = round(subtotal - discount, 2)
            if paid < 0 or paid > net_amount:
                raise ValueError("Payment must be between Rs. 0 and the net payable amount.")
            
            balance = round(net_amount - paid, 2)
            status = "PAID IN FULL" if balance == 0 else "PAYMENT DUE"
            
            cur = self.conn.execute(
                "INSERT INTO sales(customer_name,customer_phone,total_amount,discount,net_amount,paid_amount,balance,status,sale_date) VALUES(?,?,?,?,?,?,?,?,?)",
                (customer.strip(), phone.strip(), subtotal, discount, net_amount, paid, balance, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            sale_id = cur.lastrowid
            
            self.conn.execute(
                "INSERT INTO sale_items(sale_id,product_id,quantity,price,purchase_price) VALUES(?,?,?,?,?)",
                (sale_id, product_id, quantity, p["sale_price"], p["purchase_price"])
            )
            self.conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
        
        return sale_id, subtotal, discount, net_amount, balance, status, [{
            "product_id": product_id,
            "name": p["name"],
            "category": p["category"],
            "quantity": quantity,
            "price": p["sale_price"]
        }]

    def add_expense(self, title, amount, category):
        with self.conn:
            self.conn.execute(
                "INSERT INTO expenses(title,amount,category,expense_date) VALUES(?,?,?,?)",
                (title.strip(), amount, category.strip() or "General", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

    def totals(self):
        return {
            "products": self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "units": self.conn.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0],
            "sales": self.conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
            "revenue": self.conn.execute("SELECT COALESCE(SUM(net_amount),0) FROM sales").fetchone()[0],
            "due": self.conn.execute("SELECT COALESCE(SUM(balance),0) FROM sales").fetchone()[0],
            "expenses": self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0],
        }

# =========================================================
# PDF INVOICE GENERATOR FUNCTION FOR ANDROID
# =========================================================
def generate_pdf_invoice(customer, customer_phone, invoice_no, cart, subtotal, discount, final_payable, payment, balance, status):
    output_folder = "/storage/emulated/0/Download/Customer_Invoices"
    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception:
        output_folder = os.path.join(App.get_running_app().user_data_dir, "Customer_Invoices")
        os.makedirs(output_folder, exist_ok=True)

    safe_name = "".join(ch for ch in customer if ch.isalnum() or ch in (" ", "-", "_")).strip().replace(" ", "_") or "Customer"
    pdf_path = os.path.join(output_folder, f"{safe_name}_{invoice_no}.pdf")

    try:
        PAGE_W, PAGE_H = A4
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        pdf.setTitle(f"Invoice {invoice_no}")

        pdf.setFillColor(colors.HexColor("#202020"))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, PAGE_H - 50, APP_TITLE)

        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, PAGE_H - 70, f"Invoice No: {invoice_no}")
        pdf.drawString(50, PAGE_H - 85, f"Date: {datetime.now().strftime('%d %B %Y, %I:%M %p')}")
        pdf.drawString(50, PAGE_H - 100, f"Customer: {customer} ({customer_phone})")

        # Table Header
        y = PAGE_H - 140
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Item Description")
        pdf.drawString(300, y, "Qty")
        pdf.drawString(370, y, "Price")
        pdf.drawString(460, y, "Total")
        pdf.line(50, y - 5, 550, y - 5)

        y -= 25
        pdf.setFont("Helvetica", 10)
        for item in cart:
            item_total = item["quantity"] * item["price"]
            pdf.drawString(50, y, item["name"][:35])
            pdf.drawString(300, y, str(item["quantity"]))
            pdf.drawString(370, y, f"Rs. {item['price']:,.2f}")
            pdf.drawString(460, y, f"Rs. {item_total:,.2f}")
            y -= 20

        y -= 10
        pdf.line(50, y, 550, y)
        y -= 25

        pdf.drawString(350, y, f"Subtotal: Rs. {subtotal:,.2f}")
        y -= 18
        pdf.drawString(350, y, f"Discount: -Rs. {discount:,.2f}")
        y -= 18
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(350, y, f"Final Payable: Rs. {final_payable:,.2f}")
        y -= 18
        pdf.setFont("Helvetica", 10)
        pdf.drawString(350, y, f"Paid: Rs. {payment:,.2f}")
        y -= 18
        pdf.drawString(350, y, f"Balance Due: Rs. {balance:,.2f}")
        y -= 20
        pdf.drawString(350, y, f"Status: {status}")

        pdf.showPage()
        pdf.save()
        return pdf_path
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

# =========================================================
# UI SCREENS
# =========================================================
class MainScreen(Screen):
    summary_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh_summary()
    def refresh_summary(self):
        t = App.get_running_app().store.totals()
        self.summary_text = (
            f"Products Catalog: {t['products']}\n"
            f"Total Units in Stock: {t['units']}\n"
            f"Sales Count: {t['sales']}\n"
            f"Gross Revenue: Rs. {t['revenue']:,.2f}\n"
            f"Outstanding Udaar: Rs. {t['due']:,.2f}\n"
            f"Total Expenses: Rs. {t['expenses']:,.2f}"
        )

class ProductsScreen(Screen):
    listing_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        rows = App.get_running_app().store.products()
        self.listing_text = "\n".join(
            f"ID: {r['id']} | {r['name']} ({r['category']})\n"
            f"Stock: {r['stock']} | Cost: Rs.{r['purchase_price']:.2f} | Sale: Rs.{r['sale_price']:.2f}\n"
            for r in rows
        ) or "No products found."
    def add_product(self):
        try:
            name = self.ids.pname.text.strip()
            category = self.ids.pcategory.text.strip()
            purchase = float(self.ids.purchase.text)
            sale = float(self.ids.saleprice.text)
            stock = int(self.ids.stock.text)
            if not name or purchase < 0 or sale < 0 or stock <= 0:
                raise ValueError("Check inputs. Stock must be > 0.")
            App.get_running_app().store.add_product(name, category, purchase, sale, stock)
            for k in ("pname", "pcategory", "purchase", "saleprice", "stock"):
                self.ids[k].text = ""
            self.refresh()
            popup("Product saved successfully.")
        except Exception as e:
            popup(str(e) or "Invalid product details.")

class SaleScreen(Screen):
    result_text = StringProperty("")
    def save_sale(self):
        try:
            customer = self.ids.customer.text.strip()
            phone = self.ids.phone.text.strip()
            if not customer or not all(c.isalpha() or c == ' ' for c in customer):
                raise ValueError("Customer name must be alphabetic.")
            if len(phone) != 11 or not phone.isdigit():
                raise ValueError("Phone number must be exactly 11 digits.")
            
            prod_id = int(self.ids.product_id.text)
            qty = int(self.ids.quantity.text)
            paid = float(self.ids.paid.text)

            sale_id, subtotal, discount, net, balance, status, cart = App.get_running_app().store.make_sale(
                customer, phone, prod_id, qty, paid
            )
            inv_no = f"{datetime.now().strftime('%y%m%d')}-{sale_id:05d}"
            pdf = generate_pdf_invoice(customer, phone, inv_no, cart, subtotal, discount, net, paid, balance, status)

            self.result_text = f"Sale #{sale_id} saved!\nNet: Rs.{net:,.2f}\nDue: Rs.{balance:,.2f}\nPDF: {pdf or 'Not saved'}"
            for k in ("customer", "phone", "product_id", "quantity", "paid"):
                self.ids[k].text = ""
        except Exception as e:
            popup(str(e) or "Sale error check fields.")

class UdaarScreen(Screen):
    listing_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        rows = App.get_running_app().store.conn.execute("SELECT * FROM sales WHERE balance > 0 ORDER BY sale_date DESC").fetchall()
        self.listing_text = "\n".join(
            f"Sale #{r['id']} • {r['customer_name']} ({r['customer_phone']})\nDue: Rs.{r['balance']:,.2f} | Date: {r['sale_date']}"
            for r in rows
        ) or "Alhamdulillah, no outstanding udaar!"

class ExpensesScreen(Screen):
    listing_text = StringProperty("")
    def on_pre_enter(self, *args): self.refresh()
    def refresh(self):
        rows = App.get_running_app().store.conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 50").fetchall()
        self.listing_text = "\n".join(
            f"{r['expense_date']} • {r['title']} — Rs.{r['amount']:,.2f} ({r['category']})"
            for r in rows
        ) or "No expenses recorded."
    def add_expense(self):
        try:
            title = self.ids.title.text.strip()
            amount = float(self.ids.amount.text)
            cat = self.ids.category.text.strip()
            if not title or amount <= 0:
                raise ValueError("Enter valid title and amount.")
            App.get_running_app().store.add_expense(title, amount, cat)
            for k in ("title", "amount", "category"):
                self.ids[k].text = ""
            self.refresh()
            popup("Expense recorded.")
        except Exception as e:
            popup(str(e) or "Check expense details.")

class MaherUmarPOSApp(App):
    def build(self):
        self.title = APP_TITLE
        self.store = Store(DB_NAME)
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="home"))
        sm.add_widget(ProductsScreen(name="products"))
        sm.add_widget(SaleScreen(name="sale"))
        sm.add_widget(UdaarScreen(name="udaar"))
        sm.add_widget(ExpensesScreen(name="expenses"))
        return sm
    def on_stop(self):
        if hasattr(self, "store"):
            self.store.conn.close()

if __name__ == "__main__":
    MaherUmarPOSApp().run()
