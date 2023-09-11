import sys
import logging
import uuid
import glob
import os
import shlex
from configparser import RawConfigParser, NoSectionError, NoOptionError
from usorchestrator.action import Action
from usorchestrator.remote import Remote
from usorchestrator.action_transfer import ActionTransfer
from usorchestrator.wrap_dash import wrap_dash

__all__ = ['UsOrchestratorManager', 'UsOrchestratorConfigError']

class UsOrchestratorConfigError(Exception):
    pass

class UsOrchestratorManager:
    def __init__(self, params: dict) -> None:
        self._instance_id: str = uuid.uuid4().hex[:12]

        self._logger: logging.Logger = self._gen_logger(params.get('log_file', ''), params.get('log_level', 'INFO'), self._instance_id)

        self._hosts_config: RawConfigParser = self._parse_config('hosts')
        self._routines_config: RawConfigParser = self._parse_config('routines')
        self._tests_config: RawConfigParser = self._parse_config('tests')

    def show(self, show_type: str) -> None:
        if show_type == 'hosts_groups':
            hosts_sections = self._hosts_config.sections()
            print(f'Available host groups: {hosts_sections}')
        elif show_type == 'tests':
            tests_sections = self._tests_config.sections()
            print(f'Available tests: {tests_sections}')
        elif show_type == 'routines':
            routines_sections = self._routines_config.sections()
            print(f'Available routines: {routines_sections}')
        else:
            raise ValueError(f'Unknown show type "{show_type}"')

    def orchestrate(self, params: dict) -> None:
        try:
            self._do_orchestrate(params)
        except KeyboardInterrupt:
            # ignore keyboard intrerupt error
            pass
        except Exception as e:
            # cleanup orchestrator, exit
            self._cleanup()

            print(f'ERROR: {e}')
            self._logger.exception(e, exc_info=True)
            sys.exit(1)
        finally:
            # cleanup orchestrator, exit
            self._cleanup()
            sys.exit(0)
   
    def _do_orchestrate(self, params: dict[any]) -> None:
        hosts: list[Remote] = []
        actions: list[Action] = []
        data: dict = {}

        if params.get('hosts'):
            hosts += self._process_hosts(params['hosts'])
        if params.get('hosts_groups'):
            hosts += self._process_hosts_groups(params['hosts_groups'])

        if params.get('commands'):
            actions += self._process_commands(params['commands'])
        if params.get('routines'):
            actions += self._process_routines(params['routines'])
        if params.get('tests'):
            actions += self._process_tests(params['tests'])
        if params.get('transfers'):
            actions += self._process_transfers(params['transfers'])

        if not hosts:
            print('At least one of the following options for hosts identification must be provided: "--host", "--hosts-group"')
            sys.exit(1)

        if not actions:
            print('At least one of the following options for actions execution must be provided: "--command", "--routine", "--test", "--transfer"')
            sys.exit(1)

        if params.get('data'):
            data = self._parse_data(params['data'])

        self._handle_actions(hosts, actions, data)
        sys.exit(0)

    def _cleanup(self) -> None:
        pass

    def _gen_logger(self, log_file: str, log_level: str, instance_id: str) -> logging.Logger:
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        format:str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        if not log_level in levels:
            log_level = "INFO"

        logger = logging.getLogger()
        logger.setLevel(levels[log_level])

        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()

        handler.setLevel(levels[log_level])
        handler.setFormatter(logging.Formatter(format))

        logger.addHandler(handler)

        # logger = logging.LoggerAdapter(logger, {'instance_id': instance_id})

        return logger

    def _parse_config(self, config_type: str) -> RawConfigParser:
        parser = RawConfigParser(comment_prefixes=None)
        config_files = [
            # search in project directory
            *glob.glob(os.path.dirname(os.path.realpath(__file__)) + f'/../config/{config_type}.d/*.conf'),

            # search in /etc/usorchestrator
            f'/etc/usorchestrator/{config_type}.conf',
            *glob.glob(f'/etc/usorchestrator/{config_type}.d/*.conf'),

            # search in /etc/opt/usorchestrator
            f'/etc/opt/usorchestrator/{config_type}.conf',
            *glob.glob(f'/etc/opt/usorchestrator/{config_type}.d/*.conf'),

            # search in ~/.config/usorchestrator
            os.path.expanduser(f'~/.config/usorchestrator/{config_type}.conf'),
            *glob.glob(os.path.expanduser(f'~/.config/usorchestrator/{config_type}.d/*.conf')),
        ]

        parser.read(config_files)

        # if not parser.sections():
            # raise UsorchestratorConfigError(f'Could not find any "{config_type}" configuration file')

        return parser

    # data is provided as a list formatted in ENV style
    # example: --data "key1=value1" --data "key2=value2"
    def _parse_data(self, data_files: list[str]) -> dict:
        data: dict = {}

        # validate data
        for data_file in data_files:
            # split data into key and value
            try:
                key, value = data_file.split('=', 1)
            except ValueError as e:
                print(f'Invalid data format: {e}')
                self._logger.exception(e, exc_info=True)
                sys.exit(1)

            # validate key
            if not key:
                print(f'Invalid data format: key is empty')
                sys.exit(1)

            data[key] = value

        return data

    # process hosts
    def _process_hosts(self, raw_hosts: list[str]) -> list:
        hosts = []

        for host in raw_hosts:
            hosts.append(Remote(host))

        self._logger.debug(f'Discovered hosts: "{raw_hosts}"')

        return hosts

    # process hosts_groups
    def _process_hosts_groups(self, hosts_groups: list[str]) -> list:
        hosts = []

        for hosts_group in hosts_groups:
            try:
                raw_hosts = shlex.split(self._hosts_config.get(hosts_group, 'hosts', fallback=''))
                for host in raw_hosts:
                    hosts.append(Remote(host))
            except (NoSectionError, NoOptionError) as e:
                print(f'Could not extract hosts: {e}')
                self._logger.exception(e, exc_info=True)
                sys.exit(1)

            self._logger.debug(f'Discovered hosts "{raw_hosts}" from hosts config')

        return hosts

    # process commands
    def _process_commands(self, commands: list[str]) -> list[Action]:
        actions = []

        for command in commands:
            actions.append(self._process_command(command))

        return actions
    
    def _process_command(self, command: str) -> Action:
        action = Action('command', command)
        action.addCommand(command)

        self._logger.debug(f'Discovered "{action.name}" command action')

        return action

    # process routines
    def _process_routines(self, routines: list[str]) -> list[Action]:
        actions = []

        for routine in routines:
            actions.append(self._process_routine(routine))

        return actions

    def _process_routine(self, routine: str) -> Action:
        try:
            if not self._routines_config.has_section(routine):
                raise NoSectionError(routine)

            action = Action('routine', routine)
            action.setSpliceLocalhost(self._routines_config.getboolean(routine, 'splice_localhost', fallback=False))
            action.addCommand(self._routines_config.get(routine, 'command', fallback='').strip())
            action.addTransfer(self._routines_config.get(routine, 'transfer', fallback=''))
            
            # add condition action (only one of iftest, ifroutine, ifcommand option is supported, not multiple)
            if self._routines_config.has_option(routine, 'iftest'):
                iftest_cnf = self._routines_config.get(routine, 'iftest')
                action.setCondition(self._process_test(iftest_cnf))

            if self._routines_config.has_option(routine, 'ifroutine'):
                ifroutine_cnf = self._routines_config.get(routine, 'ifroutine')
                action.setCondition(self._process_routine(ifroutine_cnf))

            if self._routines_config.has_option(routine, 'ifcommand'):
                if_cnf = self._routines_config.get(routine, 'ifcommand')
                action.setCondition(self._process_command(if_cnf))

            # add additional actions
            if self._routines_config.has_option(routine, 'doroutines'):
                doroutines_cnf = shlex.split(self._routines_config.get(routine, 'doroutines', fallback=''))
                for doroutine_cnf in doroutines_cnf:
                    action.addAction(self._process_routine(doroutine_cnf))
        except (NoSectionError, NoOptionError) as e:
            print(f'Could not extract routine: {e}')
            self._logger.exception(e, exc_info=True)
            sys.exit(1)

        log_msg = f'Discovered "{action.name}" routine action with commands "{action.commands}", additional actions "{action.getActionsNames()}", condition "{action.getConditionName()}"'
        self._logger.debug(log_msg)

        return action

    # process tests
    def _process_tests(self, tests: list[str]) -> list[Action]:
        actions = []

        for test in tests:
            actions.append(self._process_test(test))

        return actions
    
    def _process_test(self, test: str) -> Action:
        try:
            if not self._tests_config.has_section(test): raise NoSectionError(test)

            action = Action('test', test)
            action.addCommand(self._tests_config.get(test, 'command', fallback='').strip())
        except (NoSectionError, NoOptionError) as e:
            print(f'Could not extract test: {e}')
            self._logger.exception(e, exc_info=True)
            sys.exit(1)

        self._logger.debug(f'Discovered "{action.name}" test action with commands "{action.commands}"')

        return action

    # process transfers
    def _process_transfers(self, transfers: list[str]) -> list[Action]:
        actions = []

        for transfer in transfers:
            actions.append(self._process_transfer(transfer))

        return actions
    
    def _process_transfer(self, transfer: str) -> Action:
        action = Action('transfer', transfer)
        action.addTransfer(ActionTransfer(transfer))

        self._logger.debug(f'Discovered "{action.name}" transfer action')

        return action

    # handle actions for all hosts
    def _handle_actions(self, hosts: list[Remote], actions: list[Action], data: dict = None) -> None:
        self._logger.debug('Starting processing actions on all hosts')

        spliced_hosts = []

        for host in hosts:
            for action in actions:
                if action.splice_localhost and host.local:
                    spliced_hosts.append(host)
                    continue
                self._handle_action(host, action, data)

        for host in spliced_hosts:
            for action in actions:
                if not host.local: continue
                self._handle_action(host, action, data)

    # handle individual action
    def _handle_action(self, host: Remote, action: Action, data: dict = None) -> None:
        if action.type == 'test':
            log_msg = f'Running "{action.name}" {action.type} for "{host.host}"'
        else:
            log_msg = f'Running "{action.name}" {action.type} on "{host.host}"'

        self._logger.debug(log_msg)
        sys.stdout.write(('* ' + log_msg + ' ...\r'))

        try:
            action_exec = action.runAction(host, data)
        except Exception as e:
            sys.stdout.write('\033[K')
            print(f'ERROR: {e}')
            self._logger.exception(e, exc_info=True)
        else:
            sys.stdout.write('\033[K')

            if action_exec.passed_condition:
                if action.type == 'test':
                    log_msg = f'"{action.name}" {action.type} for "{host.host}"'
                else:
                    log_msg = f'"{action.name}" {action.type} on "{host.host}"'

                header = log_msg
                print(wrap_dash(header, action_exec.stdout, action_exec.stderr))