import os
import shutil
import tempfile
from collections import defaultdict
import subprocess
from tempfile import NamedTemporaryFile as Temp
from . import  diff_git_rel_diff
from . import data


#处理输出两次提交的oid
def compare_trees(*trees):
    #*可传入多个参数
    entries = defaultdict(lambda: [None] * len(trees))
    #创建默认字典 entries，自动为不存在的键生成默认值。

    #lambda: [None] * len(trees): 为每个新键生成一个长度为树数量的列表，所有元素初始化为 None。
    for i, tree in enumerate(trees):

        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)


#
def diff_blobs(o_from, o_to, path='blob'):
    #创建两个临时文件
    with Temp() as f_from, Temp() as f_to:
        for oid, f in ((o_from, f_from), (o_to, f_to)):  #元组解包的迭代
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        #Linux的diff命令用于比较两个文件差异,windows下可以尝试用git diff命令
        # with subprocess.Popen(
        #         ['diff', '--unified', '--show-c-function',
        #          '--label', f'a/{path}', f_from.name,
        #          '--label', f'b/{path}', f_to.name],
        #         stdout=subprocess.PIPE) as proc:
        #
        #         output, _ = proc.communicate()

        output = diff_git_rel_diff.diff_show(f_from, f_to, path)

        return output


def iter_changed_files(t_from, t_to):
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = ('new file' if not o_from else
                      'deleted' if not o_to else
                      'modified')
            yield path, action


def merge_trees(t_base, t_HEAD, t_other):
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_object (merge_blobs (o_base, o_HEAD, o_other))
    return tree



def merge_blobs (o_base, o_HEAD, o_other):
    with Temp () as f_base, Temp () as f_HEAD, Temp () as f_other:

        # Write blobs to files
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write (data.get_object (oid))
                f.flush ()

        with subprocess.Popen (
            ['diff3', '-m',
             '-L', 'HEAD', f_HEAD.name,
             '-L', 'BASE', f_base.name,
             '-L', 'MERGE_HEAD', f_other.name,
            ], stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate ()
            assert proc.returncode in (0, 1)

        return output



#返回两次提交差异
def diff_trees(t_from, t_to):
    output = b''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output


import tempfile
import os
import subprocess


def merge_blobs_c(o_base, o_HEAD, o_other):
    # 创建临时目录来存储文件
    temp_dir = tempfile.mkdtemp()
    temp_files = []

    try:
        # 准备文件数据
        file_data = []
        for oid, label in [(o_base, 'base'), (o_HEAD, 'HEAD'), (o_other, 'other')]:
            if oid:
                content = data.get_object(oid)
                # 确保内容是字节类型
                if isinstance(content, str):
                    content = content.encode('utf-8')

                # 创建临时文件路径
                file_path = os.path.join(temp_dir, f"{label}.tmp")
                with open(file_path, 'wb') as f:  # 使用二进制模式写入
                    f.write(content)
                file_data.append(file_path)
            else:
                # 对于不存在的对象，创建一个空文件
                file_path = os.path.join(temp_dir, f"{label}.tmp")
                with open(file_path, 'wb') as f:
                    f.write(b'')
                file_data.append(file_path)

        # 提取文件路径
        f_base_path, f_HEAD_path, f_other_path = file_data

        # 准备 git merge-file 命令
        cmd = [
            'git', 'merge-file',
            '--diff3',
            '-L', 'HEAD',
            '-L', 'BASE',
            '-L', 'MERGE_HEAD',
            f_HEAD_path,
            f_base_path,
            f_other_path
        ]

        # 运行命令
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, errors = proc.communicate()

        # git merge-file 返回 0 表示成功，1 表示有冲突，>1 表示错误
        if proc.returncode > 1:
            raise Exception(f"git merge-file failed: {errors.decode('utf-8', errors='replace')}")

        # 读取合并后的内容
        with open(f_HEAD_path, 'rb') as f:
            result = f.read()

        return result

    finally:
        # 清理临时目录和文件
        try:
            for file_path in file_data:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass  # 忽略清理错误