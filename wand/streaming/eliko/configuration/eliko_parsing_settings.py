from gamevolt.configuration.appsetting import appsetting


@appsetting
class ElikoParsingSettings:
    sample_dt_us: int
    nsamp_per_packet: int
    body_forward_x: float
    body_forward_y: float
    body_forward_z: float
