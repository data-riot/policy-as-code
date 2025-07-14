from dataclasses import dataclass
from datetime import datetime

@dataclass
class Customer:
    id: str
    signup_date: datetime
    status: str

@dataclass
class Order:
    id: str
    customer: Customer
    order_date: datetime
    delivery_date: datetime
    issue: str

    @property
    def is_late(self):
        return self.issue == "late"