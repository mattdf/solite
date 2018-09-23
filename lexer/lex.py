#!/usr/bin/python3

from pypeg2 import *
from sys import argv, exit
import inspect
import pprint

pp = pprint.PrettyPrinter(indent=4)

class Type(Keyword):
    grammar = Enum( K("int256"), K("uint256"), K("address"), K("string"), K("bytes") )

class IfElse(List):
    pass

class ForLoop(List):
    pass

class WhileLoop(List):
    pass

class SwitchCase(List):
    pass

class Control(List):
    grammar = [IfElse, ForLoop, WhileLoop, SwitchCase]

class BinOp(str):
    grammar = re.compile(r'\+|\-|\>|\<|\>=|\<=|==|\!=')
    #grammar = ["+","-","/","*",">>","<<","%","<",">",">=","<=","=="]

class Prefix(str):
    grammar = re.compile(r'\!|\~')

class Expr(List):
    pass

class Parens(List):
    pass

class VarDecl(Namespace):
    pass

class Number(str):
    grammar = re.compile(r"\d+")

class Hex(str):
    grammar = re.compile(r"0x[A-Fa-f0-9]+")

class String(str):
    grammar = re.compile(r'"(?:[^\\"]|\\.)*"')

class Array(List):
    grammar = name(), "[", Expr, "]"

class Variable(List):
    grammar = attr("name", re.compile(r"[A-Za-z0-9]+"))

class Parameter:
    grammar = attr("typing", Type), name()

class Parameters(Namespace):
    grammar = optional(csl(Parameter))

class Argument(List):
    grammar = Expr

class Arguments(List):
    grammar = optional(csl(Argument))

class Assignment(Namespace):
    grammar = attr("name", [Array, Variable]), "=", attr("value", Expr), ";" 

class Call(Namespace):
    grammar = optional(attr("assign", word), "="), name(), "(", attr("args", Arguments), ")"

class Return(List):
    grammar = "return", some(attr("rval", Expr)), ";"

block = "{", maybe_some([Control, Return, VarDecl, Assignment, Call]), "}"

class Function(List):
    grammar = "function", "(", attr("typing", Type), ")", name(), "(", attr("params", Parameters),")", block

class Contract(List):
    grammar = "contract", name(), "{", maybe_some([VarDecl, Function]), "}"

class ElseIf(List):
    grammar = "else", "if", "(", attr("econd", Expr), ")", block

el = "else", block

IfElse.grammar = "if", "(", attr("cond", Expr), ")", attr("body", block), attr("ifel", maybe_some(ElseIf)), optional(attr("el", el))
ForLoop.grammar = "for", "(", attr("init", Assignment), ";", attr("cond", Expr), ";", attr("step", [Assignment, Expr]), ")", block
WhileLoop.grammar = "while", "(", attr("cond", Expr), ")", attr("body", block)
SwitchCase.grammar = "switch", "etc"

Expr.grammar = maybe_some(Prefix), attr("left", [
    Number, Hex, String, Parens, Array, Variable, Call
]), maybe_some(BinOp, Expr)

Parens.grammar = "(", some(Expr), ")"

VarDecl.grammar = Type, optional(attr("isarray", ("[", optional(Number) ,"]"))), name(), maybe_some("=", attr("value", Expr)), ";"

