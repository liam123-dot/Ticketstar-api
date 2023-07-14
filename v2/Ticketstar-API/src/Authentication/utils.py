import hmac
import hashlib
import base64


def get_secret_hash(username, CLIENT_ID, CLIENT_SECRET):
    msg = username + CLIENT_ID
    dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                   msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()
