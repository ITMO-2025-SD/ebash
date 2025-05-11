import dataclasses


@dataclasses.dataclass(frozen=True)
class Context:
    return_code: int
    workdir: str
    stdout: list[str]
    stderr: list[str]

    def with_error(self, error_code: int, error_message: str):
        return Context(error_code, self.workdir, [], self.stderr + [error_message])
