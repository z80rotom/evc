import logging
import sys

from enum import IntEnum, auto
from dataclasses import dataclass

from evcListener import evcListener
from evcParser import evcParser



MAX_WORK = 500
MAX_FLAG = 4000
MAX_SYS_FLAG = 1000

class ECommandArgType(IntEnum):
    Flag = auto()
    SysFlag = auto()
    Integer = auto()
    Float = auto()
    Boolean = auto()
    String = auto()
    NumberEnum = auto()

@dataclass
class CommandDefArgument:
    eArgType: ECommandArgType
    argTypeIdentifier: str
    identifier: str
    storage: int
    line: int
    column: int

@dataclass
class Command:
    identifier: str
    storage: int
    retArg: CommandDefArgument
    args: list[CommandDefArgument]
    line: int
    column: int

class evcCompiler(evcListener):
    def __init__(self, ifpath):
        self.src_ifpath = ifpath
        self.now_src_ifpath = ifpath
        self.logger = logging.getLogger(__name__)
        self.commands = {}
    
    def parseNumberContext(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return float(ctx.NUMBER().getText())

    def parseNumberContextInt(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return int(ctx.NUMBER().getText())

    def parseType(self, argType:evcParser.Type):
        argTypes = {
            "flag" : ECommandArgType.Flag,
            "sysflag" : ECommandArgType.SysFlag,
            "int" : ECommandArgType.Integer,
            "float" : ECommandArgType.Float,
            "bool" : ECommandArgType.Boolean,
            "str" : ECommandArgType.String
        }
        eArgType = argTypes[argType.getText()]
        return eArgType

    def parseFuncArgList(self, ctx:evcParser.FuncArgListContext):
        args = []
        for funcArgCtx in ctx.funcArg():
            identifier = funcArgCtx.Identifier().getText()
            storage = self.parseNumberContextInt(funcArgCtx.number())
            eArgType = self.parseType(funcArgCtx.Type())
            argTypeIdentifier = funcArgCtx.Type().getText()

            # TODO: Validate storage based on type

            args.append(CommandDefArgument(
                eArgType,
                argTypeIdentifier,
                identifier,
                storage,
                funcArgCtx.start.line,
                funcArgCtx.start.column
            ))
        return args

    def parseRetFuncArg(self, ctx:evcParser.RetFuncArgContext):
        eArgType = self.parseType(ctx.Type())
        argTypeIdentifier = ctx.Type().getText()
        retArg = CommandDefArgument(
            eArgType,
            argTypeIdentifier,
            None,
            None,
            ctx.start.line,
            ctx.start.line
        )
        return retArg

    def enterCommand(self, ctx:evcParser.CommandContext):
        # print("COMMAND defined: ", ctx.getText())
        # print("COMMAND defined: ", ctx.Identifier().getText())
        if ctx.Identifier() is None:
            # Error. Invalid name for command.
            self.logger.error("Invalid name for command at: {}:{}:{}".format(self.now_src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None

        storage = self.parseNumberContextInt(ctx.number())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())

        if ctx.retFuncArg() is not None:
            retArg = self.parseRetFuncArg(ctx.retFuncArg())

        self.commands[identifier] = Command(
            identifier,
            storage,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        )
