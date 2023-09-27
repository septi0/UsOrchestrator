class ActionExec:
    def __init__(self, **data) -> None:
        self._stdout: list = data.get('stdout', [])
        self._stderr: list = data.get('stderr', [])
        self._return_code: int = data.get('return_code', 0)
        self._passed_condition: bool = data.get('passed_condition', True)
    
    @property
    def stdout(self) -> list:
        return self._stdout
    
    @property
    def stderr(self) -> list:
        return self._stderr
    
    @property
    def return_code(self) -> int:
        return self._return_code
    
    @property
    def passed_condition(self) -> bool:
        return self._passed_condition
    
    def update(self, **data) -> None:
        self._stdout = data.get('stdout', self._stdout)
        self._stderr = data.get('stderr', self._stderr)
        self._return_code = data.get('return_code', self._return_code)
        self._passed_condition = data.get('passed_condition', self._passed_condition)