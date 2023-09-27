def wrap_dash(header: str, stdout: list, stderr: list) -> str:
    ret = ''

    stdout_str = '\n'.join(stdout)
    stderr_str = '\n'.join(stderr)

    input = stdout_str
    if stderr_str:
        input = input + ('\n' if input else '') + stderr_str

    if not input:
        input = ' '

    header_len = len(header) - 11
    input = input.splitlines()
    length = 0
    input_safe = []

    # process each line
    for line in input:
        # replace whitespaceces from the end of the line
        # replace tabs with 4 spaces
        line_safe = line.rstrip().replace('\t', '    ')
        input_safe.append(line_safe)

        if len(line_safe) > length:
            length = len(line_safe)

    if header_len > length:
        length = header_len

    ret += '+' + '-' * length + '+\n'
    ret += f'|{header.ljust(length + 11)}|\n'
    ret += '+' + '-' * length + '+\n'

    for line in input_safe:
        ret += f'|{line.ljust(length)}|\n'

    ret += '+' + '-' * length + '+\n'
    
    return ret