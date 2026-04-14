from datetime import date
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
