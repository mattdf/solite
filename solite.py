#!/usr/bin/python3

from lexer.lex import *
import binascii

import _sha3
sha3_256 = lambda x: _sha3.sha3_256(x).digest()

sha3_count = [0]

def sha3(seed):
    sha3_count[0] += 1
    return sha3_256(seed)

def die_error(msg):
    print(msg)
    exit(1);

class Stack:

    def __init__(self, vars, fname="", parent=None):
        self.parent = parent
        self.childs = dict()
        self.memmap = dict()
        self.lookup = dict()
        self.retAddr = 0
        self.asm = []
        self.memoffset = 1
        if parent is not None:
            self.parent.childs[fname] = self
            self.memoffset = parent.memoffset
        for varname, expr in vars.items():
            if hasattr(expr, 'value'):
                e = self.evalExpr(expr.value)
            else:
                e = "0"
            self.memmap[varname] = self.memoffset*32
            self.lookup[varname] = mload(str(self.memoffset*32))
            self.asm.append(mstore(str(self.memoffset*32), e))
            self.memoffset += 1

    def allocateReturn(self, type):
        self.memoffset += 1
        self.retAddr = self.memoffset-1

    def allocateParams(self, p):
        code = []
        cdli = 1
        for pname, pexpr in p.items():
#            pp.pprint(pexpr.typing)
            self.memmap[pname] = self.memoffset*32
            self.lookup[pname] = mload(str(self.memoffset*32))
            c = mstore(str(self.memoffset*32), cdl(str(cdli*32)))
            code.append(c)
            self.memoffset += 1
            cdli += 1
        return code

    def processControl(self, c):
        cd = ""
        for st in c:
            if isinstance(st, IfElse):
                cond = self.evalExpr(st.cond)
                body = self.processBody(st.body)
                if len(st.ifel) > 0:
                    for x in st.ifel:
                        print(x.econd)
                if hasattr(st, 'el'):
                    cd = Sexp(["IF", cond, seq(body), seq(self.processBody(st.el))])
                else:
                    cd = Sexp(["WHEN", cond, seq(body)])
            elif isinstance(st, WhileLoop):
                cond = self.evalExpr(st.cond)
                body = self.processBody(st.body)
                cd = Sexp(["WHILE", cond, seq(body)])
        return cd

    def processBody(self, st):
        codegen = []
        for x in st:
            if isinstance(x, VarDecl):
                b = self.evalExpr(x.value)
#                codegen.append(b)
            if isinstance(x, Return):
                rval = self.evalExpr(x.rval)
                codegen.append(mstore(str(self.retAddr*32), rval))
                b = freturn(str(self.retAddr*32), "32")
                codegen.append(b)
            if isinstance(x, Control):
                c = self.processControl(x)
                codegen.append(c)
            if isinstance(x, Assignment):
                c = self.evalExpr(x.value)
                n = self.resolveStore(x.name.name) 
                s = mstore(str(n), c)
                codegen.append(s)
        return codegen

    def resolveStore(self, sym):
        bucket = self
        while bucket is not None:
            try:
                return bucket.memmap[sym]
            except:
                bucket = bucket.parent


    def evalExpr(self, expr):
        l = expr.left
        if len(expr) > 1:
            op = expr[0]
            r = expr[1]
            rx = self.evalExpr(r)
            return Sexp([opMap[op], str(self.evalAtom(l)), str(rx)])
        else:
            return str(self.evalAtom(l))


    def evalAtom(self, a):
        if isType(a, [Number, Hex, String]):
            return a
        if isType(a, [Variable]):
            return self.resolveSymbol(a.name) 
        if isType(a, [Parens]):
            return self.evalExpr(a[0])

    def resolveSymbol(self, sym):
        bucket = self
        while bucket is not None:
            try:
                return bucket.lookup[sym]
            except:
                bucket = bucket.parent



varSpace = OrderedDict()

funSpace = OrderedDict()

opMap = {
    "+": "ADD",
    "-": "SUB",
    "<": "LT",
    ">": "GT",
    "==":"EQ"
}

typeMap = {
    "uint256": 1,
    "int256": 1,
    "address": 1
}

def isType(x, l):
    for t in l:
        if isinstance(x, t):
            return True
    return False


def Sexp(l):
    return '(' + " ".join(l) + ')'


def mstore(a, x):
    return Sexp(["MSTORE", a, x])


def mload(a):
    return Sexp(["MLOAD", a])


def freturn(a, x):
    return Sexp(["RETURN", a, x])

def cdl(a):
    return Sexp(["CALLDATALOAD", a])

def seq(body):
    return Sexp(["SEQ", "\n".join(body)])


def fillMap(map, st, cl):
    for lvl1 in st:
        if isinstance(lvl1, cl):
            if lvl1.name in map:
                die_error("Redeclaration error: name `%s` previously declared" % (lvl1.name))
            else:
                map[lvl1.name] = lvl1

def retMap(st, cl):
    map = OrderedDict()
    for lvl1 in st:
        if isinstance(lvl1, cl):
            if lvl1.name in map:
                die_error("Redeclaration error: name `%s` previously declared" % (lvl1.name))
            else:
                map[lvl1.name] = lvl1
    return map

def newJmpLabel(fn):
    return Sexp(["define", "fn_" + fn, Sexp(["label-counter"])])


def genFuncHash(fname):
    return '0x' + binascii.hexlify(sha3(fname))[0:8].decode("utf-8")


def genFuncTable(funcs):
    code = []
    for fname, decl in funcs.items():
        f = decl.name.name.encode("utf-8")
        faddr = genFuncHash(f) 
        code.append(newJmpLabel(faddr))
    return "\n".join(code)


def descend(obj):
    codegen = []

    fillMap(varSpace, obj, VarDecl)
    fillMap(funSpace, obj, Function)

    print(genFuncTable(funSpace))

    topStack = Stack(varSpace)
    codegen.append("\n".join(topStack.asm))

    codegen.append(Sexp(["CALLDATALOAD", "0"]))
    codegen.append(Sexp(["DIV", Sexp(["SWAP1"]), "0x100000000000000000000000000000000000000000000000000000000"]))


    for fname, decl in funSpace.items():
        f = decl.name.name.encode("utf-8")
        faddr = genFuncHash(f) 
        codegen.append(Sexp(["EQ", faddr, Sexp(["DUP1"])]))
        codegen.append(Sexp(["mark-jump", "fn_" + faddr ]))
        codegen.append(Sexp(["JUMPI"]))
    codegen.append(Sexp(["STOP"]))
    for fname, decl in funSpace.items():
        t = decl.typing
        p = decl.params
        f = decl.name.name.encode("utf-8")
        fstack = Stack(retMap(decl, VarDecl), fname, topStack)
        fstack.allocateReturn('type')
        faddr = genFuncHash(f) 
        codegen.append(Sexp(["mark-dest", "fn_" + faddr]))
        codegen.append("\n".join(fstack.asm))
        codegen.append("\n".join(fstack.allocateParams(p)))
        codegen.append("\n".join(fstack.processBody(decl)))
    print(Sexp(["START", "\n".join(codegen)]))


if __name__ == "__main__":
    if len(argv) < 2:
        print("usage: ./solite <file>")
        exit(0)

    sol_fn = argv[1]

    with open(sol_fn, "r", encoding="utf-8") as cont:
        code = cont.read()

    contract = parse(code, Contract)

    descend(contract)
