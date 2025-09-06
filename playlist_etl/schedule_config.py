from datetime import datetime, timedelta
from typing import NamedTuple

import pytz
from croniter import croniter


class ScheduleConfig(NamedTuple):
    cron_expression: str = "0 17 * * 6"
    timezone: str = "UTC"
    cache_clear_window_minutes: int = 30


def is_within_scheduled_time_window(
    schedule_config: ScheduleConfig = ScheduleConfig(), current_time: datetime | None = None
) -> bool:
    if current_time is None:
        current_time = datetime.now(pytz.UTC)

    if current_time.tzinfo is None:
        current_time = pytz.UTC.localize(current_time)

    schedule_tz = pytz.timezone(schedule_config.timezone)
    current_time = current_time.astimezone(schedule_tz)

    cron = croniter(schedule_config.cron_expression, current_time)
    next_run = cron.get_next(datetime)

    cron = croniter(schedule_config.cron_expression, current_time)
    prev_run = cron.get_prev(datetime)

    window_duration = timedelta(minutes=schedule_config.cache_clear_window_minutes)

    next_window_start = next_run - window_duration
    if next_window_start <= current_time <= next_run:
        return True

    prev_window_end = prev_run + window_duration
    return prev_run <= current_time <= prev_window_end
