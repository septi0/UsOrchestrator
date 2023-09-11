import uuid
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
        self._commands: list[str] = []
        self._condition: Action = data.get('condition', None)
        self._actions: list[Action] = []
        self._transfers: list[ActionTransfer] = []
        self._placeholders: dict = []

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
    def commands(self) -> list[str]:
        return self._commands

    def setSpliceLocalhost(self, splice_localhost:bool) -> None:
        self._splice_localhost = splice_localhost

    def addCommand(self, command:str) -> None:
        self._commands.append(command)

    def setCondition(self, condition:'Action') -> None:
        self._condition = condition

    def addAction(self, action:'Action') -> None:
        self._actions.append(action)

    def addTransfer(self, transfer:ActionTransfer) -> None:
        self._transfers.append(transfer)

    def setPlaceholders(self, placeholders:dict) -> None:
        self._placeholders = placeholders

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
            for command in self._commands:
                if not command:
                    continue

                cmd_data = {
                    'host': host.host,
                    'user': host.user,
                    'port': host.port
                }

                if data:
                    cmd_data.update(data)

                if self._placeholders:
                    # check if data keys are in placeholders
                    for placeholder in self._placeholders:
                        if placeholder not in cmd_data.keys():
                            raise ActionError(f'Placeholder "{placeholder}" must be provided')

                # make sure that placeholders are replaced

                command = self._formatCommand(command, cmd_data)

                if self.type == 'test':
                    output = remote_cmd('ssh-bash', (command,), True)
                else:
                    output = remote_cmd('ssh-bash', (command,), host.local, host.host, host.user, host.port, host.password)

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
                    output['stdout'] = 'Transfer ok'
                else:
                    output['stderr'] = 'Transfer failed: ' + output['stderr']

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
    
    def _formatCommand(self, command:str, placeholders:dict) -> str:
        # placeholder format is {{PLACEHOLDER:variablename}}
        for placeholder in placeholders.keys():
            command = command.replace('{{PLACEHOLDER:' + placeholder + '}}', str(placeholders[placeholder]))

        return command