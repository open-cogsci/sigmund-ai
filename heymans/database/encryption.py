from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, encryption_key: [str, bytes]):
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        self.fernet = Fernet(encryption_key)

    def encrypt_data(self, data) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt_data(self, data: bytes):
        return self.fernet.decrypt(data)
