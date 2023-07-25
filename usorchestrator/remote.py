import socket
import re

__all__ = ['Remote']

"""
Allwed host formats:
    - hostname
    - username@hostname
    - username@hostname:port
    - username@hostname:port/password
    - username@hostname/password
    - hostname:port
    - hostname:port/password
    - hostname/password

Note: Using the password is not recommended, as it will be visible in the process list.
"""

class Remote:
    def __init__(self, remote: str) -> None:
        self._host: str = None
        self._user: str
        self._port: int
        self._password: str
        self._local: bool
   
        pattern = r'^(?:(?P<username>[^@]+)@)?(?P<hostname>[^:/]+)(?::(?P<port>\d+))?(?:/(?P<password>.+))?$'

        match = re.match(pattern, remote)

        if not match:
            raise ValueError('Invalid remote string')

        self._host = match.group('hostname')
        self._user = match.group('username') or 'root'
        self._port = match.group('port') or 22
        self._password = match.group('password') or ''

        self._local = True if (self._host == socket.gethostname() or self._host == 'localhost') else False
    
    @property
    def host(self) -> str:
        return self._host
    
    @property
    def user(self) -> str:
        return self._user
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def password(self) -> str:
        return self._password
    
    @property
    def local(self) -> bool:
        return self._local
    
    def __str__(self) -> str:
        return f"{self._user}@{self._host}"

    def __bool__(self) -> bool:
        return self._host is not None
