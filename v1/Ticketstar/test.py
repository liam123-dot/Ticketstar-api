import stripe
stripe.api_key = "sk_test_51NJwFSDXdklEKm0RDJhFhwEBcJLEPOtBtdeovg18JHIIu4HxkXLge19WAPvUap3V0drBuJOgrvccYNgCFaLfsW3x00ME3KwKgi"

response = stripe.Account.create(
  country="GB",
  type="express",
  business_type="individual",
  capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
)
account_id = response['id']

response = stripe.AccountLink.create(
  account=account_id,
  refresh_url="https://example.com/reauth",
  return_url="https://example.com/return",
  type="account_onboarding",

)

print(response)

# from src.Asks.TicketTransfers.GetTransferUrl import *
#
# fixr_email = "carina_phenols.0x@icloud.com"
# fixr_password = "vipWah-nuzxyc-kecti8"
#
# with requests.session() as s:
#   auth_token = login(s, fixr_email, fixr_password)
#
#   get_booking_url = "https://api.fixr.co/api/v2/app/booking?only=future"
#
#   headers = {
#     "Authorization": "Token " + auth_token
#   }
#
#   response = s.get(get_booking_url, headers=headers)
#   print(response)
#   print(json.dumps(response.json(), indent=4))
#
# import pymysql
#
# connection = pymysql.connect(
#     host="localhost",
#     user='root',
#     port=3306,
#     password='Redyred358!',
#     database='ticketstartest'
# )
#
# with connection.cursor() as cursor:
#     with open("all_accounts", "r") as reader:
#         lines = reader.read().split("\n")
#
#         for line in lines:
#             splitter = line.split(",")
#             query = "INSERT INTO fixraccounts(fixr_username, fixr_password) VALUES (%s, %s)"
#             cursor.execute(query, (splitter[0], splitter[1]))
#
# connection.commit()
# connection.close()
