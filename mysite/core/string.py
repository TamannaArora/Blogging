
'''
Cryptography
'''
import random
import hashlib
from cryptography.fernet import Fernet, InvalidToken



class Hash(object):
    ''' Hash '''
    _fernet_key = 'zN6Ug74660fIGBldj2nlItDAvCoaFsP1oUAeQhXnjbI='

    """

            salt = str(random.random()).encode('utf-8')
            salt =  hashlib.sha1(salt).hexdigest() + self.email +  hashlib.sha1(salt).hexdigest()[5:10]
            lenslug = 210
            self.user_hash = hashlib.sha1(salt.encode('utf-8')).hexdigest()
            self.hash_expire = datetime.datetime.today() + datetime.timedelta(10)
    """

    @staticmethod
    def _generatesalt():
        salt = hashlib.sha1(str(random.random()).encode('utf-8'))
        return salt.hexdigest()

    @staticmethod
    def createhashforstring(string):
        ''' createhashforstring '''
        salt = Hash._generatesalt()
        salt = salt[0:5] + string + salt[0:5]
        return hashlib.sha1(salt.encode('utf-8')).hexdigest()

    @staticmethod
    def encrypt_string(plain_text):
        ''' encrypt_string '''
        cipher_suite = Fernet(Hash._fernet_key)
        plain_text = plain_text.encode('utf-8')
        return cipher_suite.encrypt(plain_text)

    @staticmethod
    def decrypt_string(encryted_text):
        ''' decrypt_string '''
        cipher_suite = Fernet(Hash._fernet_key)
        try:
            return cipher_suite.decrypt(encryted_text)
        except InvalidToken:
            return b''
