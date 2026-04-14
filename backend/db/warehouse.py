from sqlalchemy import text
from sqlalchemy.orm import Session


class WarehouseClient:
    """Abstract client for a SQL-compatible data warehouse.

    В этом прототипе используется текущая SQLAlchemy-сессия.
    Для реального Snowflake/BigQuery/Redshift замените реализацию query() на соответствующий драйвер.
    """

    def __init__(self, db: Session):
        self.db = db

    def query(self, sql: str):
        result = self.db.execute(text(sql))
        return [dict(row) for row in result]

    def fetch_sales(self):
        return self.query("SELECT * FROM sales ORDER BY date DESC LIMIT 100")

    def fetch_inventory(self):
        return self.query("SELECT * FROM inventory ORDER BY category")

    def fetch_finance(self):
        return self.query("SELECT * FROM finance ORDER BY date DESC LIMIT 100")

    def fetch_employees(self):
        return self.query("SELECT * FROM employees ORDER BY hire_date DESC LIMIT 100")
