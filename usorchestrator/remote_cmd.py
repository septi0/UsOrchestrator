import subprocess
import shlex
from usorchestrator.exceptions import RemoteCmdError

def remote_cmd(protocol: str, action: tuple[str], local:bool, host:str = '', user:str = 'root', port:int = 22, password: str = None) -> dict:
    remote_cmd_prefix = []
    ssh_opts = []

    if password:
        remote_cmd_prefix += ['sshpass', '-p', password]
    else:
        ssh_opts += ['-o', 'PasswordAuthentication=No', '-o', 'BatchMode=yes']

    if protocol == 'ssh-bash':
        bash_command = ['bash', '-c', action[0]]
        bash_command_quoted = ' '.join(shlex.quote(c) for c in bash_command)
        
        if local:
            # run given command locally
            command_to_run = bash_command
        else:
            # run given commands with ssh
            command_to_run = [*remote_cmd_prefix, 'ssh', f'{user}@{host}', '-p', str(port), *ssh_opts, bash_command_quoted]
    elif protocol == 'scp':
        src, dest = action
        if local:
            # run given command locally
            command_to_run = ['cp', '-a', src, dest]
        else:
            # run given commands with ssh
            command_to_run = [*remote_cmd_prefix, 'scp', '-P', str(port), *ssh_opts, '-r', src, f'{user}@{host}:{dest}']
    else:
        raise RemoteCmdError('Unknown protocol provided')

    cmd = subprocess.run(command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ret = {
        'stdout': cmd.stdout.decode('utf-8').strip(),
        'stderr': cmd.stderr.decode('utf-8').strip(),
        'return_code': cmd.returncode
    }

    return ret