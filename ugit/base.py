from . import data
import os
from pathlib import Path
import itertools
import operator
from collections import namedtuple
import string
from collections import deque, namedtuple
from . import diff

def init():
    data.init()
    data.update_ref('HEAD', data.RefValue(symbolic=True, value='refs/heads/master'))

#把工作目录的文件写入到存储库
# def write_tree(directory='.'):
#     entries=[]
#
#     for entry in Path(directory).iterdir(): #该遍历加上递归会把目录下的子目录遍历出即出现/other/1.txt的对象xxentry.name
#
#         if is_ignored (entry):
#             continue
#         if entry.is_file():
#
#             type_='blob'
#             with open(entry, 'rb') as f:
#                 oid=data.hash_object(f.read())
#
#         elif entry.is_dir():
#             type_ = 'tree'
#             oid=write_tree(entry)
#         entries.append((entry.name, oid, type_))
#     tree = ''.join(f'{type_} {oid} {name}\n'
#                    for name, oid, type_
#                    in sorted(entries)) #生成式推导式
#     return data.hash_object(tree.encode(), 'tree')

#把索引中的文件写入到存储库
def write_tree ():
    # Index is flat, we need it as a tree of dicts
    index_as_tree = {}
    #扁平化化为树状结构
    with data.get_index () as index:

        for path, oid in index.items ():
            # 把目录和文件提取
            path = path.split ('/')
            dirpath, filename = path[:-1], path[-1]
            #定义当前暂存区索引
            current = index_as_tree
            # Find the dict for the directory of this file
            for dirname in dirpath:
                current = current.setdefault (dirname, {})#添加目录名字典键，找不到值则默认为{}current为dirname{}
            #为文件和oid值保存到当前目录dirname字典中
            current[filename] = oid
#     {
#         "dir1": {
#             "dir2": {
#                 "file.txt": "oid_value"
#             }
#         }
#     }
# #在工作区中寻找暂存区的索引并进行哈希处理保存到object中
    def write_tree_recursive(tree_dict):
        entries = []
        for name, value in tree_dict.items():
            if type(value) is dict:#判断是否为自带你类型如果是则为tree
                type_ = 'tree'
                oid = write_tree_recursive(value)
            else:
                type_ = 'blob'
                oid = value
            entries.append((name, oid, type_))

        tree = ''.join(f'{type_} {oid} {name}\n'
                       for name, oid, type_
                       in sorted(entries))
        return data.hash_object(tree.encode(), 'tree')

    return write_tree_recursive(index_as_tree)


#根据oid获取这个文件中夹的信息
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

def read_tree (tree_oid, update_working=False):
    with data.get_index () as index:
        index.clear ()
        index.update (get_tree (tree_oid))

        if update_working:
            _checkout_index (index)

def is_ignored(path):
    return '.ugit' in Path(path).parts or 'ugit-script.py' in Path(path).parts or 'ugit.exe' in Path(path).parts  #关于Path(path).parts https://pytutorial.com/python-pathlibparts-explained-file-path-components/

def commit (message):
    commit=f'tree {write_tree()}\n'
    HEAD=data.get_ref('HEAD').value
    if HEAD:
        commit += f'parent {HEAD}\n'
    MERGE_HEAD = data.get_ref('MERGE_HEAD').value
    if MERGE_HEAD:
        commit += f'parent {MERGE_HEAD}\n'
        data.delete_ref('MERGE_HEAD', deref=False)


    commit += '\n'
    commit += f' {message}\n'
    oid=data.hash_object(commit.encode(), 'commit')
    data.update_ref('HEAD', data.RefValue (symbolic=False, value=oid))
    return oid

Commit = namedtuple ('Commit', ['tree', 'parents', 'message'])


def get_commit (oid):
    parents = []

    commit = data.get_object (oid, 'commit').decode ()
    lines = iter (commit.splitlines ())
    for line in itertools.takewhile (operator.truth, lines):#operator.truth()函数是操作员模块的库函数，用于检查给定值是否为真/真值，如果给定值为真/真值，则返回True ，否则返回False 。
        key, value = line.split (' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parents.append(value)
        else:
            assert False, f'Unknown field {key}'
# lines 迭代器的状态变化：
#
# 初始：lines 指向索引 0（tree 行）。
#
# 在 takewhile 消费过程中：
#
# 消费索引 0 后，指向索引 1。
#
# 消费索引 1 后，指向索引 2。
#
# 消费索引 2（空行）后，由于条件为 False，停止。此时 lines 迭代器已前进到索引 3（" s" 行）。
#
# 经历以上两步运算后 lines 指向的字段
# lines 迭代器当前指向的元素：索引 3 的行，即 " s"。
    message = '\n'.join (lines)
    return Commit (tree=tree, parents=parents, message=message)
def checkout (name):
    oid=get_oid(name)
    commit = get_commit (oid)
    read_tree(commit.tree, update_working=True)
    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=f'refs/heads/{name}')
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)

    data.update_ref('HEAD', HEAD, deref=False)

def reset(oid):
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid))
def is_branch (branch):
    return data.get_ref (f'refs/heads/{branch}').value is not None


def get_branch_name ():
    HEAD = data.get_ref ('HEAD', deref=False)
    if not HEAD.symbolic:
        return None
    HEAD = HEAD.value
    assert HEAD.startswith ('refs/heads/')
    return os.path.relpath (HEAD, 'refs/heads')

def iter_branch_names ():
    for refname, _ in data.iter_refs ('refs/heads/'):
        yield os.path.relpath (refname, 'refs/heads/')
#判断远程提交的祖先是否有本地
def is_ancestor_of (commit, maybe_ancestor):
    return maybe_ancestor in iter_commits_and_parents ({commit})
def create_tag (name, oid):
    # TODO Actually create the tag
    data.update_ref(f'refs/tags/{name}',  data.RefValue (symbolic=False, value=oid))

def get_oid (name):
    if name =='@':name='HEAD'
    ref_to_try={
        f'{name}',
        f'refs/{name}',
        f'refs/tags/{name}',
        f'refs/heads/{name}',
    }
    for ref in ref_to_try:
        if data.get_ref (ref, deref=False).value:
            return data.get_ref(ref).value
        #all() 函数用于判断给定的可迭代参数 iterable 中的所有元素是否都为 TRUE，如果是返回 True，否则返回 False。
    is_hex = all(c in string.hexdigits for c in name)#可以使用 string.hexdigits 来判断一个字符串是否只包含十六进制字符：
    if len(name) == 40 and is_hex:
        return name

    assert False, f'Unknown name {name}'
#找妈妈
def iter_commits_and_parents (oids):
    oids = deque (oids)
    visited = set ()

    while oids:
        oid = oids.popleft ()
        if not oid or oid in visited:
            continue
        visited.add (oid)
        yield oid

        commit = get_commit (oid)

        # Return first parent next
        oids.extendleft(commit.parents[:1])
        # Return other parents later
        oids.extend(commit.parents[1:])

#它的目的是遍历给定的提交（commits）及其所有祖先提交，并 yield 这些提交所引用的所有对象（包括提交对象、树对象和二进制对象）的OID（对象ID）。
def iter_objects_in_commits (oids):
    # N.B. Must yield the oid before acccessing it (to allow caller to fetch it
    # if needed)

    visited = set ()
    def iter_objects_in_tree (oid):
        visited.add (oid)
        yield oid
        for type_, oid, _ in _iter_tree_entries (oid):
            if oid not in visited:
                if type_ == 'tree':
                    yield from iter_objects_in_tree (oid)  #yield from 可以委托给子生成器
                else:
                    visited.add (oid)
                    yield oid

    for oid in iter_commits_and_parents (oids):
        yield oid
        commit = get_commit (oid)
        if commit.tree not in visited:
            yield from iter_objects_in_tree (commit.tree)




def create_branch (name, oid):
    data.update_ref (f'refs/heads/{name}',  data.RefValue (symbolic=False, value=oid))

#获取工作树
def get_working_tree ():
    result = {}
    for root, _, filenames in os.walk ('.'):
        for filename in filenames:
            path = os.path.relpath (f'{root}/{filename}').replace('\\','/')
            if is_ignored (path) or not os.path.isfile (path):
                continue
            with open (path, 'rb') as f:
                result[path] = data.hash_object (f.read ())
    return result

#得到暂存区索引目录
def get_index_tree ():
    with data.get_index () as index:
        return index
def merge (other):
    HEAD = data.get_ref('HEAD').value
    assert HEAD
    merge_base = get_merge_base(other, HEAD)
    c_other = get_commit(other)
    if merge_base == HEAD:
        read_tree(c_other.tree, update_working=True)
        data.update_ref('HEAD',
                        data.RefValue(symbolic=False, value=other))
        print('Fast-forward merge, no need to commit')
        return

    data.update_ref('MERGE_HEAD', data.RefValue(symbolic=False, value=other))

    c_base = get_commit(merge_base)
    c_HEAD = get_commit(HEAD)
    read_tree_merged (c_base.tree, c_HEAD.tree, c_other.tree, update_working=True)
    print('Merged in working tree\nPlease commit')


def get_merge_base (oid1, oid2):
    parents1 = set (iter_commits_and_parents ({oid1}))

    for oid in iter_commits_and_parents ({oid2}):
        if oid in parents1:
            return oid


#清空原有的文件并创建带有差异信息的文件
def read_tree_merged (t_base, t_HEAD, t_other, update_working=False):
    with data.get_index () as index:
        index.clear ()
        index.update (diff.merge_trees (
            get_tree (t_base),
            get_tree (t_HEAD),
            get_tree (t_other)
        ))

        if update_working:
            _checkout_index (index)


def _checkout_index (index):
    _empty_current_directory ()
    for path, oid in index.items ():
        os.makedirs (os.path.dirname (f'./{path}'), exist_ok=True)
        with open (path, 'wb') as f:
            f.write (data.get_object (oid, 'blob'))
#允许添加的路径是目录
def add (filenames):
    #当传入的是文件时 把要提交的文件储存到索引字典中
    def add_file(filename):
        # Normalize path
        filename = os.path.relpath(filename).replace("\\","/")
        with open(filename, 'rb') as f:
            oid = data.hash_object(f.read())
        index[filename] = oid

    #当传入的时目录时把要提交的文件储存到索引字典中
    def add_directory(dirname):
        for root, _, filenames in os.walk(dirname):
            for filename in filenames:
                # Normalize path
                path = os.path.relpath(f'{root}/{filename}').replace("\\","/")
                if is_ignored(path) or not os.path.isfile(path):
                    continue
                add_file(path)
    with data.get_index () as index:
        for name in filenames:
            if os.path.isfile(name):
                add_file(name)
            elif os.path.isdir(name):
                add_directory(name)

