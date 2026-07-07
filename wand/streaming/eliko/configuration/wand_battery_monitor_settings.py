from gamevolt.configuration.appsetting import appsetting


@appsetting
class WandBatteryMonitorSettings:
    enabled: bool = False
    # How often to poll each tracked wand. Each poll is an OTA command (one
    # STORED ack + one AC,123 delivery notice per wand), so keep this coarse.
    poll_interval_s: float = 60.0
    # OTA delivery timeout for the GDHR poll ("timeout_ms=" parameter).
    timeout_ms: int = 2000
    # Linear voltage→percent mapping bounds for the AAAA alkaline cell.
    # Rough by design — alkaline sag/recovery makes anything finer illusory.
    full_millivolts: int = 1550
    empty_millivolts: int = 1100
    # Daily CSV of readings (battery_YYYYMMDD.csv) for plotting discharge over time.
    log_directory: str = "./diagnostics/battery"
