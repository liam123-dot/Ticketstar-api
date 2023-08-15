import requests
import sys

response = requests.get('https://organiser-legacy.fixr.co/api/v2/app/ticket-reference/QMBNU3FRgWpFCm8xMjAGn5/209d27f065/pdf')

print(sys.getsizeof(response.text))
