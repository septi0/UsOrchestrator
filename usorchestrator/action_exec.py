class ActionExec:
    def __init__(self, **data) -> None:
        self._passed_condition: bool = data.get('passed_condition', True)
        self._stdout: list = data.get('stdout', [])
        self._stderr: list = data.get('stderr', [])
        self._return_code: int = data.get('return_code', 0)

    @property
    def passed_condition(self) -> bool:
        return self._passed_condition
    
    @property
    def stdout(self) -> list:
        return self._stdout
    
    @property
    def stderr(self) -> list:
        return self._stderr
    
    @property
    def return_code(self) -> int:
        return self._return_code
    
    def update(self, **data) -> None:
        self._passed_condition = data.get('passed_condition', self._passed_condition)
        self._stdout = data.get('stdout', self._stdout)
        self._stderr = data.get('stderr', self._stderr)
        self._return_code = data.get('return_code', self._return_code)