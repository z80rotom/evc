import logging

from core import *
from dataclasses import dataclass, field

@dataclass
class Scope:
    prefix: str = field(default_factory=lambda: None)
    animations: dict[str, Animation] = field(default_factory=dict)
    commands: dict[str, Command] = field(default_factory=dict)
    functions: dict[str, Function] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    parentScope: object = field(default_factory=lambda: None)
    childScopes: list  = field(default_factory=list)

class ScopeManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scope = Scope()
        self.globalScope = self.scope
        self.prevScope = []
    
    def addAnimation(self, identifier, animation):
        self.scope.animations[identifier] = animation

    def addFunction(self, identifier, function):
        self.scope.functions[identifier] = function
    
    def addCommand(self, identifier, command):
        self.scope.commands[identifier] = command
    
    def addVariable(self, identifier, variable):
        self.scope.variables[identifier] = variable
    
    def addVariables(self, variables, scope=None):
        if scope is None:
            scope = self.scope
        for variable in variables:
            scope.variables[variable.identifier] = variable

    def resolveScopedIdentifier(self, identifier, fieldName):
        prefix = identifier[:-1] # All but last
        leaf = identifier[-1] # Last
        
        currSearchPrefix = prefix[0]
        currSearchIdx = 0
        cmpPrefix = []
        itScope = [self.globalScope]
        while len(itScope) > 0:
            newItScope = []
            for scope in itScope:
                if cmpPrefix == prefix and scope.prefix is not None:
                    # Already found our prefix, don't go further into named scopes
                    continue
                if cmpPrefix == prefix and scope.prefix is None:
                    if hasattr(scope, fieldName) and leaf in getattr(scope, fieldName):
                        return getattr(scope, fieldName)[identifier]
                if cmpPrefix != prefix and scope.prefix is not None:
                    if currSearchPrefix == scope.prefix and (cmpPrefix + [currSearchPrefix]) == prefix:
                        if hasattr(scope, fieldName) and leaf in getattr(scope, fieldName):
                            return getattr(scope, fieldName)[leaf]
                    elif currSearchPrefix == scope.prefix:
                        # Found the scope. Shouldn't be able to create one with the same prefix.
                        # So clean out the next iterator and fill with your children
                        newItScope = []
                        newItScope.extend(scope.childScopes)
                        cmpPrefix.append(scope.prefix)
                        currSearchIdx += 1
                        currSearchPrefix = prefix[currSearchIdx]
                        break
                if cmpPrefix != prefix and scope.prefix is None:
                    newItScope.extend(scope.childScopes)
            itScope = newItScope
        return None


    def resolveIdentifier(self, identifier, fieldName):
        identifierSplit = identifier.split("::")
        if len(identifierSplit) > 1:
            return self.resolveScopedIdentifier(identifierSplit, fieldName)
        if hasattr(self.globalScope, fieldName) and identifier in getattr(self.globalScope, fieldName):
            return getattr(self.globalScope, fieldName)[identifier]
        if hasattr(self.scope, fieldName) and identifier in getattr(self.scope, fieldName):
            return getattr(self.scope, fieldName)[identifier]
        
        if self.scope.parentScope is not None:
            itScope = [self.scope.parentScope]
            while len(itScope) > 0:
                newItScope = []
                for scope in itScope:
                    if scope.prefix is not None:
                        continue
                    if hasattr(scope, fieldName) and identifier in getattr(scope, fieldName):
                        return getattr(scope, fieldName)[identifier]
                    if scope.parentScope is None:
                        continue
                    if scope.parentScope is self.globalScope:
                        continue
                    newItScope.append(scope.parentScope)
                itScope = newItScope
        return None

    def resolveCommand(self, identifier):
        return self.resolveIdentifier(identifier, "commands")

    def resolveFunction(self, identifier):
        return self.resolveIdentifier(identifier, "functions")
    
    def resolveVariable(self, identifier):
        return self.resolveIdentifier(identifier, "variables")
    
    def resolveAnimation(self, identifier):
        return self.resolveIdentifier(identifier, "animations")
    
    def getGlobalScope(self):
        return self.globalScope

    def addChildGlobal(self, scope):
        scope.parentScope = self.globalScope
        self.globalScope.childScopes.append(scope)

    def addChild(self, scope):
        scope.parentScope = self.scope
        self.scope.childScopes.append(scope)

    def push(self, newScope=None):
        if newScope is None:
            newScope = Scope()
        self.addChild(newScope)
        self.prevScope.append(self.scope)
        self.scope = newScope
        return self.scope

    def pop(self):
        if len(self.prevScope) <= 0:
            self.logger.warn("Attempting to popscope without prevScope")
            return
        if self.scope is self.globalScope:
            self.logger.warn("Attempting to popScope when at globalScope")
            return
        self.scope = self.prevScope.pop()
        return self.scope
    
    def wildCardImport(self, scope_mgr):
        self.globalScope.animations.update(scope_mgr.getGlobalScope().animations)
        self.globalScope.commands.update(scope_mgr.getGlobalScope().commands)
        self.globalScope.functions.update(scope_mgr.getGlobalScope().functions)
        self.globalScope.variables.update(scope_mgr.getGlobalScope().variables)
        self.globalScope.childScopes.extend(scope_mgr.getGlobalScope().childScopes)
        # print(scope_mgr.getGlobalScope().childScopes)

    def fromImport(self, scope_mgr, identifiers):
        # How to bring in namespaced variables specifically?
        for identifier in identifiers:
            foundIdentifier = False
            if identifier in scope_mgr.getGlobalScope().animations:
                self.scope.animations[identifier] = scope_mgr.getGlobalScope().animations[identifier]
                foundIdentifier = True
            elif identifier in scope_mgr.getGlobalScope().commands:
                self.scope.commands[identifier] = scope_mgr.getGlobalScope().commands[identifier]
                foundIdentifier = True
            elif identifier in scope_mgr.getGlobalScope().functions:
                self.scope.functions[identifier] = scope_mgr.getGlobalScope().functions[identifier]
                foundIdentifier = True
            elif identifier in scope_mgr.getGlobalScope().variables:
                self.scope.variables[identifier] = scope_mgr.getGlobalScope().variables[identifier]
                foundIdentifier = True
            if not foundIdentifier:
                return foundIdentifier