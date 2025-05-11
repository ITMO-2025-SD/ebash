import dataclasses


@dataclasses.dataclass(frozen=True)
class Context:
    return_code: int
    workdir: str
    environ: dict[str, str]
    stdout: list[str]
    stderr: list[str]

    # Mutation methods.
    def with_error(self, error_code: int, error_message: str):
        return Context(error_code, self.workdir, self.environ, [], self.stderr + [error_message])

    def with_environ(self, key: str, value: str):
        new_environ = dict(self.environ)
        new_environ[key] = value
        return Context(self.return_code, self.workdir, new_environ, self.stdout, self.stderr)

    def with_stdout(self, data: list[str]):
        return Context(self.return_code, self.workdir, self.environ, data, self.stderr)
