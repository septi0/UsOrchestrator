import uuid
import shlex
import re
from usorchestrator.remote import Remote
from usorchestrator.action_transfer import ActionTransfer
from usorchestrator.action_exec import ActionExec
from usorchestrator.remote_cmd import remote_cmd
from usorchestrator.exceptions import ActionError

class Action:
    def __init__(self, action_type:str, action_name:str, **data) -> None:
        self.id: str = uuid.uuid4().hex[:12]

        self._type: str = action_type
        self._name: str = action_name

        self._splice_localhost: bool = data.get('splice_localhost', False)
        self._exec_mode: str = data.get('exec_mode', 'remote')
        self._commands: list[str] = []
        self._condition: Action = data.get('condition', None)
        self._actions: list[Action] = []
        self._transfers: list[ActionTransfer] = []
        self._data_definition: dict = {}
        self._requirements: list = []

        command = data.get('command')
        action = data.get('action')
        transfer = data.get('transfer')

        if command and type(command) == str: self.addCommand(command)
        if action and type(action) == Action: self.addAction(action)
        if transfer and type(transfer) == ActionTransfer: self.addTransfer(transfer)

    @property
    def type(self) -> str:
        return self._type
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def splice_localhost(self) -> bool:
        return self._splice_localhost
    
    @property
    def exec_mode(self) -> str:
        return self._exec_mode
    
    @property
    def commands(self) -> list[str]:
        return self._commands
    
    @property
    def condition(self) -> 'Action':
        return self._condition
    
    @property
    def actions(self) -> list['Action']:
        return self._actions
    
    @property
    def transfers(self) -> list['ActionTransfer']:
        return self._transfers

    def setSpliceLocalhost(self, splice_localhost:bool) -> None:
        self._splice_localhost = splice_localhost

    def setExecMode(self, exec_mode:str) -> None:
        self._exec_mode = exec_mode

    def addCommand(self, command:str) -> None:
        self._commands.append(command)

    def setCondition(self, condition:'Action') -> None:
        self._condition = condition

    def addAction(self, action:'Action') -> None:
        self._actions.append(action)

    def addTransfer(self, transfer:ActionTransfer) -> None:
        self._transfers.append(transfer)

    def setDataDefinition(self, data:dict) -> None:
        self._data_definition = data

    def setRequirements(self, requirements: list) -> None:
        self._requirements = requirements

    def getActionsNames(self) -> list:
        return [action.name for action in self._actions]

    def getConditionName(self) -> str:
        if self._condition:
            return self._condition.name

        return ''

    def runAction(self, host: Remote, data: dict = None) -> ActionExec:
        # agregator action
        if self._condition:
            condition_runned_action = self._condition.runAction(host, data)

            if not condition_runned_action.passed_condition or condition_runned_action.return_code != 0:
                condition_runned_action.update(passed_condition=False)
                return condition_runned_action

        stdout: list = []
        stderr: list = []

        # end leaf action
        if self._commands:
            for cmd in self._commands:
                if not cmd:
                    continue

                cmd_variables = self._define_cmd_variables(host, data)
                cmd_parts = self._init_cmd(cmd_variables)
                
                cmd_parts.append(cmd)
                cmd_to_exec = '\n'.join(cmd_parts)

                if self._exec_mode == 'local':
                    output = remote_cmd('ssh-bash', (cmd_to_exec,), True)
                elif self._exec_mode == 'remote':
                    output = remote_cmd('ssh-bash', (cmd_to_exec,), host.local, host.host, host.user, host.port, host.password)
                else:
                    raise ActionError(f'Unknown exec mode "{self._exec_mode}"')

                stdout.append(output['stdout'])
                stderr.append(output['stderr'])

                if output['return_code'] != 0:
                    return ActionExec(stdout=stdout, stderr=stderr, return_code=output['return_code'])

        # end leaf action
        if self._transfers:
            for transfer in self._transfers:
                if not transfer:
                    continue
                
                output = remote_cmd('scp', (transfer.src, transfer.dst), host.local, host.host, host.user, host.port, host.password)
                # output overwrites
                if output['return_code'] == 0:
                    output['stdout'] = 'Transfer completed' + (':\n' + output['stdout'] if output['stdout'] else '')
                else:
                    output['stderr'] = 'Transfer failed' + (':\n' + output['stderr'] if output['stderr'] else '')

                stdout.append(output['stdout'])
                stderr.append(output['stderr'])

                if output['return_code'] != 0:
                    return ActionExec(stdout=stdout, stderr=stderr, return_code=output['return_code'])

        # agregator action
        if self._actions:
            for action in self._actions:
                if not action:
                    continue

                runned_action = action.runAction(host, data)

                if not runned_action.passed_condition or runned_action.return_code != 0:
                    return runned_action
                
                stdout += runned_action.stdout
                stderr += runned_action.stderr

        return ActionExec(stdout=stdout, stderr=stderr, return_code=0)
    
    def _define_cmd_variables(self, host: Remote, data: dict) -> dict:
        default_variables = {
            'target_host': host.host,
            'target_user': host.user,
            'target_port': host.port
        }

        if not self._data_definition:
            return default_variables
        
        cmd_variables = {**default_variables}
        
        for (name, default_value) in self._data_definition.items():
            if data.get(name):
                cmd_variables[name] = data[name]
            elif default_value:
                cmd_variables[name] = default_value
            else:
                raise ActionError(f'Variable "{name}" value must be provided')

        return cmd_variables

    def _init_cmd(self, variables: dict) -> list:
        cmd_parts = []

        cmd_parts.append('set -e')

        # add check for required programs
        if self._requirements:
            for requirement in self._requirements:
                require_safe = shlex.quote(requirement)
                cmd_parts.append(f'command -v {require_safe} > /dev/null 2>&1 || {{ echo >&2 "Required command \\"{require_safe}\\" not found"; exit 999; }}')

        # add variables
        if variables:
            for (name, value) in variables.items():
                if not self._valid_bash_variable_name(name):
                    raise ActionError(f'Variable "{name}" is not a valid bash variable name')
                
                value = str(value)
                
                safe_value = shlex.quote(value)

                # make sure that value is quoted
                if value == safe_value:
                    safe_value = f"'{safe_value}'"

                cmd_parts.append(f'{name}={safe_value}')

        return cmd_parts
    
    def _valid_bash_variable_name(self, name: str) -> bool:
        if not name:
            return False

        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None