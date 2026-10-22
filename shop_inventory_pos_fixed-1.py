import os
import shutil
import sqlite3
from datetime import datetime
 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
 
 
# =========================================================
# CONFIGURATION
# =========================================================
 
SHOP_NAME = "MAHER UMAR MOBILE & COMMUNICATION"
 
ENABLE_SPECIAL_DISCOUNTS = True
 
DISCOUNT_RULES = {
    "MOBILE": {"min_qty": 3, "discount_pct": 5.0},
    "FAST CHARGER": {"min_qty": 50, "discount_pct": 5.0},
    "CHARGER": {"min_qty": 150, "discount_pct": 5.0},
    "HANDSFREE": {"min_qty": 150, "discount_pct": 5.0},
    "AIRBUS": {"min_qty": 10, "discount_pct": 5.0},
}
 
PHONE_KEYWORDS = [
    "vivo", "oppo", "samsung", "iphone", "tecno",
    "infinix", "itel", "phone", "y04", "y20",
    "a38", "a36", "reno"
]
 
EARBUD_KEYWORDS = [
    "airbus", "airbud", "earbud", "earbuds",
    "airpods", "wireless buds", "wireless earbuds"
]
 
HANDSFREE_KEYWORDS = [
    "handsfree", "headset", "neckband"
]
 
OUTPUT_FOLDER = os.path.join(
    os.path.expanduser("~"),
    "Customer_Invoices"
)
 
ANDROID_OUTPUT_FOLDER = (
    "/storage/emulated/0/Download/Customer_Invoices"
)
 
 
# =========================================================
# HELPERS
# =========================================================
 
def normalize_category(category):
    """Convert category into a consistent matching format."""
    return (category or "GENERAL").strip().upper()
 
 
def detect_category(name, category=""):
    """Detect a category when the user leaves it blank."""
    if category and category.strip():
        return normalize_category(category)
 
    name_lower = name.lower()
 
    if "fast charger" in name_lower:
        return "FAST CHARGER"
 
    if any(word in name_lower for word in EARBUD_KEYWORDS):
        return "AIRBUS"
 
    if any(word in name_lower for word in HANDSFREE_KEYWORDS):
        return "HANDSFREE"
 
    if "charger" in name_lower:
        return "CHARGER"
 
    if any(word in name_lower for word in PHONE_KEYWORDS):
        return "MOBILE"
 
    return "GENERAL"
 
 
def money(value):
    return f"Rs. {float(value):,.2f}"
 
 
def read_number(prompt, number_type=float, minimum=None):
    """Read a number and reject invalid or out-of-range input."""
    while True:
        try:
            value = number_type(input(prompt).strip())
 
            if minimum is not None and value < minimum:
                print(f"[ERROR] Value {minimum} se kam nahi ho sakti.")
                continue
 
            return value
 
        except ValueError:
            print("[ERROR] Valid numeric value enter karein.")
 
 
def calculate_category_discount(cart):
    """
    Calculate discounts separately for each eligible category.
 
    A category's threshold is based on the total quantity of
    all items in that category within the current cart.
    """
    if not ENABLE_SPECIAL_DISCOUNTS:
        return 0.0
 
    quantities = {}
    amounts = {}
 
    for item in cart:
        category = normalize_category(item.get("category", ""))
 
        quantities[category] = (
            quantities.get(category, 0) + item["quantity"]
        )
 
        amounts[category] = (
            amounts.get(category, 0)
            + item["quantity"] * item["price"]
        )
 
    total_discount = 0.0
 
    for category, rule in DISCOUNT_RULES.items():
        qty = quantities.get(category, 0)
 
        if qty >= rule["min_qty"]:
            total_discount += (
                amounts.get(category, 0)
                * rule["discount_pct"] / 100
            )
 
    return round(total_discount, 2)
 
 
# =========================================================
# DATABASE MANAGER
# =========================================================
 
class DatabaseManager:
 
    def __init__(self, db_name="shop_database.db"):
        current_dir = os.path.dirname(
            os.path.abspath(__file__)
        )
 
        self.db_path = os.path.join(current_dir, db_name)
 
        self.conn = sqlite3.connect(
            self.db_path,
            timeout=30
        )
 
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
 
        self.cursor = self.conn.cursor()
 
        self.create_tables()
 
    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                purchase_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                stock INTEGER NOT NULL,
                created_at TEXT
            )
        """)
 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                customer_phone TEXT,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0.0,
                net_amount REAL NOT NULL,
                paid_amount REAL NOT NULL,
                balance REAL NOT NULL,
                status TEXT NOT NULL,
                sale_date TEXT NOT NULL
            )
        """)
 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                purchase_price REAL,
                FOREIGN KEY (sale_id)
                    REFERENCES sales(id),
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
            )
        """)
 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                expense_date TEXT NOT NULL
            )
        """)
 
        # Safe migrations for existing databases.
        self._add_column_if_missing(
            "sales", "customer_phone", "TEXT"
        )
 
        self._add_column_if_missing(
            "sales", "paid_amount", "REAL DEFAULT 0.0"
        )
 
        self._add_column_if_missing(
            "sales", "balance", "REAL DEFAULT 0.0"
        )
 
        self._add_column_if_missing(
            "sales", "status", "TEXT DEFAULT 'PAID'"
        )
 
        self._add_column_if_missing(
            "sale_items", "purchase_price", "REAL"
        )
 
        self.conn.commit()
 
    def _add_column_if_missing(
        self, table, column, column_definition
    ):
        existing_columns = {
            row["name"]
            for row in self.conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }
 
        if column not in existing_columns:
            self.conn.execute(
                f"ALTER TABLE {table} ADD COLUMN "
                f"{column} {column_definition}"
            )
 
    def backup_database(self):
        backup_folder = os.path.join(
            os.path.dirname(self.db_path),
            "Backups"
        )
 
        try:
            os.makedirs(backup_folder, exist_ok=True)
 
            date_str = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
 
            backup_path = os.path.join(
                backup_folder,
                f"shop_backup_{date_str}.db"
            )
 
            # SQLite-safe backup, including committed DB data.
            destination = sqlite3.connect(backup_path)
 
            try:
                self.conn.backup(destination)
            finally:
                destination.close()
 
            print(
                f"\n[SUCCESS] Backup created:\n{backup_path}"
            )
 
            return backup_path
 
        except Exception as error:
            print(f"\n[ERROR] Backup failed: {error}")
            return None
 
    def close(self):
        if self.conn:
            self.conn.close()
 
 
# =========================================================
# PRODUCT MODEL
# =========================================================
 
class ProductModel:
 
    def __init__(self, db):
        self.db = db
 
    def get_all_products(self):
        rows = self.db.conn.execute("""
            SELECT * FROM products ORDER BY name COLLATE NOCASE
        """).fetchall()
 
        return [dict(row) for row in rows]
 
    def get_product_by_id(self, product_id):
        row = self.db.conn.execute("""
            SELECT * FROM products WHERE id = ?
        """, (product_id,)).fetchone()
 
        return dict(row) if row else None
 
    def add_product(
        self, name, category, p_price, s_price, stock
    ):
        name = name.strip()
 
        if not name:
            raise ValueError("Product name cannot be empty.")
 
        if p_price < 0 or s_price < 0:
            raise ValueError("Prices cannot be negative.")
 
        if stock <= 0:
            raise ValueError("Stock quantity must be positive.")
 
        category = detect_category(name, category)
        clean_name = name.upper()
 
        with self.db.conn:
            existing = self.db.conn.execute("""
                SELECT * FROM products
                WHERE LOWER(name) = LOWER(?)
            """, (clean_name,)).fetchone()
 
            if existing:
                product_id = existing["id"]
                new_stock = existing["stock"] + stock
 
                self.db.conn.execute("""
                    UPDATE products
                    SET stock = ?,
                        purchase_price = ?,
                        sale_price = ?,
                        category = ?
                    WHERE id = ?
                """, (
                    new_stock,
                    p_price,
                    s_price,
                    category,
                    product_id
                ))
 
                print(
                    f"[SUCCESS] {clean_name} updated. "
                    f"New stock: {new_stock}"
                )
 
                return product_id
 
            date_str = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
 
            cursor = self.db.conn.execute("""
                INSERT INTO products (
                    name, category, purchase_price,
                    sale_price, stock, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                clean_name,
                category,
                p_price,
                s_price,
                stock,
                date_str
            ))
 
            print(
                f"[SUCCESS] {clean_name} added "
                f"to inventory. Category: {category}"
            )
 
            return cursor.lastrowid
 
 
# =========================================================
# SALES MODEL
# =========================================================
 
class SalesModel:
 
    def __init__(self, db):
        self.db = db
 
    def create_sale(
        self, customer, customer_phone,
        total_amount, discount, paid_amount, items
    ):
        if not items:
            raise ValueError("Cannot record an empty sale.")
 
        if total_amount < 0 or discount < 0:
            raise ValueError("Invalid sale amount.")
 
        if discount > total_amount:
            raise ValueError("Discount exceeds subtotal.")
 
        net_amount = round(total_amount - discount, 2)
 
        if paid_amount < 0:
            raise ValueError("Payment cannot be negative.")
 
        if paid_amount > net_amount:
            raise ValueError(
                "Payment cannot exceed the final payable amount."
            )
 
        balance = round(net_amount - paid_amount, 2)
 
        status = (
            "PAID IN FULL"
            if balance == 0
            else "PAYMENT DUE"
        )
 
        sale_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
 
        # The sale, sale items and stock deductions must succeed
        # together. A failure rolls the transaction back.
        with self.db.conn:
            for item in items:
                row = self.db.conn.execute("""
                    SELECT stock, purchase_price
                    FROM products
                    WHERE id = ?
                """, (item["product_id"],)).fetchone()
 
                if row is None:
                    raise ValueError(
                        f"Product ID {item['product_id']} not found."
                    )
 
                if item["quantity"] <= 0:
                    raise ValueError("Quantity must be positive.")
 
                if item["quantity"] > row["stock"]:
                    raise ValueError(
                        f"Insufficient stock for product "
                        f"ID {item['product_id']}."
                    )
 
                # Store the purchase cost at sale time for
                # more reliable future profit reporting.
                item["purchase_price"] = row["purchase_price"]
 
            cursor = self.db.conn.execute("""
                INSERT INTO sales (
                    customer_name, customer_phone,
                    total_amount, discount, net_amount,
                    paid_amount, balance, status, sale_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer,
                customer_phone,
                total_amount,
                discount,
                net_amount,
                paid_amount,
                balance,
                status,
                sale_date
            ))
 
            sale_id = cursor.lastrowid
 
            for item in items:
                self.db.conn.execute("""
                    INSERT INTO sale_items (
                        sale_id, product_id, quantity,
                        price, purchase_price
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sale_id,
                    item["product_id"],
                    item["quantity"],
                    item["price"],
                    item["purchase_price"]
                ))
 
                update = self.db.conn.execute("""
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ? AND stock >= ?
                """, (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"]
                ))
 
                if update.rowcount != 1:
                    raise ValueError(
                        "Stock changed during checkout. "
                        "Please try again."
                    )
 
        return sale_id
 
    def get_sales_history(self):
        sales = self.db.conn.execute("""
            SELECT * FROM sales ORDER BY sale_date DESC, id DESC
        """).fetchall()
 
        history = []
 
        for sale_row in sales:
            sale = dict(sale_row)
 
            rows = self.db.conn.execute("""
                SELECT
                    si.*,
                    p.name,
                    COALESCE(
                        si.purchase_price,
                        p.purchase_price
                    ) AS cost_price
                FROM sale_items si
                LEFT JOIN products p
                    ON si.product_id = p.id
                WHERE si.sale_id = ?
            """, (sale["id"],)).fetchall()
 
            items = [dict(row) for row in rows]
 
            total_cost = sum(
                item["quantity"] * (item["cost_price"] or 0)
                for item in items
            )
 
            profit = sale["net_amount"] - total_cost
 
            history.append({
                "sale": sale,
                "items": items,
                "profit": profit
            })
 
        return history
 
    def get_udaar_customers(self):
        rows = self.db.conn.execute("""
            SELECT * FROM sales
            WHERE balance > 0
            ORDER BY sale_date DESC
        """).fetchall()
 
        return [dict(row) for row in rows]
 
 
# =========================================================
# EXPENSE MODEL
# =========================================================
 
class ExpenseModel:
 
    def __init__(self, db):
        self.db = db
 
    def add_expense(self, title, amount, category):
        title = title.strip()
 
        if not title:
            raise ValueError("Expense title cannot be empty.")
 
        if amount <= 0:
            raise ValueError("Expense must be greater than zero.")
 
        if not category or not category.strip():
            category = "General"
 
        date_str = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
 
        with self.db.conn:
            self.db.conn.execute("""
                INSERT INTO expenses (
                    title, amount, category, expense_date
                )
                VALUES (?, ?, ?, ?)
            """, (
                title,
                amount,
                category.strip(),
                date_str
            ))
 
    def get_all_expenses(self):
        rows = self.db.conn.execute("""
            SELECT * FROM expenses
            ORDER BY expense_date DESC, id DESC
        """).fetchall()
 
        return [dict(row) for row in rows]
 
 
# =========================================================
# PDF INVOICE GENERATOR
# =========================================================
 
def generate_pdf_invoice(
    customer, customer_phone, invoice_no,
    cart, subtotal, discount, final_payable,
    payment, balance, status
):
    output_folder = ANDROID_OUTPUT_FOLDER
 
    # Fall back to a writable home-directory location.
    try:
        os.makedirs(output_folder, exist_ok=True)
        test_path = os.path.join(output_folder, ".write_test")
 
        with open(test_path, "w", encoding="utf-8") as file:
            file.write("ok")
 
        os.remove(test_path)
 
    except OSError:
        output_folder = OUTPUT_FOLDER
        os.makedirs(output_folder, exist_ok=True)
 
    assets_folder = os.path.join(output_folder, "assets")
    os.makedirs(assets_folder, exist_ok=True)
 
    template_names = [
        "invoice_blank_template.png",
        "invoice_blank_template (1).png",
        "invoice_blank_template.jpg",
        "invoice_blank_template.jpeg",
    ]
 
    search_folders = [
        "/storage/emulated/0/Download",
        output_folder,
        assets_folder,
        os.path.dirname(os.path.abspath(__file__))
    ]
 
    template_path = None
 
    for folder in search_folders:
        if not os.path.isdir(folder):
            continue
 
        for filename in template_names:
            candidate = os.path.join(folder, filename)
 
            if os.path.isfile(candidate):
                template_path = candidate
                break
 
        if template_path:
            break
 
    if not template_path:
        print(
            "[WARNING] Invoice template not found. "
            "Sale can still be recorded."
        )
        return None
 
    safe_name = "".join(
        ch for ch in customer
        if ch.isalnum() or ch in (" ", "-", "_")
    ).strip().replace(" ", "_") or "Customer"
 
    pdf_path = os.path.join(
        output_folder,
        f"{safe_name}_{invoice_no}.pdf"
    )
 
    PAGE_W, PAGE_H = A4
    IMG_W, IMG_H = 1118, 1536
 
    def X(px):
        return px * PAGE_W / IMG_W
 
    def Y(py):
        return PAGE_H - (py * PAGE_H / IMG_H)
 
    def draw_text(
    pdf, x, y, text,
    font="Helvetica",
    size=12, color=None
):
        pdf.setFillColor(color or colors.HexColor("#202020"))
        pdf.setFont(font, size)
        pdf.drawString(X(x), Y(y), str(text))
 
    def draw_right(
        pdf, x, y, text, font="Helvetica",
        size=12, color=None
    ):
        pdf.setFillColor(color or colors.HexColor("#202020"))
        pdf.setFont(font, size)
        pdf.drawRightString(X(x), Y(y), str(text))
 
    def draw_center(
        pdf, x, y, text, font="Helvetica",
        size=12, color=None
    ):
        pdf.setFillColor(color or colors.HexColor("#202020"))
        pdf.setFont(font, size)
        pdf.drawCentredString(X(x), Y(y), str(text))
 
    try:
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        pdf.setTitle(f"Invoice {invoice_no} - {customer}")
        pdf.setAuthor(SHOP_NAME)
 
        pdf.drawImage(
            ImageReader(template_path),
            0, 0,
            width=PAGE_W,
            height=PAGE_H,
            preserveAspectRatio=False,
            mask="auto"
        )
 
        dark = colors.HexColor("#242424")
        red = colors.HexColor("#C9232A")
        green = colors.HexColor("#168044")
        rule = colors.HexColor("#B9A6A3")
 
        now = datetime.now()
 
        date_text = now.strftime("%d %B %Y")
        time_text = now.strftime("%I:%M %p")
 
 
 
 
                
        customer_y = 255
        invoice_no_y = 295
        invoice_date_y = 335


        draw_text(
            pdf, 285, customer_y,
            f"{customer[:25]} ({customer_phone})",
            "Helvetica-Bold", 11, dark
        )


        draw_text(
            pdf, 285, invoice_no_y,
            invoice_no, "Helvetica", 11, dark
        )


        draw_text(
            pdf, 285, invoice_date_y,
            f"{date_text}  {time_text}",
            "Helvetica", 11, dark
        )
 
        table_left = 68
        table_right = 1050
        table_top = 451
        table_bottom = 820
 
        col_serial = 190
        col_description = 525
        col_price = 730
        col_qty = 870
 
        preferred_phones = {
            "oppo a38", "oppo a76", "oppo a3x",
            "oppo a60", "vivo y20", "vivo y21", "vivo y29"
        }
 
        sorted_cart = sorted(
            cart,
            key=lambda item: (
                0 if item["name"].lower() in preferred_phones
                else 1,
                item["name"].lower()
            )
        )
 
        row_count = max(6, len(sorted_cart))
        row_height = (
            table_bottom - table_top
        ) / row_count
 
        pdf.setStrokeColor(rule)
        pdf.setLineWidth(0.45)
 
        for row in range(row_count + 1):
            y = table_top + row * row_height
 
            pdf.line(
                X(table_left), Y(y),
                X(table_right), Y(y)
            )
 
        for x in (
            col_serial, col_description, col_price, col_qty
        ):
            pdf.line(
                X(x), Y(table_top),
                X(x), Y(table_bottom)
            )
 
        font_size = max(
            7, min(11, row_height * 0.28)
        )
 
        for index, product in enumerate(sorted_cart, start=1):
            top = table_top + (index - 1) * row_height
            baseline = top + row_height * 0.63
 
            draw_center(
                pdf,
                (table_left + col_serial) / 2,
                baseline,
                index, "Helvetica", font_size, dark
            )
 
            draw_text(
                pdf,
                col_serial + 29,
                baseline,
                product["name"].title()[:28],
                "Helvetica-Bold", font_size, dark
            )
 
            draw_center(
                pdf,
                (col_description + col_price) / 2,
                baseline,
                f'{product["price"]:,.2f}',
                "Helvetica", font_size, dark
            )
 
            draw_center(
                pdf,
                (col_price + col_qty) / 2,
                baseline,
                product["quantity"],
                "Helvetica", font_size, dark
            )
 
            amount = product["quantity"] * product["price"]
 
            draw_center(
                pdf,
                (col_qty + table_right) / 2,
                baseline,
                f"{amount:,.2f}",
                "Helvetica", font_size, dark
            )
 
        summary_rows = [
            ("Subtotal", f"Rs. {subtotal:,.2f}", 852, "Helvetica", dark),
            ("Discount", f"-Rs. {discount:,.2f}", 899, "Helvetica", dark),
            ("FINAL PAYABLE", f"Rs. {final_payable:,.2f}", 946, "Helvetica-Bold", red),
            ("Payment Received", f"Rs. {payment:,.2f}", 993, "Helvetica", dark),
            ("REMAINING BALANCE", f"Rs. {balance:,.2f}", 1040, "Helvetica-Bold", dark),
        ]
 
        for label, value, y, font, color in summary_rows:
            draw_right(pdf, 850, y, label, font, 11, color)
            draw_right(pdf, 1050, y, value, font, 11, color)
 
        for y in (872, 919, 966, 1013, 1060):
            pdf.setStrokeColor(rule)
            pdf.setLineWidth(0.5)
            pdf.line(X(575), Y(y), X(1050), Y(y))
 
        draw_right(
            pdf, 1050, 1097,
            f"PAYMENT STATUS: {status}",
            "Helvetica-Bold", 10.5,
            red if balance > 0 else green
        )
 
        pdf.showPage()
        pdf.save()
 
        print(f"[SUCCESS] Invoice saved: {pdf_path}")
        return pdf_path
 
    except Exception as error:
        print(f"[ERROR] PDF generation failed: {error}")
 
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except OSError:
            pass
 
        return None
 
 
# =========================================================
# DISPLAY HELPERS
# =========================================================
 


def show_inventory(product_model):
    print("\n" + "=" * 44)
    print("          INVENTORY STOCK REPORT")
    print("=" * 44)


    products = product_model.get_all_products()


    if not products:
        print("\n  Your inventory is currently empty.")
        print("=" * 44)
        return


    total_products = len(products)
    total_units = sum(p["stock"] for p in products)
    low_stock_count = sum(
        1 for p in products if p["stock"] <= 5
    )


    print(f"\n  Total Products : {total_products}")
    print(f"  Total Units    : {total_units}")
    print(f"  Low Stock Items: {low_stock_count}")
    print("-" * 44)


    category_names = {
        "1": "Mobile",
        "2": "Accessories",
        "3": "Airbuds",
        "4": "Other Category",
        "MOBILE": "Mobile",
        "ACCESSORIES": "Accessories",
        "AIRBUDS": "Airbuds",
        "OTHER": "Other Category",
        "GENERAL": "General",
        "AUDIO": "Audio",
    }


    for index, p in enumerate(products, start=1):
        name = str(p["name"]).strip().upper()
        raw_category = str(p.get("category") or "GENERAL")
        category = category_names.get(
            raw_category.strip().upper(),
            raw_category.strip().title()
        )


        stock = p["stock"]
        price = p["sale_price"]


        if stock <= 0:
            status = "[OUT OF STOCK]"
        elif stock <= 5:
            status = "[LOW STOCK]"
        else:
            status = "[IN STOCK]"


        print(f"\n  PRODUCT {index:02d}  |  ID: {p['id']}")
        print(f"  {name}")
        print(f"  Category : {category}")
        print(f"  Sale Price: Rs. {price:,.2f}")
        print(f"  Stock Qty : {stock} units")
        print(f"  Status    : {status}")
        print("  " + "-" * 34)


    print("\n" + "=" * 44)
    print("          END OF INVENTORY REPORT")
    print("=" * 44)


        
        
         
 


def add_products_mode(product_model):
    print("\n" + "=" * 44)
    print("          ADD / UPDATE PRODUCTS")
    print("=" * 44)
    print("\nWelcome to Inventory Mode!")
    print("Type '00' to exit inventory mode.")


    category_options = {
        "1": "MOBILE",
        "2": "ACCESSORIES",
        "3": "AIRBUDS",
        "4": "OTHER"
    }


    # Category shortcuts sirf ek baar show honge.
    print("\n" + "-" * 44)
    print("       PRODUCT CATEGORY SHORTCUTS")
    print("-" * 44)
    print("  [1] Mobile Phones")
    print("  [2] Accessories")
    print("  [3] Airbuds")
    print("  [4] Other Category")
    print("-" * 44)
    print("Select the category number for each product.")


    while True:
        name = input("\nProduct Name: ").strip()


        if name.lower() in ("00", "done", "exit"):
            print("\n[INFO] Inventory Mode closed.")
            break


        if not name:
            print("[ERROR] Product name cannot be empty!")
            continue


        # Category menu dobara print nahi hoga.
        while True:
            category_choice = input(
                "Product Category (1-4): "
            ).strip()


            if category_choice in category_options:
                category = category_options[category_choice]
                break


            print(
                "[ERROR] Invalid category! "
                "Enter 1, 2, 3, or 4."
            )


        print(f"[INFO] Selected Category: {category}")


        try:
            p_price = float(
                input("Purchase Price (Rs.): ").strip()
            )


            s_price = float(
                input("Sale Price (Rs.): ").strip()
            )


            stock = int(
                input("Stock Quantity to Add: ").strip()
            )


            if p_price < 0 or s_price < 0:
                print("[ERROR] Prices cannot be negative!")
                continue


            if stock <= 0:
                print("[ERROR] Stock must be greater than zero!")
                continue


            product_model.add_product(
                name, category, p_price, s_price, stock
            )


        except ValueError:
            print("[ERROR] Invalid number! Please try again.")


        except sqlite3.Error as error:
            print(f"[DATABASE ERROR] {error}")


            
         
         
         
# =========================================================
# POS BILLING
# =========================================================
 


def search_pos_product(product_model):
    while True:
        query = input(
            "\nSearch Product Name (00 to finish): "
        ).strip()


        if query == "00":
            return None


        if not query:
            print("[ERROR] Product name enter karein.")
            continue


        products = product_model.get_all_products()


        matches = [
            p for p in products
            if query.casefold() in p["name"].casefold()
        ]


        if not matches:
            print(
                f"[NOT FOUND] '{query}' se milta "
                "koi product nahi mila."
            )
            continue


        exact_matches = [
            p for p in matches
            if p["name"].strip().casefold()
            == query.casefold()
        ]


        if len(exact_matches) == 1:
            product = exact_matches[0]
            print(f"\n[EXACT MATCH] {product['name']}")
            print(f"Price: Rs. {product['sale_price']:,.2f}")
            print(f"Stock: {product['stock']}")
            return product


        print("\n--- MATCHING PRODUCTS ---")


        for index, product in enumerate(matches, start=1):
            print(
                f"{index}. {product['name']} | "
                f"Rs. {product['sale_price']:,.2f} | "
                f"Stock: {product['stock']}"
            )


        print("00. Search Again")


        while True:
            choice = input("Select product number: ").strip()


            if choice == "00":
                break


            if choice.isdigit():
                index = int(choice)


                if 1 <= index <= len(matches):
                    return matches[index - 1]


            print("[ERROR] List se valid number select karein.")


 
 
 
 
 
def make_sale(product_model, sales_model):
    print("\n--- POS BILLING & INVOICE COUNTER ---")
 
            # Customer Name Validation
    while True:
        customer = input("Customer Name: ").strip()


        if (
            customer
            and all(
                ch.isalpha() or ch == " "
                for ch in customer
            )
            and any(ch.isalpha() for ch in customer)
        ):
            break


        print(
            "ERROR: Customer should be in Alphabetic only."
        )


        
        
        
    # Customer Phone Validation
    while True:
        customer_phone = input(
            "Customer Phone (11 digits): "
        ).strip()


        if (
            customer_phone.isascii()
            and customer_phone.isdigit()
            and len(customer_phone) == 11
        ):
            break


        print("ERROR: Phone number exactly 11 digits ka hona chahiye.")
 
    cart = []
 
    print("\nSPECIAL DISCOUNT OFFERS")
 
    if ENABLE_SPECIAL_DISCOUNTS:
        for category, rule in DISCOUNT_RULES.items():
            print(
                f"{category}: Buy {rule['min_qty']} or more "
                f"-> {rule['discount_pct']}% OFF"
            )


                      
    
    while True:
        product = search_pos_product(product_model)


        if product is None:
            if not cart:
                print("[INFO] Empty cart. Sale cancelled.")
                return
            break


        if product["stock"] <= 0:
            print("[ERROR] Product out of stock!")
            continue


        existing = next(
            (
                item for item in cart
                if item["product_id"] == product["id"]
            ),
            None
        )


        already_in_cart = (
            existing["quantity"] if existing else 0
        )


        available = product["stock"] - already_in_cart


        if available <= 0:
            print("[ERROR] Available stock already in cart.")
            continue


        while True:
            try:
                qty = int(input(
                    f"Quantity for {product['name']} "
                    f"(Available: {available}): "
                ).strip())


                if qty <= 0:
                    print("[ERROR] Quantity must be greater than zero.")
                elif qty > available:
                    print("[ERROR] Requested quantity exceeds stock.")
                else:
                    break


            except ValueError:
                print("[ERROR] Please enter a whole number.")


        if existing:
            existing["quantity"] += qty
        else:
            cart.append({
                "product_id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "quantity": qty,
                "price": product["sale_price"]
            })


        print(
            f"[SUCCESS] {product['name']} x {qty} "
            "added to cart."
        ) 
 
    subtotal = round(
        sum(
            item["quantity"] * item["price"]
            for item in cart
        ),
        2
    )
 
    default_discount = calculate_category_discount(cart)
 
    print(f"\nSubtotal: {money(subtotal)}")
    print(f"Discount: {money(default_discount)}")
 
  
 
 
        
       
    discount = default_discount


    # Keep the discount within the valid range.
    if discount < 0 or discount > subtotal:
        discount = 0.0


    final_payable = round(subtotal - discount, 2)


    print("\n" + "=" * 42)
    print("             BILL SUMMARY")
    print("=" * 42)
    print(f"Subtotal          : {money(subtotal)}")
    print(f"Automatic Discount: {money(discount)}")
    print("-" * 42)
    print(f"FINAL PAYABLE     : {money(final_payable)}")
    print("=" * 42)


    while True:
        paid_amount = read_number(
            "Customer ne kitna pay kiya (Rs.): ",
            float,
            0
        )
        paid_amount = round(paid_amount, 2)


        if paid_amount < 0:
            print("[ERROR] Payment negative nahi ho sakti.")
            continue


        if paid_amount > final_payable:
            print(
                "[ERROR] Payment final payable se zyada hai. "
                "Exact amount ya kam amount enter karein."
            )
            continue


        break


    balance = round(final_payable - paid_amount, 2)
 
    status = (
        "PAID IN FULL" if balance == 0 else "PAYMENT DUE"
    )
 
    try:
        sale_id = sales_model.create_sale(
            customer,
            customer_phone,
            subtotal,
            discount,
            paid_amount,
            cart
        )
 
        invoice_no = (
            f"{datetime.now().strftime('%y%m%d')}-"
            f"{sale_id:05d}"
        )
 
        pdf_path = generate_pdf_invoice(
            customer,
            customer_phone,
            invoice_no,
            cart,
            subtotal,
            discount,
            final_payable,
            paid_amount,
            balance,
            status
        )
 
        print("\n========================================")
        print("            SALE RECORDED")
        print("========================================")
        print(f"Sale ID: {sale_id}")
        print(f"Invoice No: {invoice_no}")
        print(f"Subtotal: {money(subtotal)}")
        print(f"Discount: {money(discount)}")
        print(f"Final Payable: {money(final_payable)}")
        print(f"Payment Received: {money(paid_amount)}")
        print(f"Remaining Balance: {money(balance)}")
        print(f"Status: {status}")
 
        if pdf_path:
            print(f"Invoice PDF: {pdf_path}")
        else:
            print(
                "[WARNING] Sale saved, but PDF was not generated."
            )
 
    except (ValueError, sqlite3.Error) as error:
        print(f"[ERROR] Sale could not be recorded: {error}")
 
 
# =========================================================
# SALES HISTORY & PROFIT
# =========================================================
 
def show_sales_history(sales_model):
    print("\n---------------- SALES HISTORY & PROFIT ----------------")
 
    history = sales_model.get_sales_history()
 
    if not history:
        print("Koi sale record nahi hai.")
        return
 
    total_profit = 0.0
 
    for record in history:
        sale = record["sale"]
 
        print(
            f"ID: {sale['id']} | "
            f"Date: {sale['sale_date']} | "
            f"Customer: {sale['customer']} | "
            f"Net: {money(sale['net_amount'])} | "
            f"Due: {money(sale['balance'])} | "
            f"Gross Profit: {money(record['profit'])}"
        )
 
        total_profit += record["profit"]
 
    print("-" * 60)
    print(f"Total Gross Profit: {money(total_profit)}")
    print("Note: Shop expenses are not deducted from this figure.")


   # =========================================================
# UDAAR BOOK
# =========================================================
 
def show_udaar(sales_model):
    print("\n---------------- UDAAR BOOK ----------------")
 
    customers = sales_model.get_udaar_customers()
 
    if not customers:
        print("Alhamdulillah, koi outstanding udaar nahi hai!")
        return
 
    total_due = 0.0
 
    for customer in customers:
        print(
            f"Sale ID: {customer['id']} | "
            f"Customer: {customer['customer_name']} | "
            f"Phone: {customer['customer_phone']} | "
            f"Due: {money(customer['balance'])}"
        )
 
        total_due += customer["balance"]
 
    print("-" * 55)
    print(f"Total Outstanding Balance: {money(total_due)}")
 
 
# =========================================================
# EXPENSE TRACKER
# =========================================================
 
def expense_menu(expense_model):
    while True:
        print("\n--- EXPENSE TRACKER (KHARCHA BOOK) ---")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Back to Main Menu")
 
        choice = input("Choice (1-3): ").strip()
 
        if choice == "1":
            title = input("Expense Title: ").strip()
 
            if not title:
                print("[ERROR] Title cannot be empty.")
                continue
 
            amount = read_number(
                "Amount (Rs.): ", float, 0.01
            )
 
            category = input(
                "Category (Utility/Food/Transport): "
            ).strip() or "General"
 
            try:
                expense_model.add_expense(
                    title, amount, category
                )
 
                print(
                    f"[SUCCESS] Expense added: "
                    f"{title} - {money(amount)}"
                )
 
            except (ValueError, sqlite3.Error) as error:
                print(f"[ERROR] Expense not saved: {error}")
 
        elif choice == "2":
            expenses = expense_model.get_all_expenses()
 
            if not expenses:
                print("Koi expense record mojood nahi hai.")
                continue
 
            total_expenses = 0.0
 
            print("\n--- ALL EXPENSES ---")
 
            for expense in expenses:
                print(
                    f"Date: {expense['expense_date']} | "
                    f"Title: {expense['title']} | "
                    f"Category: {expense['category']} | "
                    f"Amount: {money(expense['amount'])}"
                )
 
                total_expenses += expense["amount"]
 
            print("-" * 55)
            print(f"Total Shop Expenses: {money(total_expenses)}")
 
        elif choice == "3":
            break
 
        else:
            print("[ERROR] 1, 2 ya 3 enter karein.")
 
 
# =========================================================
# MAIN APPLICATION
# =========================================================
 
def main():
    db = None
 
    try:
        db = DatabaseManager()
 
        product_model = ProductModel(db)
        sales_model = SalesModel(db)
        expense_model = ExpenseModel(db)
 
        while True:
            print("\n========================================")
            print(f"   {SHOP_NAME}")
            print("========================================")
            print("1. View Inventory & Stock Alerts")
            print("2. Add / Update Product Stock")
            print("3. Make a Sale & Generate PDF Invoice")
            print("4. Sales History & Profit Reports")
            print("5. Udaar Book (Credit Customers)")
            print("6. Expense Tracker (Kharcha Book)")
            print("7. Create Database Backup")
            print("8. Exit App")
 
            choice = input(
                "\nApni choice enter karein (1-8): "
            ).strip()
 
            if choice == "1":
                show_inventory(product_model)
 
            elif choice == "2":
                add_products_mode(product_model)
 
            elif choice == "3":
                make_sale(product_model, sales_model)
 
            elif choice == "4":
                show_sales_history(sales_model)
 
            elif choice == "5":
                show_udaar(sales_model)
 
            elif choice == "6":
                expense_menu(expense_model)
 
            elif choice == "7":
                db.backup_database()
 
            elif choice == "8":
                print("[INFO] Software band ho raha hai.")
                break
 
            else:
                print("[ERROR] 1 se 8 ke darmiyan choice enter karein.")
 
    except KeyboardInterrupt:
        print("\n[INFO] Application stopped by user.")
 
    except sqlite3.Error as error:
        print(f"\n[DATABASE ERROR] {error}")
 
    finally:
        if db is not None:
            db.close()
 
 
if __name__ == "__main__":
    main()
