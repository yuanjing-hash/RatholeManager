# backend/security.py
from cryptography.fernet import Fernet

# !!! 重要 !!!
# 这个密钥绝对不能硬编码在代码里。在生产环境中，应该从环境变量或安全的配置文件中读取。
# 为了演示，我们先生成一个。请确保这个 KEY 的安全，一旦丢失，所有密码都无法解密。
# 你可以运行 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 来生成自己的密钥。
SECRET_KEY = b'pzsZzVd-hizgDy_u-M9Ypm2y2x41gT8m5eL2t_G2gPY='

cipher_suite = Fernet(SECRET_KEY)

def encrypt_password(password: str) -> str:
    """加密密码"""
    encrypted_text = cipher_suite.encrypt(password.encode('utf-8'))
    return encrypted_text.decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    decrypted_text = cipher_suite.decrypt(encrypted_password.encode('utf-8'))
    return decrypted_text.decode('utf-8')