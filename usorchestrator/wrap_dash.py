def wrap_dash(header: str, stdout: str, stderr: str) -> str:
    ret = ''

    input = stdout
    if stderr:
        if input: input += '\n' + stderr
        else: input += stderr
        
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