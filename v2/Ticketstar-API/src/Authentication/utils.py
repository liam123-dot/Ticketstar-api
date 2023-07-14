import hmac
import hashlib
import base64


class SecretHashGenerationException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'Error generating secret hash: {self.message}'


def get_secret_hash(username, CLIENT_ID, CLIENT_SECRET):
    try:
        msg = username + CLIENT_ID
        dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'),
                       msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()
    except Exception as e:
        raise SecretHashGenerationException(str(e))
