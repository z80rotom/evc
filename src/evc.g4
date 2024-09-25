
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
    |  variableDefinition ';'
    |  namespace
    |  import_
    |  fromImport
    ;

import_
    :   IMPORT Identifier ';'
    ;

fromImport
    :   FROM Identifier IMPORT fromImportRhs ';'
    ;

fromImportRhs
    : '{' Identifier (',' Identifier)*  '}'
    | Identifier
    | WILDCARD
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
    :   COMMAND Identifier '(' funcArgList ')' ('->' type)? ':' number ';'
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
// End animation


// Functions
function
    : functionSpecifier? FUNCTION Identifier '(' funcArgList ')' ('->' type)? '{' block '}'
    ;

functionSpecifier
    :   COMMON
    |   ENTRY
    ;

funcArgList
    : funcArg?
    | funcArg (',' funcArg)+
    ;

// Used by commands too which is the only place I would recommend to have to use the return storage specifier.
funcArg
    : type Identifier (':' funcArgStorage)?
    ;

funcArgStorage
    : number
    | RETURN
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
    | contextBlock
    | variableAssignment ';'
    | variableDefinition ';'
    | functionCall ';'
    | return ';'
    | break ';'
    ;

contextBlock
    : WITH Identifier '(' funcCallArgList ')' '{' block '}'
    ;

switchBlock
    : SWITCH '(' ifExpr ')' '{' caseBlock+ '}'
    ;

caseBlock
    : CASE (ScopedIdentifier | Identifier | number) ':' block
    | DEFAULT ':' block
    ;

break
    :   BREAK
    ;

return
    :   RETURN  (Identifier | number)?
    ;

forBlock
    : FOR '(' variableDefinition ';' ifExpr ';'  ')' '{' block '}'
    ;

whileBlock
    : WHILE '(' ifExpr ')' '{' block '}'
    ;

// TODO: These need to support tuple assignments
variableDefinition
    :   CONST? type Identifier (':' number)? ('=' variableRightHandAssignment)?
    ;

variableAssignment
    :   (ScopedIdentifier | Identifier) assignmentOperator variableRightHandAssignment
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
    | ScopedIdentifier
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

// Must be lowercase or suddenly it stops being able to understand assignment at all
// God damn I need to get better at antlr4
assignmentOperator
    : '='
    | '+='
    | '-='
    ;

// Adding ScopedIdentifier as a potential type breaks the unless lowercase
type
    : FLAG
    | SYSFLAG
    | INT
    | FLOAT
    | BOOL
    | STR
    | ScopedIdentifier
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

WILDCARD: '*';

WITH: 'with';

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