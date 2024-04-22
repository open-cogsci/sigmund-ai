from cryptography.fernet import Fernet
import types
import typing
import logging
logger = logging.getLogger('sigmund')


class EncryptionManager:
    """Handles encryption and decryption of messages and attachments. The
    encryption key is derived from the user's password.
    """
    def __init__(self, encryption_key: typing.Union[str, bytes, None] = None):
        if encryption_key is None:
            logger.warning('no encryption key provided')
            self.fernet = None
            return
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        self.fernet = Fernet(encryption_key)

    def encrypt_data(self, data) -> bytes:
        if self.fernet is None:
            return data.encode('utf-8') if isinstance(data, str) else data
        return self.fernet.encrypt(data)

    def decrypt_data(self, data: bytes):
        if self.fernet is None:
            return data.decode('utf-8') if isinstance(data, bytes) else data
        return self.fernet.decrypt(data)