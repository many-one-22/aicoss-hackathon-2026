"""
sentiment_lookup.py
"""

from db import get_connection  # app/ 패키지로 옮기면 "from app.db import get_connection"으로 변경


def get_sentiment_info(poi_id: str) -> list[dict]:
    conn = get_connection()

    rows = conn.execute(
        "SELECT aspect, positive_count, neutral_count, negative_count, trend_tag "
        "FROM restaurant_sentiment WHERE restaurant_id = ?;",
        (poi_id,),
    ).fetchall()

    conn.close()

    return [
        {
            "aspect": row["aspect"],
            "positive_count": row["positive_count"],
            "neutral_count": row["neutral_count"],
            "negative_count": row["negative_count"],
            "trend_tag": row["trend_tag"],
        }
        for row in rows
    ]


def get_trend_tags_only(poi_id: str) -> list[str]:
    info = get_sentiment_info(poi_id)
    return [row["trend_tag"] for row in info if row["trend_tag"]]
