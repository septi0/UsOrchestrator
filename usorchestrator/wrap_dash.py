import re

def wrap_dash(header: str, stdout: list, stderr: list) -> str:
    ret = ''

    stdout_str = '\n'.join(stdout)
    stderr_str = '\n'.join(stderr)

    input = stdout_str
    if stderr_str:
        input = input + ('\n' if input else '') + stderr_str

    if not input:
        input = ' '

    # get length of the header but without the possible color codes (ANSI)
    header_len = len(normalize_str(header))
    input = input.splitlines()
    length = 0
    input_safe = []

    # process each line
    for line in input:
        # replace whitespaceces from the end of the line
        # replace tabs with 4 spaces
        line_safe = line.rstrip().replace('\t', '    ')
        input_safe.append(line_safe)
        line_safe_len = len(normalize_str(line_safe))

        if line_safe_len > length:
            length = line_safe_len

    if header_len > length:
        length = header_len

    ret += '+' + '-' * length + '+\n'
    ret += f'|{header.ljust(gen_ljust_width(header, length))}|\n'
    ret += '+' + '-' * length + '+\n'

    for line in input_safe:
        ret += f'|{line.ljust(gen_ljust_width(line, length))}|\n'

    ret += '+' + '-' * length + '+\n'
    
    return ret

def normalize_str(input: str) -> str:
    # remove ANSI color codes / escape sequences
    return re.sub(r'\x1b[^m]*m', '', input)

def gen_ljust_width(input: str, length: int) -> int:
    return length + (len(input) - len(normalize_str(input)))