import re
from typing import Literal, final

from ebash_lib.common.command import MetaCommand
from ebash_lib.common.context import Context
from ebash_lib.common.parser import Parser


@final
class BashLoop:
    env_var_regex = re.compile(r"\$([a-zA-Z_]+)")

    def __init__(self, parser: Parser[MetaCommand], environ: dict[str, str], cwd: str) -> None:
        self.parser = parser
        self.environ = environ
        self.cwd: str = cwd

    def load_environ(self, quote_type: Literal[None, '"', "'"], token: str):
        if quote_type == "'":  # strong quoting
            return token

        return self.env_var_regex.sub(lambda m: self.environ.get(m.group(1), ""), token).replace("|$|", "$")

    def run_lexer(self, line: str) -> list[str] | None:
        current_quote: Literal[None, '"', "'"] = None
        current_word: list[str] = []
        current_tokens: list[str] = []
        is_backslash: bool = False
        for char in line:
            if is_backslash:
                # Yeah, this is not ideal as there are corner cases if the actual text has |$|, ik that
                current_word.append(char if char != "$" else "|$|")
                is_backslash = False
            elif char == "\\":
                is_backslash = True
            elif current_quote is None and char in ("'", '"'):
                current_quote = char
            elif current_quote == char or (current_quote is None and char in "\n\t "):
                if current_word:
                    current_tokens.append(self.load_environ(current_quote, "".join(current_word)))
                current_word = []
                current_quote = None
            else:
                current_word.append(char)

        if current_quote is not None or is_backslash:
            return None
        if current_word:
            current_tokens.append(self.load_environ(current_quote, "".join(current_word)))

        return current_tokens

    def run_once(self, line: str) -> list[str]:
        if line == '\x18': # Введен Ctrl+X
            tokens = self.run_lexer("exit")
        else:
            tokens = self.run_lexer(line)
        if tokens is None:
            return ["Unmatched quotes"]
        command = self.parser.parse(tokens)
        if not command:
            return ["Syntax error"]
        new_context = command(Context(0, self.cwd, self.environ, [], []))
        output: list[str] = []
        if new_context.return_code:
            output.append(f"Error code {new_context.return_code}")
        if new_context.stderr:
            output.append("=== Error messages ===\n" + "\n".join(new_context.stderr) + "\n" + "=" * (6 + 5 + 8 + 3))
        self.cwd = new_context.workdir
        self.environ = new_context.environ
        output.append("\n".join(new_context.stdout))
        return output

    def run(self):
        while True:
            print("\n".join(self.run_once(input(f"[{self.cwd}]> "))))
