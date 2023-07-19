# import cv2
#
# def read_qr_code(filename):
#     """Read an image and read the QR code.
#
#     Args:
#         filename (string): Path to file
#
#     Returns:
#         qr (string): Value from QR code
#     """
#
#     try:
#         img = cv2.imread(filename)
#         detect = cv2.QRCodeDetector()
#         value, points, straight_qrcode = detect.detectAndDecode(img)
#         return value
#     except:
#         return
#
#
# print(read_qr_code("ticket_8QD6NyNxcH3xaAkPyjwUhh-1.png"))


url = "https://api.fixr.co/api/v2/app/booking?only=future&limit=999"

headers = {
    "Authorization": "Token ae7fe9321bab58f53ce4beb9796330d9f2c9c10e"
}

import requests

response = requests.get(url, headers=headers)

print(response)
print(response.text)

