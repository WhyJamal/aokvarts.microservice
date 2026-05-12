from datetime import datetime, timedelta


def get_date_range(period: str):
    today = datetime.now().date()

    if period == "yesterday":
        start = today - timedelta(days=1)
        end = today

    elif period == "month":
        start = today.replace(day=1)
        end = today

    elif period == "year":
        start = today.replace(month=1, day=1)
        end = today

    else:
        start = today
        end = today

    return (
        start.strftime("%Y-%m-%d") + "T00:00:00.000",
        end.strftime("%Y-%m-%d") + "T00:00:00.000",
    )