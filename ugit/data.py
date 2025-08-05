import os
import hashlib
GIT_DIR='.ugit'
def init():
    os.makedirs(GIT_DIR)
    os.makedirs(f'{GIT_DIR}/object')
def hash_object(data,type_='blob'):
    #作用：用于区分不同目录下的相同文件名？
    obj = type_.encode() + b'\x00' + data #encode默认编码utf-8 https://www.runoob.com/python/att-string-encode.html
    oid=hashlib.sha1(obj).hexdigest()
    with open(f'{GIT_DIR}/object/{oid}', 'wb') as out:
        out.write(obj)
    return oid
def get_object(oid,expected='blob'):
    with open(f'{GIT_DIR}/object/{oid}', 'rb') as f:
        obj= f.read()

    type_, _, content = obj.partition (b'\x00')#解包
    type_ = type_.decode ()

    if expected is not None:
        assert type_ == expected, f'Expected {expected}, got {type_}'#关于assert https://c.biancheng.net/ref/assert.html
    return content
def set_HEAD(oid):
    with open(f'{GIT_DIR}/HEAD', 'w') as f:
        f.write(oid)
def get_HEAD():
    if os.path.isfile(f'{GIT_DIR}/HEAD'):
        with open(f'{GIT_DIR}/HEAD') as f:
            return f.read().strip()