# Generated from evc.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .evcParser import evcParser
else:
    from evcParser import evcParser

# This class defines a complete listener for a parse tree produced by evcParser.
class evcListener(ParseTreeListener):

    # Enter a parse tree produced by evcParser#prog.
    def enterProg(self, ctx:evcParser.ProgContext):
        pass

    # Exit a parse tree produced by evcParser#prog.
    def exitProg(self, ctx:evcParser.ProgContext):
        pass


    # Enter a parse tree produced by evcParser#progEntry.
    def enterProgEntry(self, ctx:evcParser.ProgEntryContext):
        pass

    # Exit a parse tree produced by evcParser#progEntry.
    def exitProgEntry(self, ctx:evcParser.ProgEntryContext):
        pass


    # Enter a parse tree produced by evcParser#import_.
    def enterImport_(self, ctx:evcParser.Import_Context):
        pass

    # Exit a parse tree produced by evcParser#import_.
    def exitImport_(self, ctx:evcParser.Import_Context):
        pass


    # Enter a parse tree produced by evcParser#fromImport.
    def enterFromImport(self, ctx:evcParser.FromImportContext):
        pass

    # Exit a parse tree produced by evcParser#fromImport.
    def exitFromImport(self, ctx:evcParser.FromImportContext):
        pass


    # Enter a parse tree produced by evcParser#namespace.
    def enterNamespace(self, ctx:evcParser.NamespaceContext):
        pass

    # Exit a parse tree produced by evcParser#namespace.
    def exitNamespace(self, ctx:evcParser.NamespaceContext):
        pass


    # Enter a parse tree produced by evcParser#alias.
    def enterAlias(self, ctx:evcParser.AliasContext):
        pass

    # Exit a parse tree produced by evcParser#alias.
    def exitAlias(self, ctx:evcParser.AliasContext):
        pass


    # Enter a parse tree produced by evcParser#aliasRh.
    def enterAliasRh(self, ctx:evcParser.AliasRhContext):
        pass

    # Exit a parse tree produced by evcParser#aliasRh.
    def exitAliasRh(self, ctx:evcParser.AliasRhContext):
        pass


    # Enter a parse tree produced by evcParser#enum.
    def enterEnum(self, ctx:evcParser.EnumContext):
        pass

    # Exit a parse tree produced by evcParser#enum.
    def exitEnum(self, ctx:evcParser.EnumContext):
        pass


    # Enter a parse tree produced by evcParser#enumEntry.
    def enterEnumEntry(self, ctx:evcParser.EnumEntryContext):
        pass

    # Exit a parse tree produced by evcParser#enumEntry.
    def exitEnumEntry(self, ctx:evcParser.EnumEntryContext):
        pass


    # Enter a parse tree produced by evcParser#command.
    def enterCommand(self, ctx:evcParser.CommandContext):
        pass

    # Exit a parse tree produced by evcParser#command.
    def exitCommand(self, ctx:evcParser.CommandContext):
        pass


    # Enter a parse tree produced by evcParser#animation.
    def enterAnimation(self, ctx:evcParser.AnimationContext):
        pass

    # Exit a parse tree produced by evcParser#animation.
    def exitAnimation(self, ctx:evcParser.AnimationContext):
        pass


    # Enter a parse tree produced by evcParser#animationBlock.
    def enterAnimationBlock(self, ctx:evcParser.AnimationBlockContext):
        pass

    # Exit a parse tree produced by evcParser#animationBlock.
    def exitAnimationBlock(self, ctx:evcParser.AnimationBlockContext):
        pass


    # Enter a parse tree produced by evcParser#animationLock.
    def enterAnimationLock(self, ctx:evcParser.AnimationLockContext):
        pass

    # Exit a parse tree produced by evcParser#animationLock.
    def exitAnimationLock(self, ctx:evcParser.AnimationLockContext):
        pass


    # Enter a parse tree produced by evcParser#function.
    def enterFunction(self, ctx:evcParser.FunctionContext):
        pass

    # Exit a parse tree produced by evcParser#function.
    def exitFunction(self, ctx:evcParser.FunctionContext):
        pass


    # Enter a parse tree produced by evcParser#functionSpecifier.
    def enterFunctionSpecifier(self, ctx:evcParser.FunctionSpecifierContext):
        pass

    # Exit a parse tree produced by evcParser#functionSpecifier.
    def exitFunctionSpecifier(self, ctx:evcParser.FunctionSpecifierContext):
        pass


    # Enter a parse tree produced by evcParser#funcArgList.
    def enterFuncArgList(self, ctx:evcParser.FuncArgListContext):
        pass

    # Exit a parse tree produced by evcParser#funcArgList.
    def exitFuncArgList(self, ctx:evcParser.FuncArgListContext):
        pass


    # Enter a parse tree produced by evcParser#funcArg.
    def enterFuncArg(self, ctx:evcParser.FuncArgContext):
        pass

    # Exit a parse tree produced by evcParser#funcArg.
    def exitFuncArg(self, ctx:evcParser.FuncArgContext):
        pass


    # Enter a parse tree produced by evcParser#retFuncArg.
    def enterRetFuncArg(self, ctx:evcParser.RetFuncArgContext):
        pass

    # Exit a parse tree produced by evcParser#retFuncArg.
    def exitRetFuncArg(self, ctx:evcParser.RetFuncArgContext):
        pass


    # Enter a parse tree produced by evcParser#functionCall.
    def enterFunctionCall(self, ctx:evcParser.FunctionCallContext):
        pass

    # Exit a parse tree produced by evcParser#functionCall.
    def exitFunctionCall(self, ctx:evcParser.FunctionCallContext):
        pass


    # Enter a parse tree produced by evcParser#funcCallArgList.
    def enterFuncCallArgList(self, ctx:evcParser.FuncCallArgListContext):
        pass

    # Exit a parse tree produced by evcParser#funcCallArgList.
    def exitFuncCallArgList(self, ctx:evcParser.FuncCallArgListContext):
        pass


    # Enter a parse tree produced by evcParser#funcCallArg.
    def enterFuncCallArg(self, ctx:evcParser.FuncCallArgContext):
        pass

    # Exit a parse tree produced by evcParser#funcCallArg.
    def exitFuncCallArg(self, ctx:evcParser.FuncCallArgContext):
        pass


    # Enter a parse tree produced by evcParser#block.
    def enterBlock(self, ctx:evcParser.BlockContext):
        pass

    # Exit a parse tree produced by evcParser#block.
    def exitBlock(self, ctx:evcParser.BlockContext):
        pass


    # Enter a parse tree produced by evcParser#blockEntry.
    def enterBlockEntry(self, ctx:evcParser.BlockEntryContext):
        pass

    # Exit a parse tree produced by evcParser#blockEntry.
    def exitBlockEntry(self, ctx:evcParser.BlockEntryContext):
        pass


    # Enter a parse tree produced by evcParser#switchBlock.
    def enterSwitchBlock(self, ctx:evcParser.SwitchBlockContext):
        pass

    # Exit a parse tree produced by evcParser#switchBlock.
    def exitSwitchBlock(self, ctx:evcParser.SwitchBlockContext):
        pass


    # Enter a parse tree produced by evcParser#caseBlock.
    def enterCaseBlock(self, ctx:evcParser.CaseBlockContext):
        pass

    # Exit a parse tree produced by evcParser#caseBlock.
    def exitCaseBlock(self, ctx:evcParser.CaseBlockContext):
        pass


    # Enter a parse tree produced by evcParser#break.
    def enterBreak(self, ctx:evcParser.BreakContext):
        pass

    # Exit a parse tree produced by evcParser#break.
    def exitBreak(self, ctx:evcParser.BreakContext):
        pass


    # Enter a parse tree produced by evcParser#return.
    def enterReturn(self, ctx:evcParser.ReturnContext):
        pass

    # Exit a parse tree produced by evcParser#return.
    def exitReturn(self, ctx:evcParser.ReturnContext):
        pass


    # Enter a parse tree produced by evcParser#talkBlock.
    def enterTalkBlock(self, ctx:evcParser.TalkBlockContext):
        pass

    # Exit a parse tree produced by evcParser#talkBlock.
    def exitTalkBlock(self, ctx:evcParser.TalkBlockContext):
        pass


    # Enter a parse tree produced by evcParser#forBlock.
    def enterForBlock(self, ctx:evcParser.ForBlockContext):
        pass

    # Exit a parse tree produced by evcParser#forBlock.
    def exitForBlock(self, ctx:evcParser.ForBlockContext):
        pass


    # Enter a parse tree produced by evcParser#whileBlock.
    def enterWhileBlock(self, ctx:evcParser.WhileBlockContext):
        pass

    # Exit a parse tree produced by evcParser#whileBlock.
    def exitWhileBlock(self, ctx:evcParser.WhileBlockContext):
        pass


    # Enter a parse tree produced by evcParser#variableDefinition.
    def enterVariableDefinition(self, ctx:evcParser.VariableDefinitionContext):
        pass

    # Exit a parse tree produced by evcParser#variableDefinition.
    def exitVariableDefinition(self, ctx:evcParser.VariableDefinitionContext):
        pass


    # Enter a parse tree produced by evcParser#variableAssignment.
    def enterVariableAssignment(self, ctx:evcParser.VariableAssignmentContext):
        pass

    # Exit a parse tree produced by evcParser#variableAssignment.
    def exitVariableAssignment(self, ctx:evcParser.VariableAssignmentContext):
        pass


    # Enter a parse tree produced by evcParser#variableRightHandAssignment.
    def enterVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext):
        pass

    # Exit a parse tree produced by evcParser#variableRightHandAssignment.
    def exitVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext):
        pass


    # Enter a parse tree produced by evcParser#ifBlock.
    def enterIfBlock(self, ctx:evcParser.IfBlockContext):
        pass

    # Exit a parse tree produced by evcParser#ifBlock.
    def exitIfBlock(self, ctx:evcParser.IfBlockContext):
        pass


    # Enter a parse tree produced by evcParser#elseIfBlock.
    def enterElseIfBlock(self, ctx:evcParser.ElseIfBlockContext):
        pass

    # Exit a parse tree produced by evcParser#elseIfBlock.
    def exitElseIfBlock(self, ctx:evcParser.ElseIfBlockContext):
        pass


    # Enter a parse tree produced by evcParser#unlessBlock.
    def enterUnlessBlock(self, ctx:evcParser.UnlessBlockContext):
        pass

    # Exit a parse tree produced by evcParser#unlessBlock.
    def exitUnlessBlock(self, ctx:evcParser.UnlessBlockContext):
        pass


    # Enter a parse tree produced by evcParser#elseBlock.
    def enterElseBlock(self, ctx:evcParser.ElseBlockContext):
        pass

    # Exit a parse tree produced by evcParser#elseBlock.
    def exitElseBlock(self, ctx:evcParser.ElseBlockContext):
        pass


    # Enter a parse tree produced by evcParser#ifExpr.
    def enterIfExpr(self, ctx:evcParser.IfExprContext):
        pass

    # Exit a parse tree produced by evcParser#ifExpr.
    def exitIfExpr(self, ctx:evcParser.IfExprContext):
        pass


    # Enter a parse tree produced by evcParser#number.
    def enterNumber(self, ctx:evcParser.NumberContext):
        pass

    # Exit a parse tree produced by evcParser#number.
    def exitNumber(self, ctx:evcParser.NumberContext):
        pass


    # Enter a parse tree produced by evcParser#string_.
    def enterString_(self, ctx:evcParser.String_Context):
        pass

    # Exit a parse tree produced by evcParser#string_.
    def exitString_(self, ctx:evcParser.String_Context):
        pass


    # Enter a parse tree produced by evcParser#comparatorLeft.
    def enterComparatorLeft(self, ctx:evcParser.ComparatorLeftContext):
        pass

    # Exit a parse tree produced by evcParser#comparatorLeft.
    def exitComparatorLeft(self, ctx:evcParser.ComparatorLeftContext):
        pass


    # Enter a parse tree produced by evcParser#comparatorRight.
    def enterComparatorRight(self, ctx:evcParser.ComparatorRightContext):
        pass

    # Exit a parse tree produced by evcParser#comparatorRight.
    def exitComparatorRight(self, ctx:evcParser.ComparatorRightContext):
        pass


    # Enter a parse tree produced by evcParser#boolValue.
    def enterBoolValue(self, ctx:evcParser.BoolValueContext):
        pass

    # Exit a parse tree produced by evcParser#boolValue.
    def exitBoolValue(self, ctx:evcParser.BoolValueContext):
        pass



del evcParser