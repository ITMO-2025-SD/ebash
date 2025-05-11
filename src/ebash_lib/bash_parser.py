from ebash_lib.common.command import CommandRunner, MetaCommand, Pipe, SetEnv, SetEnvData
from ebash_lib.common.parser import PrefixParser, SimpleParser, SplittingParser

BashParser = (
    SimpleParser[MetaCommand](CommandRunner)
    .chain(PrefixParser, SetEnv, SetEnvData.parse)
    .chain(SplittingParser, Pipe, "|")
)
