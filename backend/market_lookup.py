from __future__ import annotations

from db import get_connection


def get_market_info(market_name: str) -> dict | None:
    conn = get_connection()

    row = conn.execute(
        "SELECT market_name, address, sido, sigungu, num_stores, items, open_cycle, parking_p02, parking_p03 "
        "FROM markets WHERE market_name = ? LIMIT 1;",
        (market_name,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "name": row["market_name"],
        "address": row["address"],
        "sido": row["sido"],
        "sigungu": row["sigungu"],
        "num_stores": row["num_stores"],
        "items": row["items"],
        "open_cycle": row["open_cycle"],
        # parking_p02/p03는 markets 테이블 전용 'Y'/'N' 형식 (restaurants.parking은 '있음'/'없음'이라 다름 — SCHEMA_NOTES.md)
        "parking": row["parking_p02"] == "Y" or row["parking_p03"] == "Y",
    }
