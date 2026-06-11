from gamevolt.configuration.appsetting import appsetting


@appsetting
class ElikoConnectionSettings:
    host: str
    port: int
    reconnect_delay_s: float
    report_type: str
