from sqlalchemy import text
from db.connections import get_engine

def get_timesheet_data():
    try:
        engine = get_engine("timesheet")

        query = text("""
            SELECT COUNT(DISTINCT h1.employeeid) AS total_users
            FROM [hikaccess] h1
            WHERE
                h1.[direction] = 'IN'
                AND h1.[DateTime] >= CAST(CAST(GETDATE() - 1 AS DATE) AS DATETIME)
                AND NOT EXISTS (
                    SELECT 1
                    FROM [hikaccess] h2
                    WHERE
                        h2.[employeeid] = h1.[employeeid]
                        AND h2.[direction] = 'OUT'
                        AND h2.[DateTime] > h1.[DateTime]
                );
        """)

        with engine.connect() as conn:
            result = conn.execute(query)
            row = result.fetchone()
            return {
                "total_users": row[0] if row and row[0] is not None else 0
            }

    except Exception as e:
        print("Timesheet DB error:", e)
        return {
            "total_users": 0
        }