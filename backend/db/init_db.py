from datetime import date, timedelta
import os
import random
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Sales, Inventory, Finance, Employee
from .session import engine, SessionLocal


def _add_missing(session, model_cls, samples, key_fn):
    existing_rows = session.query(model_cls).all()
    existing_keys = {key_fn(row) for row in existing_rows}
    to_add = [sample for sample in samples if key_fn(sample) not in existing_keys]
    if to_add:
        session.add_all(to_add)


def init_db():
    """Create tables and populate/extend sample data idempotently."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        # Synthetic data scale (kept deterministic via fixed seed below).
        # This makes the chat and dashboards feel "alive" without requiring a real warehouse.
        # Set to 0 to keep only the small handcrafted samples.
        synthetic_scale = int(os.getenv("SYNTHETIC_DATA_SCALE", "3"))
        synthetic_scale = max(0, min(synthetic_scale, 20))
        rng = random.Random(42)

        sales_samples = [
            Sales(date=date(2024, 1, 15), product="Cloud CRM", region="North America", revenue=120000.0, quantity=40),
            Sales(date=date(2024, 2, 11), product="Analytics Suite", region="Europe", revenue=98000.0, quantity=34),
            Sales(date=date(2024, 3, 5), product="Mobile POS", region="APAC", revenue=72000.0, quantity=22),
            Sales(date=date(2024, 4, 9), product="Cloud CRM", region="Europe", revenue=106000.0, quantity=36),
            Sales(date=date(2024, 5, 18), product="Analytics Suite", region="North America", revenue=114000.0, quantity=39),
            Sales(date=date(2024, 6, 7), product="Mobile POS", region="LATAM", revenue=68000.0, quantity=24),
            Sales(date=date(2024, 7, 14), product="Data Warehouse Pro", region="North America", revenue=134000.0, quantity=28),
            Sales(date=date(2024, 8, 20), product="Cloud CRM", region="APAC", revenue=97000.0, quantity=31),
            Sales(date=date(2024, 9, 12), product="Data Warehouse Pro", region="Europe", revenue=121000.0, quantity=27),
            Sales(date=date(2024, 10, 3), product="AI Forecasting", region="North America", revenue=142000.0, quantity=25),
            Sales(date=date(2024, 11, 16), product="AI Forecasting", region="APAC", revenue=109000.0, quantity=19),
            Sales(date=date(2024, 12, 6), product="Analytics Suite", region="Middle East", revenue=88000.0, quantity=26),
        ]

        inventory_samples = [
            Inventory(product="Cloud CRM", category="Software", stock=120, value=180000.0),
            Inventory(product="Analytics Suite", category="Software", stock=65, value=91000.0),
            Inventory(product="Mobile POS", category="Hardware", stock=38, value=76000.0),
            Inventory(product="Data Warehouse Pro", category="Software", stock=52, value=126000.0),
            Inventory(product="AI Forecasting", category="Software", stock=44, value=119000.0),
            Inventory(product="POS Terminal Gen2", category="Hardware", stock=29, value=93000.0),
            Inventory(product="Barcode Scanner X", category="Hardware", stock=72, value=54000.0),
            Inventory(product="Retail Tablet", category="Hardware", stock=47, value=88000.0),
            Inventory(product="Support Premium", category="Services", stock=140, value=45000.0),
            Inventory(product="Implementation Pack", category="Services", stock=84, value=39000.0),
            Inventory(product="BI Connector Pack", category="Add-ons", stock=58, value=62000.0),
            Inventory(product="Security Module", category="Add-ons", stock=41, value=73000.0),
        ]

        finance_samples = [
            Finance(date=date(2024, 1, 31), revenue=200000.0, expense=130000.0, profit=70000.0),
            Finance(date=date(2024, 2, 29), revenue=220000.0, expense=145000.0, profit=75000.0),
            Finance(date=date(2024, 3, 31), revenue=240000.0, expense=155000.0, profit=85000.0),
            Finance(date=date(2024, 4, 30), revenue=255000.0, expense=167000.0, profit=88000.0),
            Finance(date=date(2024, 5, 31), revenue=271000.0, expense=175000.0, profit=96000.0),
            Finance(date=date(2024, 6, 30), revenue=263000.0, expense=182000.0, profit=81000.0),
            Finance(date=date(2024, 7, 31), revenue=289000.0, expense=191000.0, profit=98000.0),
            Finance(date=date(2024, 8, 31), revenue=305000.0, expense=202000.0, profit=103000.0),
            Finance(date=date(2024, 9, 30), revenue=318000.0, expense=211000.0, profit=107000.0),
            Finance(date=date(2024, 10, 31), revenue=330000.0, expense=219000.0, profit=111000.0),
            Finance(date=date(2024, 11, 30), revenue=349000.0, expense=228000.0, profit=121000.0),
            Finance(date=date(2024, 12, 31), revenue=372000.0, expense=241000.0, profit=131000.0),
        ]

        employee_samples = [
            Employee(department="Sales", hire_date=date(2023, 6, 1), termination_date=None, salary=90000.0),
            Employee(department="Finance", hire_date=date(2023, 7, 12), termination_date=None, salary=95000.0),
            Employee(department="HR", hire_date=date(2023, 9, 20), termination_date=None, salary=78000.0),
            Employee(department="Engineering", hire_date=date(2023, 3, 5), termination_date=None, salary=110000.0),
            Employee(department="Sales", hire_date=date(2023, 12, 1), termination_date=date(2024, 2, 28), salary=85000.0),
            Employee(department="Sales", hire_date=date(2024, 1, 15), termination_date=None, salary=82000.0),
            Employee(department="Sales", hire_date=date(2024, 2, 5), termination_date=None, salary=87000.0),
            Employee(department="Sales", hire_date=date(2024, 3, 12), termination_date=None, salary=91000.0),
            Employee(department="Finance", hire_date=date(2024, 1, 22), termination_date=None, salary=98000.0),
            Employee(department="Finance", hire_date=date(2024, 4, 2), termination_date=None, salary=99000.0),
            Employee(department="HR", hire_date=date(2024, 2, 18), termination_date=None, salary=76000.0),
            Employee(department="HR", hire_date=date(2024, 5, 20), termination_date=None, salary=80000.0),
            Employee(department="Engineering", hire_date=date(2024, 1, 9), termination_date=None, salary=118000.0),
            Employee(department="Engineering", hire_date=date(2024, 3, 7), termination_date=None, salary=122000.0),
            Employee(department="Engineering", hire_date=date(2024, 6, 10), termination_date=None, salary=125000.0),
            Employee(department="Operations", hire_date=date(2024, 2, 14), termination_date=None, salary=79000.0),
            Employee(department="Operations", hire_date=date(2024, 4, 25), termination_date=None, salary=83000.0),
            Employee(department="Customer Success", hire_date=date(2024, 3, 11), termination_date=None, salary=77000.0),
            Employee(department="Customer Success", hire_date=date(2024, 7, 8), termination_date=None, salary=81000.0),
            Employee(department="Sales", hire_date=date(2024, 8, 1), termination_date=date(2024, 11, 15), salary=86000.0),
            Employee(department="Operations", hire_date=date(2024, 9, 3), termination_date=date(2024, 12, 20), salary=78000.0),
        ]

        if synthetic_scale > 0:
            products = [
                "Cloud CRM",
                "Analytics Suite",
                "Mobile POS",
                "Data Warehouse Pro",
                "AI Forecasting",
                "POS Terminal Gen2",
                "Barcode Scanner X",
                "Retail Tablet",
                "Support Premium",
                "Implementation Pack",
                "BI Connector Pack",
                "Security Module",
            ]
            regions = ["North America", "Europe", "APAC", "LATAM", "Middle East", "Africa"]

            # Add additional synthetic products (keeps inventory richer).
            categories = ["Software", "Hardware", "Services", "Add-ons"]
            for i in range(1, 1 + 60 * synthetic_scale):
                cat = categories[i % len(categories)]
                prod = f"{cat} Item {i:03d}"
                stock = rng.randint(0, 260)
                # Value roughly proportional to stock with noise.
                unit_value = rng.uniform(120.0, 2400.0) * (1.4 if cat == "Software" else 1.0)
                value = round(stock * unit_value, 2)
                inventory_samples.append(Inventory(product=prod, category=cat, stock=stock, value=value))

            # Sales: daily-ish for ~18 months, weighted by product and region.
            start_day = date(2023, 7, 1)
            days = 540
            sale_products = products + [f"Software Item {i:03d}" for i in range(1, 1 + 20 * synthetic_scale)]
            for d in range(days):
                day = start_day + timedelta(days=d)
                # few deals per day
                deals = rng.randint(1, 3 + synthetic_scale)
                for _ in range(deals):
                    product = rng.choice(sale_products)
                    region = rng.choice(regions)
                    quantity = rng.randint(1, 8 + synthetic_scale * 2)
                    base = rng.uniform(1800, 12000) * (1.6 if "Software" in product or product in products[:5] else 1.0)
                    season = 1.0 + 0.08 * (1 if day.month in (10, 11, 12) else 0)
                    revenue = round(base * quantity * season, 2)
                    sales_samples.append(Sales(date=day, product=product, region=region, revenue=revenue, quantity=quantity))

            # Finance: month-end series for 24 months.
            month_end = date(2023, 1, 31)
            for m in range(24):
                # Approx month-end by adding ~30 days then snapping back a bit if needed.
                approx = month_end + timedelta(days=30 * m)
                month_end_day = date(approx.year, approx.month, 28)
                # Simple trend + noise.
                revenue = 190000 + m * (8500 + 800 * synthetic_scale) + rng.randint(-15000, 20000)
                expense = 120000 + m * (6200 + 550 * synthetic_scale) + rng.randint(-12000, 18000)
                profit = revenue - expense
                finance_samples.append(
                    Finance(
                        date=month_end_day,
                        revenue=float(revenue),
                        expense=float(expense),
                        profit=float(profit),
                    )
                )

            # Employees: hires over time + some terminations.
            departments = ["Sales", "Finance", "HR", "Engineering", "Operations", "Customer Success", "Marketing"]
            base_hire = date(2023, 1, 1)
            for i in range(1, 1 + 50 * synthetic_scale):
                dept = rng.choice(departments)
                hire = base_hire + timedelta(days=rng.randint(0, 700))
                salary_band = {
                    "Engineering": (95000, 165000),
                    "Sales": (65000, 130000),
                    "Finance": (70000, 125000),
                    "HR": (60000, 105000),
                    "Operations": (55000, 98000),
                    "Customer Success": (55000, 105000),
                    "Marketing": (60000, 120000),
                }[dept]
                salary = float(rng.randint(*salary_band))
                # ~18% termination rate in sample
                termination = None
                if rng.random() < 0.18:
                    termination = hire + timedelta(days=rng.randint(30, 420))
                employee_samples.append(
                    Employee(
                        department=dept,
                        hire_date=hire,
                        termination_date=termination,
                        salary=salary,
                    )
                )

        _add_missing(
            session,
            Sales,
            sales_samples,
            lambda row: (row.date, row.product, row.region, row.revenue, row.quantity),
        )
        _add_missing(
            session,
            Inventory,
            inventory_samples,
            lambda row: (row.product, row.category, row.stock, row.value),
        )
        _add_missing(
            session,
            Finance,
            finance_samples,
            lambda row: (row.date, row.revenue, row.expense, row.profit),
        )
        _add_missing(
            session,
            Employee,
            employee_samples,
            lambda row: (row.department, row.hire_date, row.termination_date, row.salary),
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
