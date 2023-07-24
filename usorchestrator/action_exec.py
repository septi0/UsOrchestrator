class ActionExec:
    def __init__(self, **data) -> None:
        self._passed_condition: bool = data.get('passed_condition', True)
        self._stdout: str = data.get('stdout', '')
        self._stderr: str = data.get('stderr', '')
        self._return_code: int = data.get('return_code', 0)

    @property
    def passed_condition(self) -> bool:
        return self._passed_condition
    
    @property
    def stdout(self) -> str:
        return self._stdout
    
    @property
    def stderr(self) -> str:
        return self._stderr
    
    @property
    def return_code(self) -> int:
        return self._return_code