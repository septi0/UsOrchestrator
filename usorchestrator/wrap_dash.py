def wrap_dash(header: str, stdout: list, stderr: list) -> str:
    ret = ''

    stdout_str = '\n'.join(stdout)
    stderr_str = '\n'.join(stderr)

    input = stdout_str
    if stderr_str:
        if input: input += '\n' + stderr_str
        else: input += stderr_str
        
    input = input.splitlines()
    header = header + ':'

    if not input: input = ' '

    length = len(max(input, key=len))
    if(len(header) > length): length = len(header)

    ret += '+' + '-' * length + '+\n'
    ret += f'|{header.ljust(length)}|\n'
    ret += '+' + '-' * length + '+\n'

    for line in input:
        ret += f'|{line.ljust(length)}|\n'

    ret += '+' + '-' * length + '+\n'
    
    return ret