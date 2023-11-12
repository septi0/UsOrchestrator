import sys
from usorchestrator.action import Action
from usorchestrator.action_exec import ActionExec
from usorchestrator.remote import Remote

class ActionOutput:
    def __init__(self, action: Action, host: Remote) -> None:
        self._action: Action = action
        self._host: Remote = host

        self._header_str: str = f'"{self._action.name}" {self._action.type} for "{self._host.host}"'

    def print_temp_info(self):
        sys.stdout.write((f'● Running {self._header_str} ...\r'))

    def reset_temp_info(self):
        sys.stdout.write('\033[K')

    def print_info(self, action_exec: ActionExec):
        # colorize header marker
        if action_exec.return_code == 0:
            header_marker = '\033[0;32m' + '●' + '\033[0m'
        else:
            if not action_exec.passed_condition:
                header_marker = '\033[0;33m' + '●' + '\033[0m'
            else:
                header_marker = '\033[0;31m' + '●' + '\033[0m'
        
        header = self._header_str
        (stdout, stderr) = self._get_action_output(action_exec)

        header_marker_len = 2
        header_len = len(header) + header_marker_len
        length = header_len

        # transform output and search for the longest line
        for i, line in enumerate(stdout):
            stdout[i] = self.normalize_output_line(line)
            length = max(length, len(stdout[i]))

        for i, line in enumerate(stderr):
            stderr[i] = self.normalize_output_line(line)
            length = max(length, len(stderr[i]))

        # generate print output
        output_print = '+' + '-' * length + '+\n'
        output_print += f'|{header_marker} {header.ljust(length - header_marker_len)}|\n'
        output_print += '+' + '-' * length + '+\n'

        for line in stdout:
            output_print += f'|{line.ljust(length)}|\n'

        for line in stderr:
            # colorize stderr
            output_print += f'|\033[0;31m{line.ljust(length)}\033[0m|\n'

        output_print += '+' + '-' * length + '+\n'
        
        sys.stdout.write(output_print)

    def _get_action_output(self, action_exec: ActionExec) -> tuple:
        # filter empty lines
        stdout = list(filter(None, action_exec.stdout))
        stderr = list(filter(None, action_exec.stderr))

        # add return code for output
        if action_exec.passed_condition:
            if not stdout and not stderr:
                stdout = [f'Return code {action_exec.return_code}']
        else:
            stdout = [f'Skipped. Condition not met (Return code {action_exec.return_code})', *stdout]

        # make sure every new line is a new list item
        stdout = '\n'.join(stdout).splitlines()
        stderr = '\n'.join(stderr).splitlines()

        return (stdout, stderr)
    
    def normalize_output_line(self, line: str) -> str:
        # replace whitespaceces from the end of the line
        # replace tabs with 4 spaces
        line = line.rstrip().replace('\t', '    ')

        return line