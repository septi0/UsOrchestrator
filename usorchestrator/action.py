import uuid
from usorchestrator.remote import Remote
from usorchestrator.action_transfer import ActionTransfer
from usorchestrator.action_exec import ActionExec
from usorchestrator.remote_cmd import remote_cmd
from usorchestrator.exceptions import ActionError

class Action:
    def __init__(self, action_type:str, action_name:str, **data) -> None:
        self.id: str = uuid.uuid4().hex[:12]

        self.type: str = action_type
        self.name: str = action_name

        self.splice_localhost: bool = data.get('splice_localhost', False)
        self.commands: list[str] = []
        self.condition: Action = data.get('condition', None)
        self.actions: list[Action] = []
        self.transfers: list[ActionTransfer] = []

        command = data.get('command')
        action = data.get('action')
        transfer = data.get('transfer')

        if command and type(command) == str: self.addCommand(command)
        if action and type(action) == Action: self.addAction(action)
        if transfer and type(transfer) == ActionTransfer: self.addTransfer(transfer)

    def setSpliceLocalhost(self, splice_localhost:bool) -> None:
        self.splice_localhost = splice_localhost

    def addCommand(self, command:str) -> None:
        self.commands.append(command)

    def setCondition(self, condition:'Action') -> None:
        self.condition = condition

    def addAction(self, action:'Action') -> None:
        self.actions.append(action)

    def addTransfer(self, transfer:ActionTransfer) -> None:
        self.transfers.append(transfer)

    def getActionsNames(self) -> list:
        return [action.name for action in self.actions]

    def getConditionName(self) -> str:
        if self.condition: return self.condition.name

        return ''

    def runAction(self, host: Remote, data: dict = None) -> ActionExec:
        if self.condition:
            condition_runned_action = self.condition.runAction(host, data)
            if not condition_runned_action.passed_condition or condition_runned_action.return_code != 0:
                return ActionExec(passed_condition=False)

        runned_actions = []

        if self.actions:
            for action in self.actions:
                if not action:
                    continue
                
                runned_actions.append(action.runAction(host, data))

        if self.transfers:
            for transfer in self.transfers:
                if not transfer:
                    continue
                
                output = remote_cmd('scp', (transfer.src, transfer.dst), host.local, host.host, host.user, host.port, host.password)
                # output overwrites
                if output['return_code'] == 0: output['stdout'] = 'Transfer ok'
                else: output['stderr'] = 'Transfer failed: ' + output['stderr']

                runned_actions.append(ActionExec(passed_condition=True, stdout=output['stdout'], stderr=output['stderr'], return_code=output['return_code']))

        if self.commands:
            for command in self.commands:
                if not command:
                    continue

                cmd_data = {
                    'host': host.host,
                    'user': host.user,
                    'port': host.port
                    }

                if data:
                    cmd_data.update(data)

                command = self._formatCommand(command, cmd_data)

                # if placeholders left, raise error
                if self._hasPlaceholders(command):
                    raise ActionError(f'Placeholders left. Not all data was provided for action "{self.name}" {self.type}')

                if self.type == 'test':
                    output = remote_cmd('ssh-bash', (command,), True)
                else:
                    output = remote_cmd('ssh-bash', (command,), host.local, host.host, host.user, host.port, host.password)

                runned_actions.append(ActionExec(passed_condition=True, stdout=output['stdout'], stderr=output['stderr'], return_code=output['return_code']))

        if not runned_actions: raise ActionError(f'No action attached to "{self.name}" {self.type}')

        return runned_actions[-1]

    def _hasPlaceholders(self, command:str) -> bool:
        if '{{PLACEHOLDER:' in command: return True

        return False
    
    def _formatCommand(self, command:str, placeholders:dict) -> str:
        # placeholder format is {{PLACEHOLDER:variablename}}
        for placeholder in placeholders.keys():
            command = command.replace('{{PLACEHOLDER:' + placeholder + '}}', placeholders[placeholder])

        return command