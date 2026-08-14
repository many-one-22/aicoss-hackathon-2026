import json
from datetime import date

from app.db import get_connection


def get_price_info(item_name: str) -> dict | None:
    conn = get_connection()

    price_row = conn.execute(
        "SELECT price, unit FROM prices WHERE item = ? ORDER BY year_month DESC LIMIT 1;",
        (item_name,),
    ).fetchone()

    season_row = conn.execute(
        "SELECT current_price, level, peak_months FROM seasonality WHERE item = ? LIMIT 1;",
        (item_name,),
    ).fetchone()

    conn.close()

    if price_row is None and season_row is None:
        return None

    peak_months = json.loads(season_row["peak_months"]) if season_row else []

    return {
        "item": item_name,
        "current_price": season_row["current_price"] if season_row else price_row["price"],
        "unit": price_row["unit"] if price_row else None,
        "price_level": season_row["level"] if season_row else None,
        "peak_months": peak_months,
        "is_in_season": date.today().month in peak_months,
    }
