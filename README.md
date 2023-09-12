# UsOrchestrator

## Description

UsOrchestrator is a tool for orchestrating actions (run commands, transfer files, test states) on multiple remote hosts automatically. It is designed to be used in a multi-host environment, where you have to execute the same actions on multiple hosts. It can be used as a standalone script or as a package.
Commands and/or transfers can be organized into routines for easier execution, as well as tests for checking the state of the remote hosts.
Hosts can also be organized into groups for easier orchestration.

## Features

- Execute commands on remote hosts
- Transfer files to remote hosts
- Execute tests on remote hosts
- Organize hosts into groups
- Organize commands and/or transfers into routines
- Configuration file support
- Logging
- Built-in routines and tests

## Software requirements

- python3
- ssh
- sshpass (if using passwords for remote hosts - not recommended)

## Installation

#### 1. As a package

```
pip install --upgrade <git-repo>
```

or 

```
git clone <git-repo>
cd <git-repo>
python setup.py install
```

#### 2. As a standalone script

```
git clone <git-repo>
```

## Usage

USorchestrator can be used in 3 ways:

#### 1. As a package globally

```
/usr/bin/usorchestrator <parameters>
```

#### 2. As a package in a virtualenv

```
<path-to-venv>/bin/usorchestrator <parameters>
```

#### 3. As a standalone script

```
<git-clone-dir>/run.py <parameters>
```

Check "Command line arguments" section for more information about the available parameters.

## Command line arguments

```
usorchestrator [-h] [--log LOG_FILE] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] {show,orchestrate} ...

options:
  -h, --help            show this help message and exit
  --log LOG_FILE        Log file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Log level
  --version             show program's version number and exit

Commands:
  {show,orchestrate}
    show                Show informations regarding different action types
      options:
        -h, --help            show this help message and exit
        --type {hosts_groups,tests,routines}
                              Show informations regarding different action types
    orchestrate         Orchestrate actions
      options:
        -h, --help            show this help message and exit
        --host HOSTS          Target host
        --hosts-group HOSTS_GROUPS
                              Target hosts group
        --command COMMANDS    Command to be executed on target hosts
        --routine ROUTINES    Routine to be executed on target hosts
        --test TESTS          Test to be executed against target hosts
        --transfer TRANSFERS  Transfer to be executed on target hosts (<local-path>:<remote-path>)
```

## Configuration files
For sample configuration files see `hosts.sample.conf` and `routines.sample.conf`. Aditionally, you can copy theese files to `/etc/usorchestrator/`, `/etc/opt/usorchestrator/` or `~/.config/usorchestrator/` and adjust the values to your needs.

#### Configuring hosts (hosts.conf)
Hosts can be configured in the configuration file or passed as command line arguments. If both are used, hosts will be merged.

Each section in the configuration file is a host group. The name of the section is the name of the host group that will be specified with the `--hosts-group` argument.

Section properties:
- `hosts` - List of hosts in the group separated by space

Valid format for hosts:

```
<user>@<host>:<port>/<password>
```

With all the fields except `host` being optional.
If no user is specified, the `root` user will be used. If no port is specified, the default port `22` will be used. If no password is specified, ssh keys will be used for authentication.

**Note!** Using passwords is not recommended as they will be stored as plain text in the configuration file, instead use ssh keys for authentication.

#### Configuring routines (routines.conf)
Each section in the configuration file is a routine. The name of the section is the name of the routine that will be specified with the `--routine` argument.

Section properties:
- `command` - Commands to be executed on the remote hosts
- `transfer` - Files to be transferred to the remote hosts
- `splice_localhost` - If set to `True`, the commands and transfers on localhost will be executed last
- `iftest` - Test that needs to be passed in order for the routine to be executed
- `ifroutine` - Routine that needs to be executed in order for the routine to be executed
- `ifcommand` - Command that needs to be executed in order for the routine to be executed
- `doroutines` - Execute another routine(s)
- `variables` - Variables that can be used in commands

For commands / routines used in conjunction with `if` type properties, they must return status `0` in order for the routine to be executed.

**Note!** Only one of `iftest`, `ifroutine`, `ifcommand` option is supported. If more than one is specified, the order of precedence is `ifcommand`, `ifroutine`, `iftest`.

Valid format for transfer:

```
<local-path>:<remote-path>
```

#### Configuring tests
Each section in the configuration file is a test. The name of the section is the name of the test that will be specified with the `--test` argument.

Section properties:
- `command` - Command to be executed against the remote hosts (e.g. `ping`, `nc`, `curl`)

The command must return status `0` in order for the test to pass.

Available default variables:
- `{target_host}` - Host on which the test is executed
- `{target_user}` - User defined in the configuration file
- `{target_port}` - Port defined in the configuration file

## Disclaimer

Due to the nature of the software, commands are being executed by python using `bash` shell. This can be dangerous if not used properly. Please use with caution and make sure you tested the commands before using them in production.

This software is provided as is, without any warranty. Use at your own risk. The author is not responsible for any damage caused by this software.

## License

This software is licensed under the GNU GPL v3 license. See the LICENSE file for more information.