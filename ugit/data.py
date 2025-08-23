import os
import hashlib
from collections import namedtuple
from contextlib import contextmanager
import shutil
import json

# Will be initialized in cli.main()
GIT_DIR = None

#关于装饰器
#Python提供内置的contextlib库，使得上线文管理器更加容易使用。其中包含如下功能：

#（1）装饰器contextmanager。该装饰器将一个函数中yield语句之前的代码当做__enter__方法执行，yield语句之后的代码当做__exit__方法执行。同时yield返回值赋值给as后的变量。



@contextmanager
def change_git_dir (new_dir):
    global GIT_DIR
    old_dir = GIT_DIR#保存原本的储存库
    GIT_DIR = f'{new_dir}/.ugit'#临时定义远程储存库
    yield
    GIT_DIR = old_dir#关闭后恢复储存库

def init():
    os.makedirs(GIT_DIR)
    os.makedirs(f'{GIT_DIR}/object')

RefValue = namedtuple ('RefValue', ['symbolic', 'value'])

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
def update_ref (ref, value, deref=True):

    ref = _get_ref_internal (ref, deref)[0]
    assert value.value
    if value.symbolic:
        value = f'ref: {value.value}'
    else:
        value = value.value
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs (os.path.dirname (ref_path), exist_ok=True)
    with open (ref_path, 'w') as f:
        f.write (value)
def get_ref (ref, deref=True):
    return _get_ref_internal (ref, deref)[1]


def delete_ref (ref, deref=True):
    ref = _get_ref_internal (ref, deref)[0]
    os.remove (f'{GIT_DIR}/{ref}')

def _get_ref_internal (ref, deref):
    ref_path = f'{GIT_DIR}/{ref}'
    value=None
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()


    symbolic = bool (value) and value.startswith ('ref:')
    if symbolic:
        value = value.split (':', 1)[1].strip ()
        if deref:
            return _get_ref_internal(value, deref=True)

    return ref, RefValue(symbolic=symbolic, value=value)


def iter_refs (prefix='',deref=True):
    refs = ['HEAD','MERGE_HEAD']
    for root, _, filenames in os.walk(f'{GIT_DIR}/refs/'):

        root = os.path.relpath(root, GIT_DIR).replace('\\','/')
        refs.extend(f'{root}/{name}' for name in filenames)

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        ref = get_ref(refname, deref=deref)
        if ref.value:
            yield refname, ref

#判断文件在当前存储库中是否存在
def object_exists (oid):
    return os.path.isfile (f'{GIT_DIR}/objects/{oid}')

#文件不存在时在远程存储库中寻找并复制到本地存储中
def fetch_object_if_missing (oid, remote_git_dir):
    if object_exists (oid):
        return
    remote_git_dir += '/.ugit'
    shutil.copy (f'{remote_git_dir}/objects/{oid}',
                 f'{GIT_DIR}/objects/{oid}')#shutil时python标准库有移动，复制，删除，解压缩等功能

#把本地分支中oid文件及其引用复制到远程库中
def push_object (oid, remote_git_dir):
    remote_git_dir += '/.ugit'
    shutil.copy (f'{GIT_DIR}/objects/{oid}',
                 f'{remote_git_dir}/objects/{oid}')
#添加索引
@contextmanager
def get_index ():
#enter
    index = {}
    if os.path.isfile (f'{GIT_DIR}/index'):
        with open (f'{GIT_DIR}/index') as f:
            index = json.load (f)#读取json转化为字典

    yield index  #作为f输出
#close
    with open (f'{GIT_DIR}/index', 'w') as f:
        json.dump (index, f)#使用json.dump()方法将字典写入文件
