from gamevolt.configuration.appsetting import appsetting


@appsetting
class SessionRecorderSettings:
    """Where and how recorded sessions are written.

    `output_dir` may be relative (resolved against the runtime root) or absolute.
    Each record toggle creates `<output_dir>/<timestamp>_<name>/`.
    """

    is_enabled: bool
    output_dir: str
    save_images: bool
    image_width: int
    image_height: int
