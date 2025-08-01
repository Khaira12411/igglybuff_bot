from datetime import datetime, timedelta
from typing import Tuple


def get_day_range_by_index(
    day_1_start: datetime, day_number: int
) -> Tuple[datetime, datetime]:
    """
    Given a starting datetime and day_number (1-based), return (start, end) of the drop window.
    """
    start = day_1_start + timedelta(days=day_number - 1)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return (start, end)
