from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import Sales, Inventory, Finance, Employee


def gather_dashboard_metrics(db: Session) -> dict:
    total_revenue = db.query(func.sum(Sales.revenue)).scalar() or 0
    active_deals = db.query(func.count(Sales.id)).scalar() or 0
    inventory_value = db.query(func.sum(Inventory.value)).scalar() or 0
    employee_count = db.query(func.count(Employee.id)).scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "active_deals": int(active_deals),
        "inventory_value": float(inventory_value),
        "employee_count": int(employee_count),
    }


def gather_sales_metrics(db: Session) -> dict:
    sales_by_region = (
        db.query(Sales.region, func.sum(Sales.revenue).label("revenue"))
        .group_by(Sales.region)
        .all()
    )
    sales_by_product = (
        db.query(Sales.product, func.sum(Sales.revenue).label("revenue"))
        .group_by(Sales.product)
        .all()
    )
    monthly_revenue = (
        db.query(Sales.date, func.sum(Sales.revenue).label("revenue"))
        .group_by(Sales.date)
        .order_by(Sales.date)
        .all()
    )
    return {
        "sales_by_region": [{"region": row[0], "revenue": float(row[1])} for row in sales_by_region],
        "sales_by_product": [{"product": row[0], "revenue": float(row[1])} for row in sales_by_product],
        "monthly_revenue": [{"date": row[0].isoformat(), "revenue": float(row[1])} for row in monthly_revenue],
    }


def gather_inventory_metrics(db: Session) -> dict:
    inventory_by_category = (
        db.query(Inventory.category, func.sum(Inventory.value).label("value"))
        .group_by(Inventory.category)
        .all()
    )
    low_stock = db.query(Inventory).filter(Inventory.stock <= 50).count()
    total_value = db.query(func.sum(Inventory.value)).scalar() or 0
    return {
        "inventory_by_category": [{"category": row[0], "value": float(row[1])} for row in inventory_by_category],
        "low_stock_items": int(low_stock),
        "total_inventory_value": float(total_value),
    }


def gather_finance_metrics(db: Session) -> dict:
    finance_trend = (
        db.query(Finance.date, Finance.revenue, Finance.expense, Finance.profit)
        .order_by(Finance.date)
        .all()
    )
    return {
        "finance_trend": [
            {
                "date": row[0].isoformat(),
                "revenue": float(row[1]),
                "expense": float(row[2]),
                "profit": float(row[3]),
            }
            for row in finance_trend
        ]
    }


def gather_hr_metrics(db: Session) -> dict:
    total_employees = db.query(func.count(Employee.id)).scalar() or 0
    turnover_count = db.query(Employee).filter(Employee.termination_date.isnot(None)).count()
    department_distribution = (
        db.query(Employee.department, func.count(Employee.id).label("count"))
        .group_by(Employee.department)
        .all()
    )
    return {
        "headcount": int(total_employees),
        "turnover": int(turnover_count),
        "department_distribution": [
            {"department": row[0], "count": int(row[1])} for row in department_distribution
        ],
    }
