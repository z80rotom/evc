import logging
import sys
import os


from antlr4 import *
from UnityPy.streams import EndianBinaryWriter

from evcListener import evcListener
from evcLexer import evcLexer
from evcParser import evcParser

from ev_argtype import EvArgType
from ev_cmd import EvCmdType
from ev_work import EvWork
# Not sure what I would use these for directly myself at the moment.
# from ev_flag import EvFlag
# from ev_sys_flag import EvSysFlag

from core import *
from scope_mgr import ScopeManager, Scope

class evcCompiler(evcListener):
    def __init__(self, ifpath):
        self.logger = logging.getLogger(__name__)
        self.src_ifpath = ifpath
        self.labels = {}
        self.strTbl = []
        self.writer = EndianBinaryWriter()
        self.scope_mgr = ScopeManager()
    
    def parseNumberContext(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return float(ctx.NUMBER().getText())

    def parseNumberContextInt(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return int(ctx.NUMBER().getText())
    
    def parseStringContext(self, ctx:evcParser.String_Context):
        strValue = ctx.STRING().getText()[1:-1]
        print(strValue)
        return self.addStringToTable(strValue)

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
        storage = self.parseFuncArgStorage(ctx.funcArgStorage())
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
            self.logger.error("Invalid name for command at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
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

        self.scope_mgr.addCommand(identifier, Command(
            identifier,
            storage,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        ))

    def addStringToTable(self, string):
        if string not in self.strTbl:
            self.strTbl.append(string)
            return len(self.strTbl) - 1
        return self.strTbl.index(string)

    def allocateChildLabel(self, label):
        childIdx = len(label.childLabels)
        name = "__child_{}_{}".format(self.strTbl[label.nameIdx], childIdx)
        newLabel = self.generateLabel(name)
        label.childLabels.append(newLabel)
        return newLabel

    def generateLabel(self, name):
        idx = self.addStringToTable(name)
        label = Label(idx)
        self.labels[idx] = label
        return label

    def parseBlock(self, ctx:evcParser.BlockContext, allocator, label, newScope=None):
        self.scope_mgr.push(newScope)
        for blockEntry in ctx.blockEntry():
            # TODO: Support multidefinition lines
            # TODO: Support tuple returns
            if blockEntry.variableDefinition() is not None:
                variableDefinition = self.parseVariableDefinition(blockEntry.variableDefinition(), allocator, True)
                self.scope_mgr.addVariable(variableDefinition.variable.identifier, variableDefinition.variable)
                label.commands.extend(variableDefinition.commands)
                continue
            if blockEntry.variableAssignment() is not None:
                label.commands.extend(self.parseVariableAssignment(blockEntry.variableAssignment()))
            if blockEntry.functionCall() is not None:
                functionCall = self.parseFunctionCall(blockEntry.functionCall())
                if type(functionCall.function) == Function:
                    # TODO: Function calls not just commands
                    self.logger.warn("Function calls aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                else:
                    commands = self.compileCommandCall(ctx, functionCall, None, None)
                    label.commands.extend(commands)
                continue
            if blockEntry.ifBlock():
                label = self.parseIfBlock(blockEntry.ifBlock(), allocator, label)
                continue
        self.scope_mgr.pop()
    
    def getIdentifier(self, ctx):
        if hasattr(ctx, "Identifier") and ctx.Identifier() is not None:
            return ctx.Identifier().getText()
        elif hasattr(ctx, "ScopedIdentifier") and ctx.ScopedIdentifier() is not None:
            return ctx.ScopedIdentifier().getText()
        return None

    def parseComparatorLeft(self, ctx:evcParser.ComparatorLeftContext):
        storage = None
        eArgType = None
        commands = []
        identifier = self.getIdentifier(ctx)
        functionCallCtx = ctx.functionCall()
        if functionCallCtx is not None:
            functionCall = self.parseFunctionCall(functionCallCtx)
            if type(functionCall.function) == Function:
                # TODO: Function calls not just commands
                self.logger.warn("Function calls aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            else:
                # TODO: Add support for binding result to variable while doing comparison
                storage = EvWork.SCWK_ANSWER.value
                eArgType = functionCall.function.retArg.eArgType
                commands = self.compileCommandCall(ctx, functionCall, None, None)
        elif identifier is not None:
            variable = self.scope_mgr.resolveVariable(identifier)
            if variable is None:
                self.logger.error("Unable to resolve variable with name {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            if variable.isConst:
                self.logger.error("Variable {} is const. Unable to perform comparison: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            storage = variable.storage
            eArgType = variable.eArgType

        return ComparatorLeft(
            storage,
            eArgType,
            commands
        )

    def parseComparator(self, comparatorToken: evcParser.Comparator):
        lookup_table = {
            '==' : 'EQ',
            '!=' : 'NE',
            '<=' : 'LE',
            '>=' : 'GE',
            '<'  : 'LT',
            '>'  : 'GT'
        }

        comparator = comparatorToken.getText()
        if comparator in lookup_table:
            return lookup_table[comparator]
        elif comparator in lookup_table.values():
            return comparator
        else:
            # Raise exception here?
            return None

    def compileComparison(self, comparatorLeft: ComparatorLeft, 
                          comparator: evcParser.Comparator, 
                          comparatorRight: evcParser.ComparatorRightContext, 
                          label: Label):
        commands = []
        cmpArg = EvArg(EvArgType.String, self.addStringToTable(self.parseComparator(comparator)))
        if comparatorRight.number() is not None:
            rightArg = EvArg(
                EvArgType.Value,
                encode_float(self.parseNumberContext(comparatorRight.number()))
            )
            if comparatorLeft.eArgType in (ECommandArgType.Integer, ECommandArgType.Float):
                args = [
                    EvArg(EvArgType.Work, comparatorLeft.storage),
                    cmpArg,
                    rightArg,
                    EvArg(EvArgType.String, label.nameIdx)
                ]
                commands.append(EvCmd(EvCmdType._IFVAL_JUMP, args) )
            else:
                # Should raise exception probably
                pass
        return commands

    def parseIfExpr(self, ctx:evcParser.IfExprContext, label):
        commands = []
        if ctx.comparatorLeft() is not None:
            comparatorLeft = self.parseComparatorLeft(ctx.comparatorLeft())
            commands.extend(comparatorLeft.commands)
            commands.extend(self.compileComparison(comparatorLeft, ctx.Comparator(), ctx.comparatorRight(), label))
        else:
            # Just a variable identifier. Flag on/off checks or checking if a work value != 0
            pass
            
        return commands
    
    def parseIfBlock(self, ctx:evcParser.IfBlockContext, allocator, label):
        ifBlockLabel = self.allocateChildLabel(label)
        # Pass in the ifBlockLabel so it knows what to jump to
        commands = self.parseIfExpr(ctx.ifExpr(), ifBlockLabel)
        label.commands.extend(commands)

        if ctx.block() is not None:
            self.parseBlock(ctx.block(), allocator, ifBlockLabel)

        for elseIfBlockCtx in ctx.elseIfBlock():
            elseIfBlockLabel = self.allocateChildLabel(label)
            commands = self.parseIfExpr(elseIfBlockCtx, elseIfBlockLabel)
            label.commands.extend(commands)

            if elseIfBlockCtx.block() is not None:
                self.parseBlock(elseIfBlockCtx.block(), allocator, elseIfBlockLabel)
        
        if ctx.elseBlock() is not None:
            self.parseBlock(ctx.elseBlock().block(), allocator, label)

        afterLabel = self.allocateChildLabel(label)
        # Only the else block will use the original label
        # Need to return the after label for the block to start using as it's main label now
        return afterLabel

    def parseConstVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext, eArgType):
        constValue = None
        if ctx.number() is not None:
            if eArgType == ECommandArgType.Integer:
                constValue = encode_float(int(ctx.number().getText()))
                try:
                    self.writer.write_int(constValue)
                except Exception as exc:
                    print("Invalid float: {}".format(argVal))
            elif argType == ECommandArgType.NumberEnum:
                self.logger.error("Enums are not fully supported at the moment")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.number().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.boolValue() is not None:
            if eArgType == ECommandArgType.Boolean:
                constValue = int(ctx.boolValue().TRUE() is not None)
            elif eArgType == ECommandArgType.Flag:
                self.logger.error("No such thing as a constant Flag")
                sys.exit()
            elif eArgType == ECommandArgType.SysFlag:
                self.logger.error("No such thing as a constant SysFlag")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.boolValue().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.string_() is not None:
            self.logger.error("Variable must be mutable to assign from string at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        elif ctx.functionCall() is not None:
            self.logger.error("Variable must be mutable to assign from function call at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        else:
            self.logger.error("Unknown variable declaration at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return constValue
    
    def parseMutVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext, eArgType, storage):
        commands = []
        if ctx.number() is not None:
            if eArgType == ECommandArgType.Integer:
                constValue = encode_float(int(ctx.number().getText()))
                try:
                    self.writer.write_int(constValue)
                except Exception as exc:
                    print("Invalid float: {}".format(argVal))
                commands.append(
                    EvCmd(EvCmdType._LDVAL, [
                        EvArg(EvArgType.Work, storage),
                        EvArg(EvArgType.Value, constValue)
                    ])
                )
            elif argType == ECommandArgType.NumberEnum:
                self.logger.error("Enums are not fully supported at the moment")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.number().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.boolValue() is not None:
            if eArgType == ECommandArgType.Boolean:
                self.logger.error("No such thing as a mutable bool")
                sys.exit()
            elif eArgType == ECommandArgType.Flag:
                if ctx.boolValue().TRUE() is not None:
                    commands.append(
                        EvCmd(EvCmdType._FLAG_SET, [
                            EvArg(EvArgType.Flag, storage)    
                        ])
                    )
                else:
                    commands.append(
                        EvCmd(EvCmdType._FLAG_RESET, [
                            EvArg(EvArgType.Flag, storage)    
                        ])
                    )
            elif eArgType == ECommandArgType.SysFlag:
                if ctx.boolValue().TRUE() is not None:
                    commands.append(
                        EvCmd(EvCmdType._SET_SYS_FLAG, [
                            EvArg(EvArgType.SysFlag, storage)    
                        ])
                    )
                else:
                    commands.append(
                        EvCmd(EvCmdType._RESET_SYS_FLAG, [
                            EvArg(EvArgType.SysFlag, storage)    
                        ])
                    )
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.boolValue().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.string_() is not None:
            self.logger.error("String variables aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        elif ctx.functionCall() is not None:
            functionCall = self.parseFunctionCall(ctx.functionCall())
            if type(functionCall.function) == Function:
                self.logger.error("Function calls returning a value aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            else:
                commands.extend(self.compileCommandCall(ctx, functionCall, eArgType, storage))
        else:
            self.logger.error("Unknown variable declaration at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return commands
    
    def compileCommandCall(self, ctx, cmdCall: FunctionCall, eArgTypeRet: ECommandArgType, retStorage=None):
        if retStorage is None:
            retStorage = EvWork.SCWK_ANSWER.value
        commands = []
        if eArgTypeRet is not None and eArgTypeRet != cmdCall.function.retArg.eArgType:
            # Note: Looks like passed in eArgTypeRet is probably not accurate here.
            self.logger.error("Invalid return type of command ({} != {}) for variable at: {}:{}:{}".format(eArgTypeRet, cmdCall.function.retArg.eArgType, self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        
        # TODO: Validate values passed to the command
        # Probably only worth warnings at the moment since commands aren't well defined.
        args = []
        for arg in cmdCall.args:
            if arg.isConst:
                if arg.constValueType in (ECommandArgType.Integer, ECommandArgType.Float):
                    args.append(EvArg(EvArgType.Value, encode_float(arg.constValue)))
                elif arg.constValueType == ECommandArgType.String:
                    args.append(EvArg(EvArgType.String, arg.constValue))
                elif arg.constValueType == ECommandArgType.Boolean:
                    self.logger.error("Not possible to pass const bool to command at: {}:{}:{}. Must use flag/sysflag for storage.".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
                else:
                    self.logger.error("I missed something it seems at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
            else:
                if arg.variable.eArgType in (ECommandArgType.Integer, ECommandArgType.Float):
                    args.append(EvArg(EvArgType.Work, arg.variable.storage))
                elif arg.variable.eArgType == ECommandArgType.Flag:
                    args.append(EvArg(EvArgType.Flag, arg.variable.storage))
                elif arg.variable.eArgType == ECommandArgType.SysFlag:
                    args.append(EvArg(EvArgType.SysFlag, arg.variable.storage))
                else:
                    self.logger.error("I missed something it seems at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
        retIdx = 0
        for i, cmdDef in enumerate(cmdCall.function.args):
            if cmdDef.storage == RETURN_STORAGE:
                self.logger.info("Using custom return storage")
                retIdx = i
                break
        args.insert(retIdx, EvArg(EvArgType.Work, retStorage))

        commands.append(
            EvCmd(cmdCall.function.storage, args)
        )

        return commands

    def mapFuncCallArg(self, ctx:evcParser.FuncCallArgContext):
        if ctx.Identifier() is not None:
            identifier = ctx.Identifier().getText()
            variable = self.scope_mgr.resolveVariable(identifier)
            if variable is None:
                self.logger.error("Unable to resolve variable name {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            # Translate const variable into the actual value
            if variable.isConst:
                return FunctionCallArg(None, True, variable.constValue, variable.eArgType)
            return FunctionCallArg(variable, False, None, None)
        if ctx.string_() is not None:
            strValue = self.parseStringContext(ctx.string_())
            if strValue is None:
                self.logger.error("Unable to parse string at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCallArg(None, True, strValue, ECommandArgType.String)
        
        if ctx.number() is not None:
            number = self.parseNumberContext(ctx.number())
            if number is None:
                self.logger.error("Unable to parse number at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCallArg(None, True, number, ECommandArgType.Float)

    def parseFuncCallArgList(self, ctx:evcParser.FuncCallArgListContext):
        return map(self.mapFuncCallArg, ctx.funcCallArg())

    def parseFunctionCall(self, ctx:evcParser.FunctionCallContext):
        identifier = self.getIdentifier(ctx)
        if identifier is None:
            self.logger.error("Unable to parse function/command name at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        args = self.parseFuncCallArgList(ctx.funcCallArgList())

        command = self.scope_mgr.resolveCommand(identifier)
        if command is not None:
            return FunctionCall(command, args)
        else:
            function = self.scope_mgr.resolveFunction(identifier)
            if function is None:
                self.logger.error("Unable to resolve function/command name {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCall(function, args)

    def parseVariableAssignment(self, ctx:evcParser.VariableAssignmentContext):
        identifier = self.getIdentifier(ctx)

        assignmentOperator = ctx.assignmentOperator().getText()
        if assignmentOperator != "=":
            self.logger.warn("Unable to peform assignment operator {} on variable {} at: {}:{}:{}".format(assignmentOperator, identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
            return []

        variable = self.scope_mgr.resolveVariable(identifier)
        storage = variable.storage
        eArgType = variable.eArgType
        aCtx = ctx.variableRightHandAssignment()
        if aCtx is not None:
            return self.parseMutVariableRightHandAssignment(aCtx, eArgType, storage)


    def parseVariableDefinition(self, ctx:evcParser.VariableDefinitionContext, allocator, canAssignMut):
        eArgType = self.parseType(ctx.type_())
        argTypeIdentifier = ctx.type_().getText()
        identifier = ctx.Identifier().getText()
        storage = self.parseNumberContextInt(ctx.number())
        isConst = ctx.CONST() is not None
        constValue = None

        # TODO: Check if variable is already defined in scope
        commands = []
        aCtx = ctx.variableRightHandAssignment()
        if isConst:
            if aCtx is not None:
                constValue = self.parseConstVariableRightHandAssignment(aCtx, eArgType)
            else:
                self.logger.error("Must specify value for const variable: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        else:
            if storage is None:
                storage = allocator(ctx, eArgType)
            if aCtx is not None:
                if not canAssignMut:
                    self.logger.error("Not able to assign mut at this scope at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
                commands = self.parseMutVariableRightHandAssignment(aCtx, eArgType, storage)
        # print(commands)
        return VariableDefinition(Variable(
            eArgType,
            argTypeIdentifier,
            identifier,
            storage,
            isConst,
            constValue,
            ctx.start.line,
            ctx.start.column,
        ), commands)

    def allocateStorageFunction(self, ctx, eArgType: ECommandArgType, allocatorData: AllocatorData):
        # TODO: Make the allocator functions more consistent
        WORK_ALLOCATION_ORDER = []
        WORK_ALLOCATION_ORDER.extend(range(32)) # LOCALWORK0...LOCALWORK31
        # Don't want to work with SCWK_TEMP0 yet, because I want to use them for arguments
        # for common functions because that's what ILCA does.
        # WORK_ALLOCATION_ORDER.extend(range(238, 242)) # SCWK_TEMP0...SCWK_TEMP3
        if eArgType == ECommandArgType.Integer:
            if len(allocatorData.works) >= len(WORK_ALLOCATION_ORDER):
                self.logger.error("Out of LOCALWORK values to allocate. Specify storage if you really need > 32 ints: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
                return
            idx = len(allocatorData.works)
            storage = WORK_ALLOCATION_ORDER[idx]
            allocatorData.works.append(storage)
            return storage
        else:
            self.logger.error("Cannot automatically allocate storage for non-int: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()

    def allocateStorageFunctionArgument(self, eArgType: ECommandArgType, allocatorData: AllocatorData):
        # TODO: Figure out error handling without always just going for the self.logger.error
        # especially because not every function has ctx information
        WORK_ALLOCATION_ORDER = []
        WORK_ALLOCATION_ORDER.extend(range(238, 242)) # SCWK_TEMP0...SCWK_TEMP3
        if eArgType == ECommandArgType.Integer:
            if len(allocatorData.works) >= len(WORK_ALLOCATION_ORDER):
                return None
                # self.logger.error("Out of TEMP0 values to allocate. Specify storage if you really need > 32 ints: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                # sys.exit()
                # return
            idx = len(allocatorData.works)
            storage = WORK_ALLOCATION_ORDER[idx]
            allocatorData.works.append(storage)
            return storage
        else:
            return None

    def mapFuncArgumentToVar(self, funcArg, allocatorData):
        storage = funcArg.storage
        if storage is None:
            storage = self.allocateStorageFunctionArgument(funcArg.eArgType, allocatorData)
        return Variable(
            funcArg.eArgType,
            funcArg.argTypeIdentifier,
            funcArg.identifier,
            storage,
            False,
            None,
            funcArg.line,
            funcArg.column
        )

    def enterFunction(self, ctx:evcParser.FunctionContext):
        if ctx.Identifier() is None:
            self.logger.error("Invalid name for function at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None
        specifier = None
        functionScope = Scope()

        if ctx.functionSpecifier() is not None:
            specifier = self.parseFunctionSpecifier(ctx.functionSpecifier())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())
            alloc = AllocatorData()
            funcArgVars = map(lambda funcArg: self.mapFuncArgumentToVar(funcArg, alloc), args)
            self.scope_mgr.addVariables(funcArgVars, scope=functionScope)

        if ctx.type_() is not None:
            retArg = self.parseRetFuncArg(ctx.type_())

        if specifier is not None:
            labelName = identifier
        else:
            # TODO: Need to properly mangle identifier based on scope.
            labelName = "_{}".format(identifier)

        label = self.generateLabel(labelName)
        
        self.scope_mgr.addFunction(identifier, Function(
            specifier,
            label.nameIdx,
            identifier,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        ))

        # Only integers should be scoped to function.
        allocatorData = AllocatorData()
        # Time to start handling blocks Yipee
        self.parseBlock(ctx.block(), 
            lambda ctx, eArgType: self.allocateStorageFunction(ctx, eArgType, allocatorData),
            label, newScope=functionScope)

    def readImport(self, ifpath):
        print("Processing file: ", ifpath)
        input_stream = FileStream(ifpath, encoding='utf-8')
        lexer = evcLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = evcParser(stream)
        tree = parser.prog()

        assembler = evcCompiler(ifpath)
        walker = ParseTreeWalker()
        walker.walk(assembler, tree)
        return assembler

    def handleImport(self, ctx, identifier):
        resolveOrder = [
            os.path.join(os.path.dirname(self.src_ifpath), "{}.evc".format(identifier)),
            "scripts/lib/{}/lib.evc".format(identifier)
        ]

        resolvedIfpath = None
        for ifpath in resolveOrder:
            if os.path.exists(ifpath):
                resolvedIfpath = ifpath
                break
        if resolvedIfpath is None:
            self.logger.error("Unable to resolve import '{}' at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return self.readImport(resolvedIfpath)

    def enterFromImport(self, ctx:evcParser.FromImportContext):
        assembler = self.handleImport(ctx, ctx.Identifier().getText())
        if ctx.fromImportRhs() is None:
            self.logger.error("Malformed from ... import {{ ... }} at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()

        if ctx.fromImportRhs().WILDCARD() is not None:
            self.scope_mgr.wildCardImport(assembler.scope_mgr)
        else:
            identifiers = [identifierTkn.getText() in ctx.fromImportRhs().Identifier()]
            foundIdentifiers = self.scope_mgr.fromImport(assembler.scope_mgr, identifiers)
            if not foundIdentifiers:
                self.logger.error("Unable to retrieve identifier {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
    
    def enterImport_(self, ctx:evcParser.Import_Context):
        assembler = self.handleImport(ctx, ctx.Identifier().getText())
        assembler.scope_mgr.getGlobalScope().prefix = ctx.Identifier().getText()
        self.scope_mgr.addChildGlobal(assembler.scope_mgr.getGlobalScope())

    def enterProgEntry(self, ctx:evcParser.ProgEntryContext):
        if ctx.variableDefinition() is not None:
            # print("Processing variable definition")
            allocator = lambda ctx, eArgType: self.logger.error("Unable to allocate work at this scope at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            variableDefinition = self.parseVariableDefinition(ctx.variableDefinition(), allocator, True)
            self.scope_mgr.addVariable(variableDefinition.variable.identifier, variableDefinition.variable)
        
    # Enter a parse tree produced by evcParser#namespace.
    def enterNamespace(self, ctx:evcParser.NamespaceContext):
        newScope = Scope()
        newScope.prefix = ctx.Identifier().getText()
        newScope = self.scope_mgr.push(newScope=newScope)

    # Exit a parse tree produced by evcParser#namespace.
    def exitNamespace(self, ctx:evcParser.NamespaceContext):
        self.scope_mgr.pop()