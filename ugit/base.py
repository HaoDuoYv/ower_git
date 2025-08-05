from . import data
import os
from pathlib import Path
import itertools
import operator
from collections import namedtuple
def write_tree(directory='.'):
    entries=[]

    for entry in Path(directory).iterdir(): #该遍历加上递归会把目录下的子目录遍历出即出现/other/1.txt的对象xx

        if is_ignored (entry):
            continue
        if entry.is_file():

            type_='blob'
            with open(entry, 'rb') as f:
                oid=data.hash_object(f.read())


        elif entry.is_dir():
            type_ = 'tree'
            oid=write_tree(entry)
        entries.append((entry.name, oid, type_))
    tree = ''.join(f'{type_} {oid} {name}\n'
                   for name, oid, type_
                   in sorted(entries)) #生成式推导式
    return data.hash_object(tree.encode(), 'tree')

def _iter_tree_entries (oid):
    if not oid:
        return
    tree = data.get_object (oid, 'tree')
    for entry in tree.decode ().splitlines ():
        type_, oid, name = entry.split (' ', 2)
        yield type_, oid, name


def get_tree (oid, base_path=''):
    result = {}
    for type_, oid, name in _iter_tree_entries (oid):
        assert '/' not in name
        assert name not in ('..', '.')
        path = base_path + name
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update (get_tree (oid, f'{path}/'))
        else:
            assert False, f'Unknown tree entry {type_}'
    return result

def _empty_current_directory ():
     for root, dirnames, filenames in os.walk ('.', topdown=False):
         for filename in filenames:
             path = os.path.relpath (f'{root}/{filename}')
             if is_ignored (path) or not os.path.isfile (path):
                 continue
             os.remove (path)
         for dirname in dirnames:
             path = os.path.relpath (f'{root}/{dirname}')
             if is_ignored (path):
                 continue
             try:
                 os.rmdir (path)
             except (FileNotFoundError, OSError):
                 # Deletion might fail if the directory contains ignored files,
                 # so it's OK
                 pass

def read_tree (tree_oid):
    _empty_current_directory()
    for path, oid in get_tree (tree_oid, base_path='./').items ():
        os.makedirs (os.path.dirname (path), exist_ok=True)
        with open (path, 'wb') as f:
            f.write (data.get_object (oid))

def is_ignored(path):
    return '.ugit' in Path(path).parts or 'ugit-script.py' in Path(path).parts or 'ugit.exe' in Path(path).parts  #关于Path(path).parts https://pytutorial.com/python-pathlibparts-explained-file-path-components/

def commit (message):
    commit=f'tree {write_tree()}\n'
    HEAD=data.get_HEAD()
    if HEAD:
        commit += f'parent {HEAD}\n'
    commit += '\n'
    commit += f' {message}\n'
    oid=data.hash_object(commit.encode(), 'commit')
    data.set_HEAD(oid)
    return oid

Commit = namedtuple ('Commit', ['tree', 'parent', 'message'])


def get_commit (oid):
    parent = None

    commit = data.get_object (oid, 'commit').decode ()
    lines = iter (commit.splitlines ())
    for line in itertools.takewhile (operator.truth, lines):
        key, value = line.split (' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'Unknown field {key}'

    message = '\n'.join (lines)
    return Commit (tree=tree, parent=parent, message=message)