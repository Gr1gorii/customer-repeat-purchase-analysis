import pandas as pd
import pytest

from retail.clean import clean
from retail.pipeline import build_database, query_outputs


def line(invoice, date, customer=1, quantity=1, price=10, stock="A", country="UK"):
    return {
        "InvoiceNo": invoice,
        "StockCode": stock,
        "Description": "Test item",
        "Quantity": quantity,
        "InvoiceDate": pd.Timestamp(date),
        "UnitPrice": price,
        "CustomerID": customer,
        "Country": country,
    }


@pytest.fixture
def edge_data():
    rows = [
        line("100", "2011-01-01 12:00", quantity=4),
        line("101", "2011-01-31 12:00"),  # Exactly the 30-day inclusive boundary.
        line("200", "2011-01-01", customer=2),
        line("201", "2011-02-01", customer=2),  # Outside 30, inside 60.
        line("300", "2011-03-15", customer=3),  # No full 30-day observation.
        line("400", "2011-01-02", customer=4),
        line("401", "2011-01-02", customer=4),  # Separate same-time invoice is a repeat.
        line("C100", "2011-02-02", quantity=-2),
        line("C101", "2011-02-03", quantity=-2),  # Same prior line can be a candidate twice.
        line("C102", "2011-02-04", quantity=-9),  # Too large for an individual prior line.
        line("C103", "2011-02-04", quantity=-1, price=11),  # Different price.
        line("C104", "2010-12-31", quantity=-1),  # Earlier than the purchase.
        line("C105", "2011-02-05", quantity=-1, customer=None),
        line("500", "2011-02-05", quantity=2, customer=None),
        line("adjust", "2011-02-06", quantity=-1, customer=None),
        line("Cpositive", "2011-02-07", quantity=1, customer=5),
        line("free", "2011-02-08", price=0, customer=6),
        line("badprice", "2011-02-08", price=-2),
        line("zerounits", "2011-02-08", quantity=0),
        line("fraction", "2011-02-08", quantity=1.5),
        line("end", "2011-04-10", customer=7),
    ]
    rows.append(rows[0].copy())
    raw = pd.DataFrame(rows)
    frame, quality = clean(raw)
    connection = build_database(frame)
    yield raw, frame, quality, connection, query_outputs(connection)
    connection.close()
