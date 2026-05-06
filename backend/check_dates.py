import os
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
print(f"NOW: {now}")
print(f"MONTH_START: {month_start}")

# Mock dates logic
dates = []
curr = month_start.date()
end_d = now.date()
while curr <= end_d:
    dates.append(curr.strftime("%Y-%m-%d"))
    curr += timedelta(days=1)
print(f"DATES: {dates}")
print(f"TOTAL DATES: {len(dates)}")
