from __future__ import annotations

from db import get_connection


def get_nutrition_info(food_name: str) -> dict | None:
    conn = get_connection()

    row = conn.execute(
        "SELECT energy_kcal, protein_g FROM nutrition WHERE food_name = ? LIMIT 1;",
        (food_name,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "food_name": food_name,
        "kcal": row["energy_kcal"],
        "protein": row["protein_g"],
    }
