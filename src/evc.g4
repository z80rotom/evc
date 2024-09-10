
grammar evc;


prog
   : progEntry+
   ;

progEntry
    :  function
    |  animation
    |  command
    |  enum
    |  alias
    |  variableDefinition
    |  namespace
    |  import_
    |  fromImport
    ;

import_
    :   IMPORT Identifier ';'
    ;

fromImport
    :   FROM Identifier IMPORT ('*' | Identifier) ';'
    ;

namespace
    :   NAMESPACE Identifier '{' progEntry+ '}'
    ;

alias
    :   ALIAS COMMAND Identifier ':' number '=' aliasRh ';'
    ;

aliasRh
    : Identifier
    ;

// Enum
enum
    :   ENUM Identifier '{' enumEntry (',' enumEntry)* ';' '}'
    ;

enumEntry
    :   Identifier '=' number
    ;

// Command
command
    :   COMMAND Identifier '(' funcArgList ')' ('->' retFuncArg)? ':' number ';'
    ;
// End command

// Animation
// Defines an animation
animation
    :   ANIMATION Identifier '{' animationBlock '}'
    ;

animationBlock
    :   (functionCall ';')+
    ;

// Defines a block where a placedata should be locked while an animation is going on
animationLock
    :   LOCK Identifier '(' string_ ')' '{' block '}'
    ;

// End animation

// Functions
function
    : functionSpecifier? FUNCTION Identifier '(' funcArgList ')' ('->' retFuncArg)? '{' block '}'
    ;

functionSpecifier
    :   COMMON
    |   ENTRY
    ;

funcArgList
    : funcArg?
    | funcArg (',' funcArg)+
    ;

funcArg
    : Type Identifier (':' number)?
    ;

retFuncArg
    : Type
    ;

functionCall
    : (Identifier | ScopedIdentifier) '(' funcCallArgList ')'
    ;

funcCallArgList
    : funcCallArg?
    | funcCallArg (',' funcCallArg)+
    ;

funcCallArg
    : Identifier
    | string_
    | number
    ;

// End Functions


// What all can be in a block?
block
    : blockEntry+
    ;

blockEntry
    : ifBlock
    | unlessBlock
    | switchBlock
    | whileBlock
    | forBlock
    | animationLock
    | talkBlock
    | variableAssignment ';'
    | variableDefinition ';'
    | functionCall ';'
    | return ';'
    | break ';'
    ;

switchBlock
    : SWITCH '(' ifExpr ')' '{' caseBlock+ '}'
    ;

caseBlock
    : CASE (Identifier | number) ':' block
    | DEFAULT ':' block
    ;

break
    :   BREAK
    ;

return
    :   RETURN  (Identifier | number)?
    ;

talkBlock
    : TALK '{' block '}'
    ;

forBlock
    : FOR '(' variableDefinition ';' ifExpr ';'  ')' '{' block '}'
    ;

whileBlock
    : WHILE '(' ifExpr ')' '{' block '}'
    ;

variableDefinition
    :   CONST? Type Identifier (':' number)? ('=' variableRightHandAssignment)?
    ;

variableAssignment
    :   Identifier '=' variableRightHandAssignment
    ;

variableRightHandAssignment
    :   number
    |   boolValue
    |   string_
    |   functionCall
    ;

ifBlock
    : IF '(' ifExpr ')' '{' block '}' (elseIfBlock)* elseBlock?
    ;

elseIfBlock
    : ELSE IF '(' ifExpr ')' '{' block '}'
    ;

unlessBlock
    : UNLESS '(' ifExpr ')' '{' block '}' elseBlock?
    ;

elseBlock
    : ELSE '{' block '}'
    ;

ifExpr
    : comparatorLeft Comparator comparatorRight
    | Identifier
    | functionCall
    ;

number
   : NUMBER
   ;

string_
   : STRING
   ;

comparatorLeft
    : Identifier
    | functionCall
    ;

comparatorRight
    : Identifier
    | number
    | boolValue
    ;

boolValue
    : TRUE
    | FALSE
    ;

STRING
   : '\u0027' ~'\u0027'* '\u0027'
   ;

Comparator
    : EQ
    | NE
    | LT
    | GT
    | LE
    | GE
    ;

Type
    : FLAG
    | SYSFLAG
    | INT
    | FLOAT
    | BOOL
    | STR
    | ScopedIdentifier // Enums
    ;

Comment
    : '//' ~ [\r\n]* -> skip
    ;

BlockComment
    : '/*' .*? '*/' -> skip
    ;

NUMBER
   : '-'? Digit+ ( '.' Digit+ )?
   ;

EOL
   : [\r\n] -> skip
   ;

WS
   : [ \t] -> skip
   ;


// Keywords
ALIAS: 'alias';

ANIMATION: 'animation';

BOOL: 'bool';

BREAK: 'break';

CASE: 'case';

COMMAND: 'command';

COMMON: 'common';

CONST: 'const';

DEFAULT: 'default';

ELSE: 'else';

ENUM: 'enum';

ENTRY: 'entry';

FALSE: 'false';

FLAG: 'flag';

FLOAT: 'float';

FOR: 'for';

FROM: 'from';

FUNCTION: 'function';

IF: 'if';

IMPORT: 'import';

INT: 'int';

LOCK: 'lock';

NAMESPACE: 'namespace';

STR: 'str';

SYSFLAG: 'sysflag';

SWITCH: 'switch';

RETURN: 'return';

TALK: 'talk';

TRUE: 'true';

UNLESS: 'unless';

WHILE: 'while';

ScopedIdentifier
    : Identifier ('::' Identifier)+
    ;

// Must be defined after keywords
Identifier
    : Nondigit (Nondigit | Digit)*
    ;

// Fragments
fragment Nondigit
    : [a-zA-Z_]
    ;

fragment Digit
    : [0-9]
    ;


// Comparators
fragment EQ: 'EQ' | '==' ;

fragment NE: 'NE' | '!=' ;

fragment LT: 'LT' | '<' ;

fragment GT: 'GT' | '>' ;

fragment LE: 'LE' | '<=' ;

fragment GE: 'GE' | '>=' ;