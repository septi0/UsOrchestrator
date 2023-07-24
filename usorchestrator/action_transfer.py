import re

class ActionTransfer:
    def __init__(self, transfer: str) -> None:
        self._transfer = transfer
        self._src, self._dst = re.split(r'(?<!\\):', transfer, 1)

    @property
    def src(self) -> str:
        return self._src
    
    @property
    def dst(self) -> str:
        return self._dst