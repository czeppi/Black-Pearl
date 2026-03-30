import aesio
import binascii
import microcontroller
import adafruit_hashlib
import os


MACROS_FNAME = 'macros.enc'


#def main():
#    macros = dict(read_macros())
#    print(macros)


def read_macros():
    return dict(_iter_macros())


def _iter_macros():
    with open(MACROS_FNAME, 'r') as fh:
        for line in fh.readlines():
            i = line.find(':')
            if i <= 0:
                return None

            macro_name = line[:i]
            macro_desc_encrypted_str = line[i + 1:].strip()
            macro_desc_encrypted_bytes = bytes.fromhex(macro_desc_encrypted_str)
            # print(f'{macro_name}: "{macro_desc_encrypted_bytes}"  [{len(macro_desc_encrypted_bytes)}]')

            decrypted_text = _decrypt(macro_desc_encrypted_bytes).strip()
            # print(f'{macro_name}: "{decrypted_text}"')

            yield macro_name, decrypted_text


def _decrypt(encrypted_bytes: bytes) -> str:
    aes = _create_aes()
    decrypted_bytes = bytearray(len(encrypted_bytes))
    aes.decrypt_into(encrypted_bytes, decrypted_bytes)  # -> decrypted_bytes
    return decrypted_bytes.decode('utf-8')


def _create_aes() -> aesio.AES:
    key_iv = adafruit_hashlib.sha256(microcontroller.cpu.uid).digest()
    key = key_iv[:16] # 16 chars
    iv = key_iv[len(key_iv) - 16:] # 16 chars
    aes = aesio.AES(key, aesio.MODE_CBC, iv)
    return aes


def _old():
    key_iv = adafruit_hashlib.sha256(microcontroller.cpu.uid).digest()
    #print(key_iv)
    key = key_iv[:16] # 16 chars
    iv = key_iv[len(key_iv) - 16:] # 16 chars
    plain_text = b'Hallo 1234567890'  # 16 chars
    print(f'plain_text: {plain_text} ({len(plain_text)})')
    print(f'key:        {key} ({len(key)})')
    print(f'iv:         {iv} ({len(iv)})')

    # encrypt
    cipher = aesio.AES(key, aesio.MODE_CBC, iv)
    encrypted_text = bytearray(len(plain_text))
    cipher.encrypt_into(plain_text, encrypted_text)
    print(f'encrypted_text: {encrypted_text}')

    # decrypt
    cipher = aesio.AES(key, aesio.MODE_CBC, iv)
    decrypted_text = bytearray(len(encrypted_text))
    cipher.decrypt_into(encrypted_text, decrypted_text)  # -> decrypted_text
    print(f'decrypted_text: {decrypted_text}')
