import subprocess
from . import data
def diff_DHEAD(f_HEAD, f_other,o_HEAD, o_other):

    cmd = [
        'git', 'diff',
        '--no-index',  # 比较非git仓库中的文件
        '--unified=0',  # 不显示上下文行
        f_HEAD.name,
        f_other.name
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=False
    )
    output, err = proc.communicate()

    # 处理错误情况
    if proc.returncode > 1:  # 0=无差异 1=有差异 2=错误
        raise RuntimeError(f"git diff failed: {err.decode('utf-8', 'ignore')}")

    # 如果文件完全一致，直接返回
    if not output or proc.returncode == 0:
        if o_HEAD:
            return data.get_object(o_HEAD)
        if o_other:
            return data.get_object(o_other)
        return b''

    # 处理输出转换为条件编译格式
    return convert_to_conditional_compilation(output, f_HEAD, f_other)


def diff_show(f_from,f_to, path='blob'):
    cmd = [
        'git', 'diff',
        '--no-index',  # 比较非索引文件
        '--unified',  # 统一差异格式
        '--no-color',  # 禁用颜色输出
        '--no-ext-diff',  # 禁用外部差异工具
        f_from.name,
        f_to.name
    ]

    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        output, _ = proc.communicate()

        # 手动添加自定义标签
        header = f"diff --a/{path} b/{path}\n".encode('utf-8')
        from_line = f"--- a/{path}\n".encode('utf-8')
        to_line = f"+++ b/{path}\n".encode('utf-8')

        # 移除原始头部（前3行）
        diff_content = b'\n'.join(output.split(b'\n')[4:])

        # 组合自定义头部和差异内容
        output = header + from_line + to_line + diff_content

    return output


def convert_to_conditional_compilation(diff_output, f_HEAD, f_other):
    """将git diff输出转换为-DHEAD的条件编译格式"""
    # 读取两个文件的全部内容
    with open(f_HEAD.name, 'rb') as f:
        head_content = f.read().splitlines(keepends=True)

    with open(f_other.name, 'rb') as f:
        other_content = f.read().splitlines(keepends=True)

    # 解析git diff输出
    output_lines = []
    diff_output = diff_output.decode('utf-8', 'replace')

    # 状态机变量
    HEAD_active = False
    other_active = False
    current_block = []

    for line in diff_output.splitlines():
        # 忽略元数据行
        if line.startswith('diff --git') or line.startswith('index'):
            continue

        # 文件头标记
        if line.startswith('--- a/'):
            current_line = 1
            continue
        if line.startswith('+++ b/'):
            continue

        # 差异块头部
        if line.startswith('@@'):
            parts = line.split(' ')
            # 获取行号信息
            head_range = parts[1][1:]  # 格式: -start_line,line_count
            other_range = parts[2][1:]  # 格式: +start_line,line_count

            # 输出前一个区块
            output_lines.extend(current_block)
            current_block = []

            # 解析行号范围
            head_start, head_count = parse_range(head_range)
            other_start, other_count = parse_range(other_range)

            # 激活HEAD块
            HEAD_active = True
            other_active = False
            current_block.append(b'#ifdef HEAD\n')

            # 输出HEAD内容
            if head_start > 0 and head_count > 0:
                current_block.extend(head_content[head_start - 1:head_start + head_count - 1])

            # 切换到other块
            current_block.append(b'#else\n')
            HEAD_active = False
            other_active = True

            # 输出other内容
            if other_start > 0 and other_count > 0:
                current_block.extend(other_content[other_start - 1:other_start + other_count - 1])

            # 结束区块
            current_block.append(b'#endif\n')
            HEAD_active = False
            other_active = False

    # 输出最后区块
    output_lines.extend(current_block)

    # 合并所有行
    result = b''.join(output_lines)
    return result


def parse_range(range_str):
    """解析行号范围"""
    if ',' in range_str:
        start, count = range_str.split(',')
        return int(start), int(count)
    return int(range_str), 1