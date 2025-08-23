from . import data
import os
from.import base
REMOTE_REFS_BASE = 'refs/heads/'
LOCAL_REFS_BASE = 'refs/remote/'
#打印远程分支
def fetch (remote_path):

    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)#获取远程分支中的分支和引用
    #根据远程分支中的分支获取object里的引用并补全数据内容
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    # Update local refs to match server
    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE).replace('\\', '/')
        data.update_ref(f'{LOCAL_REFS_BASE}/{refname}',
                        data.RefValue(symbolic=False, value=value))#把远程分支和引用值更新到当地的远程分支中
#根据远程路径把本地存储推到远程分支
def push (remote_path, refname):
    # Get refs data
    remote_refs = _get_remote_refs(remote_path)#获取远程分支
    remote_ref = remote_refs.get(refname)
    local_ref = data.get_ref (refname).value##获取本地分支
    assert local_ref
    # Don't allow force push如果远程分支不是本地提交的祖先或远程提交不存在不能强制推送
    assert not remote_ref or base.is_ancestor_of(local_ref, remote_ref)
    # Compute which objects the server doesn't have
    #把当地和远程的存储数据保存到集合中并通过相减的方式得到两存储库种中有差异的改动，只推送远程库中缺失的部分
    known_remote_refs = filter(data.object_exists, remote_refs.values())#筛选出在本地存储库中存在的远程分支
    remote_objects = set(base.iter_objects_in_commits(known_remote_refs))#远程分支文件
    local_objects = set(base.iter_objects_in_commits({local_ref}))#本地分支文件
    objects_to_push = local_objects - remote_objects#差异文件

    # Push missing objects
##把本地分支中oid文件及其引用复制到远程库中
    # Push all objects
    for oid in objects_to_push:
        data.push_object (oid, remote_path)

    # Update server ref to our value
    #切换到远程分支更新其分支
    with data.change_git_dir (remote_path):
        data.update_ref (refname,
                         data.RefValue (symbolic=False, value=local_ref))




#迭代获取远程分支名即heads里的文件并生成所有分支名：值的字典
def _get_remote_refs (remote_path, prefix=''):
    with data.change_git_dir (remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs (prefix)}
