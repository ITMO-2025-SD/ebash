from ebash_lib.common.command import CommandRunner, Pipe, SetEnv, SetEnvData
from ebash_lib.common.parser import PrefixParser, SimpleParser, SplittingParser

BashParser = (
    SimpleParser(CommandRunner)
    .chain(PrefixParser[SetEnvData], SetEnv, SetEnvData.parse)
    .chain(SplittingParser, Pipe, "|")
)
