from ebash_lib.bash_core import BashLoop
from ebash_lib.bash_parser import BashParser


def test_basics():
    loop = BashLoop(BashParser, {"aaa": "bbb"}, "")
    assert loop.run_lexer("a b c") == ["a", "b", "c"]
    assert loop.run_lexer("a 'b c d' e") == ["a", "b c d", "e"]
    assert loop.run_lexer("   a   b c   d  ") == ["a", "b", "c", "d"]
    assert loop.run_lexer("a \"b '''c d\" e") == ["a", "b '''c d", "e"]


def test_env_vars():
    loop = BashLoop(BashParser, {"aaa": "bbb"}, "")
    assert loop.run_lexer("$ccc") == [""]
    assert loop.run_lexer("$aaa") == ["bbb"]
    assert loop.run_lexer("$aaabc") == [""]
    assert loop.run_lexer("1+$aaa=b") == ["1+bbb=b"]
    assert loop.run_lexer("'$aaa'") == ["$aaa"]
    assert loop.run_lexer('"$aaa"') == ["bbb"]


def test_backslash():
    loop = BashLoop(BashParser, {"aaa": "bbb"}, "")

    assert loop.run_lexer("\\a\\b\\c") == ["abc"]
    assert loop.run_lexer("\\$a\\$b\\$c") == ["$a$b$c"]
    assert loop.run_lexer("a\\ b c") == ["a b", "c"]
    assert loop.run_lexer("a\\\\b") == ["a\\b"]
    assert loop.run_lexer("'a\\''") == ["a'"]  # different from Bash behavior, but who cares
    assert loop.run_lexer('"a\\""') == ['a"']
