from datetime import datetime
import pytz

# Create a datetime object for the given date and time in London
london_timezone = pytz.timezone('Europe/London')
dt = london_timezone.localize(datetime(2023, 8, 20, 11, 0))

# Convert to epoch time
epoch_time = int(dt.timestamp())

human_readable_time = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')

print(human_readable_time)