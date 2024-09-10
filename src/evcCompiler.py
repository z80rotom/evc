import logging
import struct
import sys

from enum import IntEnum, auto
from dataclasses import dataclass

from evcListener import evcListener
from evcParser import evcParser

from ev_argtype import EvArgType
from ev_cmd import EvCmdType
from ev_work import EvWork
# Not sure what I would use these for directly myself at the moment.
# from ev_flag import EvFlag
# from ev_sys_flag import EvSysFlag


MAX_WORK = 500
MAX_FLAG = 4000
MAX_SYS_FLAG = 1000
RETURN_STORAGE = -1

class ECommandArgType(IntEnum):
    Flag = auto()
    SysFlag = auto()
    Integer = auto()
    Float = auto()
    Boolean = auto()
    String = auto()
    NumberEnum = auto()

class EFunctionSpecifier(IntEnum):
    Common = auto()
    Entry = auto()

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

@dataclass
class Function:
    specifier: EFunctionSpecifier
    label: int
    identifier: str
    retArg: CommandDefArgument
    args: list[CommandDefArgument]
    line: int
    column: int

@dataclass
class Scope:
    commands: dict[str, Command]
    functions: dict[str, Function]
    childScopes: list

@dataclass
class EvArg:
    argType: EvArgType
    data: int

@dataclass
class EvCmd:
    cmdType: EvCmdType
    args: list[EvArg]

@dataclass
class Label:
    nameIdx: int # StrTbl
    commands: list[EvCmd]

def encode_float(var):
    var = float(var)
    data = int(struct.unpack('<i', struct.pack('<f', var))[0])
    return data

class evcCompiler(evcListener):
    def __init__(self, ifpath):
        self.src_ifpath = ifpath
        self.now_src_ifpath = ifpath
        self.logger = logging.getLogger(__name__)
        self.scope = Scope(
            {},
            {},
            []
        )
        self.globalScope = self.scope
        self.labels = {}
        self.strTbl = []
    
    def parseNumberContext(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return float(ctx.NUMBER().getText())

    def parseNumberContextInt(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return int(ctx.NUMBER().getText())

    def parseType(self, argType:evcParser.TypeContext):
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


    def parseFunctionSpecifier(self, ctx:evcParser.FunctionSpecifierContext):
        if ctx.COMMON() is not None:
            return EFunctionSpecifier.Common
        elif ctx.ENTRY is not None:
            return EFunctionSpecifier.Entry

    def parseFuncArgStorage(self, ctx:evcParser.FuncArgStorageContext):
        if ctx is not None:
            if ctx.RETURN() is not None:
                storage = RETURN_STORAGE
            else:
                storage = self.parseNumberContextInt(ctx.number())
        else:
            storage = None
        return storage
    
    def mapFuncArg(self, ctx:evcParser.FuncArgContext):
        identifier = ctx.Identifier().getText()
        storage = parseFuncArgStorage(ctx.funcArgStorage())
        eArgType = self.parseType(ctx.type_())
        argTypeIdentifier = ctx.type_().getText()

        # TODO: Validate storage based on type

        return CommandDefArgument(
            eArgType,
            argTypeIdentifier,
            identifier,
            storage,
            ctx.start.line,
            ctx.start.column
        )

    def parseFuncArgList(self, ctx:evcParser.FuncArgListContext):
        return map(self.mapFuncArg, ctx.funcArg())

    def parseRetFuncArg(self, ctx:evcParser.TypeContext):
        eArgType = self.parseType(ctx)
        argTypeIdentifier = ctx.getText()
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
        if ctx.Identifier() is None:
            self.logger.error("Invalid name for command at: {}:{}:{}".format(self.now_src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None

        storage = self.parseNumberContextInt(ctx.number())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())

        if ctx.type_() is not None:
            retArg = self.parseRetFuncArg(ctx.type_())

        self.scope.commands[identifier] = Command(
            identifier,
            storage,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        )

    def addStringToTable(self, string):
        if string not in self.strTbl:
            self.strTbl.append(string)
            return len(self.strTbl) - 1
        return self.strTbl.index(string)

    def generateLabel(self, name):
        idx = self.addStringToTable(name)
        label = Label(idx, [])
        self.labels[idx] = label
        return label

    def enterFunction(self, ctx:evcParser.FunctionContext):
        if ctx.Identifier() is None:
            self.logger.error("Invalid name for function at: {}:{}:{}".format(self.now_src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None
        specifier = None

        if ctx.functionSpecifier() is not None:
            specifier = self.parseFunctionSpecifier(ctx.functionSpecifier())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())

        if ctx.type_() is not None:
            retArg = self.parseRetFuncArg(ctx.type_())

        if specifier is not None:
            labelName = identifier
        else:
            # TODO: Need to properly mangle identifier based on scope.
            labelName = "_{}".format(identifier)

        label = self.generateLabel(labelName)
        
        self.scope.functions[identifier] = Function(
            specifier,
            label.nameIdx,
            identifier,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        )