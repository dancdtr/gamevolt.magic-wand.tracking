from __future__ import annotations

import logging

from ._levels import PACKET, TRACE, VERBOSE


class Logger(logging.Logger):
    def verbose(self, msg: object, *args: object, **kwargs: object) -> None:
        if self.isEnabledFor(VERBOSE):
            stacklevel = int(kwargs.pop("stacklevel", 1))
            self._log(VERBOSE, msg, args, stacklevel=stacklevel + 1, **kwargs)

    def trace(self, msg: object, *args: object, **kwargs: object) -> None:
        if self.isEnabledFor(TRACE):
            stacklevel = int(kwargs.pop("stacklevel", 1))
            self._log(TRACE, msg, args, stacklevel=stacklevel + 1, **kwargs)

    def packet(self, msg: object, *args: object, **kwargs: object) -> None:
        if self.isEnabledFor(TRACE):
            stacklevel = int(kwargs.pop("stacklevel", 1))
            self._log(PACKET, msg, args, stacklevel=stacklevel + 1, **kwargs)

    @property
    def is_enabled_for_trace(self) -> bool:
        return self.isEnabledFor(TRACE)
