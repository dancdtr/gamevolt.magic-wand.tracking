class AppsettingsError(Exception):
    def __init__(self, message: str, path: str | None = None):
        super().__init__(f"[{path}] {message}" if path is not None else message)
        self.path = path


AppsettingsError.__module__ = "builtins"
