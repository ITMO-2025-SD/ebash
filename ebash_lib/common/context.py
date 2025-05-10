import dataclasses


@dataclasses.dataclass(frozen=True)
class Context:
    return_code: int
    stdout: list[str]
