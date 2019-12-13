import math
import random
import re
import sys
import time


# by Erik Osheim
#
# This module uses a recursive descent, LL1 parser to generate a Code object
# for the given input. Code objects are pure expressions whose behavior can
# only be controlled via a dictionary of strings-to-numbers provided to run.
#
# Syntax:
#
# * decimal numbers (e.g. 3, 4.52)
# * simple names (foo, qux13).
# * built-in constants: pi, e, i
# * arithmetic operators: + - * / % // ^ !
# * parenthesis and absolute value: (2 + 3) * |4 - x|
# * built-in functions:
# abs, ceil, cos, degrees, floor, int, log, log10,
# log2, max, min, radians, round, sin, tan
#


# Expression cache. Expressions get compiled into Code objects; we store the 
# Code objects here for expressions that we've seen before.
_cache = {}


## Given an input expression string, parse it and create a Code object (or
# just return the cached Code object if it already exists).
def prepare(expressionString):
    global _cache
    if expressionString not in _cache:
        _cache[expressionString] = Code.gen(Parser(expressionString).parse())
    return _cache[expressionString]


## Given an input expression string and a dictionary that maps variable names
# to their values, return the evaluated expression with those variables.
def run(expressionString, varToValue = {}):
    # Hack: coerce non-string inputs into strings. The most likely scenario
    # here is that we were asked to interpret a bare number.
    if not isinstance(expressionString, str) and not isinstance(expressionString, unicode):
        expressionString = str(expressionString)
    return prepare(expressionString).run(varToValue)


## Clear the expression cache. 
def flush():
    global _cache
    _cache = {}



# Everything below this point is the actual parser implementation; if you just
# want to use the module and don't care how it works then you don't need to 
# look at any of this.



## A single token in the parsed expression
class Lexeme(object):
    def __init__(self, name, pos, data):
        self.name = name
        self.pos = pos
        self.data = data


    def __unicode__(self):
        return 'Lexeme(%r, %d, %r)' % (self.name, self.pos, self.data)



## The Lexer turns an input string of characters into a series of Lexemes.
class Lexer(object):
    def __init__(self, data):
        self.data = data
        self.lexemes = []


    ## Parse out identifiers (variable names, built-in functions).
    def lexid(self, i):
        j = i + 1
        while j < len(self.data) and self.data[j].isalnum():
            j += 1
        self.lexemes.append(Lexeme('id', i, self.data[i:j]))
        return j


    ## Parse out numerical lexemes.
    def lexnum(self, i):
        j = i + 1
        while j < len(self.data) and self.data[j].isdigit():
            j += 1
        k = j
        if k < len(self.data) and self.data[k] == '.':
            k += 1
            while k < len(self.data) and self.data[k].isdigit():
                k += 1
        if k > j + 1:
            self.lexemes.append(Lexeme('num', i, self.data[i:k]))
            return k
        else:
            self.lexemes.append(Lexeme('num', i, self.data[i:j]))
            return j


    ## Generate the lexemes for our expression string.
    def lex(self):
        i = 0
        while i < len(self.data):
            c = self.data[i]
            if c.isspace():
                i += 1
            elif c.isalpha():
                i = self.lexid(i)
            elif c.isdigit():
                i = self.lexnum(i)
            elif c == '/' and self.data[i:i + 2] == '//':
                # Integer division.
                self.lexemes.append(Lexeme('//', i, '//'))
                i += 2
            else:
                # No special processing needed; the lexeme is a single
                # character long.
                self.lexemes.append(Lexeme(c, i, c))
                i += 1
        # End-of-expression lexeme.
        self.lexemes.append(Lexeme('$', i, None))
        return self.lexemes



## Exprs are symbological representations of mathematical expressions.
class Expr(object):
    def __init__(self, operator, *args):
        self.operator = operator
        self.args = args

        
    def __unicode__(self):
        return 'Expr(%r, %r)' % (self.operator, self.args)


    ## Represent the Expr as a Lisp-style expression,
    # e.g. "(+ 4 6)" for "4 + 6"
    def lisp(self):
        if self.operator == 'num':
            return self.args[0]
        elif self.operator == 'id':
            return self.args[0]
        elif self.operator == 'apply':
            return '(%s %s)' % (self.args[0], ' '.join([a.lisp() for a in self.args[1:]]))
        elif self.args:
            return '(%s %s)' % (self.operator, ' '.join([a.lisp() for a in self.args]))
        else:
            return self.operator



class Parser(object):
    isDebugOn = False


    def error(self):
        if self.isDebugOn:
            raise Exception("parse error at %r" % self.cur)
        else:
            raise Exception("parse error at %r (byte %d)" % (self.cur.data, self.cur.pos))


    def __init__(self, data):
        self.lexer = Lexer(data)


    def next(self):
        self.k += 1
        self.cur = self.lexemes[self.k]


    def parse(self):
        self.k = 0
        self.lexemes = self.lexer.lex()
        self.cur = self.lexemes[0]
        return self.parseP()


    def lxin(self, names):
        return self.cur.name in names


    pnames = set(['num', 'id', '(', '|', '-'])
    def parseP(self):
        return self.parseE1()


    def parseEx(self, names, f1, f2, right=False):
        lhs = f1()
        lst = f2()
        if not lst:
            return lhs
        elif right:
            lst = [lhs] + lst
            expr = lst[-1]
            i = len(lst) - 3
            while i >= 0:
                expr = Expr(lst[i + 1], lst[i], expr)
                i -= 2
            return expr
        else:
            expr = lhs
            i = 0
            while i < len(lst) - 1:
                expr = Expr(lst[i], expr, lst[i + 1])
                i += 2
            return expr


    def parseE1(self):
        return self.parseEx(self.pnames, self.parseE2, self.parseE1_)


    def parseE2(self):
        return self.parseEx(self.pnames, self.parseE3, self.parseE2_)


    dash = set(['-'])
    e3names = set(['num', 'id', '(', '|'])
    def parseE3(self):
        if self.cur.name == '-':
            self.next()
            expr = self.parseE3()
            return Expr('-', expr)
        else:
            return self.parseE4()


    def parseE4(self):
        return self.parseEx(self.e3names, self.parseE5, self.parseE4_, right=True)


    def parseE5(self):
        expr = self.parseE6()
        if self.parseE5_() is None:
            return expr
        else:
            return Expr('!', expr)


    lpar = set(['('])
    pipe = set(['|'])
    rpar = set([')'])
    def parseE6(self):
        c = self.cur
        if c.name == 'num':
            self.next()
            return Expr('num', c.data)
        elif c.name == 'id':
            self.next()
            a = self.parseA()
            if a is None:
                return Expr('id', c.data)
            else:
                return Expr('apply', c.data, *a)
        elif c.name == '(':
            self.next()
            e1 = self.parseE1()
            if self.lxin(self.rpar):
                self.next()
                return e1
            else:
                self.error()
        elif c.name == '|':
            self.next()
            e1 = self.parseE1()
            if self.lxin(self.pipe):
                self.next()
                return Expr('abs', e1)
            else:
                self.error()
        else:
            self.error()


    anames = set(['!', '$', '^', '*', '/', '//', '%', '+', '-', '#', ')', '|', ','])
    def parseA(self):
        if self.lxin(self.lpar):
            self.next()
            ll = self.parseL()
            if self.lxin(self.rpar):
                self.next()
                return ll
            else:
                self.error()
        else:
            return None


    lnames = set(['num', 'id', '(', '|', '-'])
    def parseL(self):
        e1 = self.parseE1()
        l_ = self.parseL_()
        if l_ is None:
            return [e1]
        else:
            return [e1] + l_


    comma = set([','])
    def parseL_(self):
        if self.lxin(self.comma):
            self.next()
            e1 = self.parseE1()
            l_ = self.parseL_()
            if l_ is None:
                return [e1]
            else:
                return [e1] + l_
        else:
            return None


    def parseEx_(self, names, skips, f1):
        if self.lxin(names):
            c = self.cur
            self.next()
            lhs = f1()
            lst = self.parseEx_(names, skips, f1)
            return [c.name, lhs] + lst
        else:
            return []


    e1_names = set(['+', '-', '#'])
    e1_skips = set([')', '|', ',', '$'])
    def parseE1_(self):
        return self.parseEx_(self.e1_names, self.e1_skips, self.parseE2)


    e2_names = set(['*', '/', '//', '%'])
    e2_skips = set(['+', '-', '#', '$', ')', '|', ','])
    def parseE2_(self):
        return self.parseEx_(self.e2_names, self.e2_skips, self.parseE3)


    e4_names = set(['^'])
    e4_skips = set(['*', '/', '//', '%', '$', '+', '-', '#', ')', '|', ','])
    def parseE4_(self):
        #return self.parseEx_(self.e4_names, self.e4_skips, self.parseE5)
        if self.cur.name == '^':
            self.next()
            #lhs = self.parseE5()
            lhs = self.parseE3()
            lst = self.parseE4_()
            return ['^', lhs] + lst
        else:
            return []


    bang = set(['!'])
    e5names = set(['^', '$', '*', '/', '//', '%', '+', '-', '#', ')', '|', ','])
    def parseE5_(self):
        if self.lxin(self.bang):
            self.next()
            if self.parseE5_() is None:
                return '!'
            else:
                return None
        else:
            return None



class Code(object):
    # semi-private. you should probably not build these by-hand.
    def __init__(self, f, names):
        "Construct a Code instance from function 'f' and a list 'names'."
        self.f = f
        self.names = names

    # public
    def run(self, kw):
        "Run the given Code instance using the dictionary 'kw'."
        return self.f(kw)

    # semi-private. requires knowledge of the AST structure.
    @classmethod
    def gen(cls, e):
        "Generate a Code instance given a parse tree 'e'."
        if e.operator == 'num':
            if '.' in e.args[0]:
                n = float(e.args[0])
            else:
                n = int(e.args[0])
            return cls(lambda kw: n, [])
        elif e.operator == 'id':
            s = e.args[0]
            if s == 'e':
                return cls(lambda kw: math.e, [])
            elif s == 'pi':
                return cls(lambda kw: math.pi, [])
            elif s == 'i':
                return cls(lambda kw: 1j, [])
            else:
                return cls(lambda kw: kw[s], [s])
        elif e.operator == '+':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: lhs.run(kw) + rhs.run(kw), names)
        elif e.operator == '-':
            lhs = Code.gen(e.args[0])
            if len(e.args) == 1:
                return cls(lambda kw: -lhs.run(kw), lhs.names)
            else:
                rhs = Code.gen(e.args[1])
                names = lhs.names + rhs.names
                return cls(lambda kw: lhs.run(kw) - rhs.run(kw), names)
        elif e.operator == '#':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: sum([random.randint(1, rhs.run(kw)) for i in xrange(lhs.run(kw))]), names)
        elif e.operator == '*':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: lhs.run(kw) * rhs.run(kw), names)
        elif e.operator == '/':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: float(lhs.run(kw)) / rhs.run(kw), names)
        elif e.operator == '%':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: lhs.run(kw) % rhs.run(kw), names)
        elif e.operator == '//':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: lhs.run(kw) // rhs.run(kw), names)
        elif e.operator == '^':
            lhs = Code.gen(e.args[0])
            rhs = Code.gen(e.args[1])
            names = lhs.names + rhs.names
            return cls(lambda kw: lhs.run(kw) ** rhs.run(kw), names)
        elif e.operator == '!':
            lhs = Code.gen(e.args[0])
            return cls(lambda kw: math.factorial(lhs.run(kw)), lhs.names)
        elif e.operator == 'abs':
            lhs = Code.gen(e.args[0])
            return cls(lambda kw: abs(lhs.run(kw)), lhs.names)
        elif e.operator == 'apply':
            fn = e.args[0]
            if fn == 'abs':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: abs(lhs.run(kw)), lhs.names)
            elif fn == 'ceil':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.ceil(lhs.run(kw)), lhs.names)
            elif fn == 'cos':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.cos(lhs.run(kw)), lhs.names)
            elif fn == 'degrees':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.degrees(lhs.run(kw)), lhs.names)
            elif fn == 'floor':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.floor(lhs.run(kw)), lhs.names)
            elif fn == 'int':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: int(lhs.run(kw)), lhs.names)
            elif fn == 'log':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.log(lhs.run(kw)), lhs.names)
            elif fn == 'log10':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.log10(lhs.run(kw)), lhs.names)
            elif fn == 'log2':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.log(lhs.run(kw), 2), lhs.names)
            elif fn == 'max':
                args = [Code.gen(arg) for arg in e.args[1:]]
                names = []
                for arg in args: names.extend(arg.names)
                return cls(lambda kw: min([a.run(kw) for a in args]), names)
            elif fn == 'min':
                args = [Code.gen(arg) for arg in e.args[1:]]
                names = []
                for arg in args: names.extend(arg.names)
                return cls(lambda kw: min([a.run(kw) for a in args]), names)
            elif fn == 'radians':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.radians(lhs.run(kw)), lhs.names)
            elif fn == 'round':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: round(lhs.run(kw)), lhs.names)
            elif fn == 'sin':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.sin(lhs.run(kw)), lhs.names)
            elif fn == 'tan':
                lhs = Code.gen(e.args[1])
                return cls(lambda kw: math.tan(lhs.run(kw)), lhs.names)
            else:
                raise Exception("function %r is not defined" % e.args[0])
        else:
            raise Exception("can't handle %r" % e)



# Calculator Grammar:
#
# non-terminal productions
# P -> E1
# E1 -> E2 E1_
# E1_ -> + E2 E1_ | - E2 E1_ | e
# E2 -> E3 E2_
# E2_ -> * E3 E2_ | / E3 E2_ | // E3 E2_ | % E3 E2_ | e
# E3 -> E4 | - E4
# E4 -> E5 E4_
# E4_ -> ^ E5 E4_ | e
# E5 -> E6 E5_
# E5_ -> ! E5_ | e
# E6 -> num | id A | ( E1 ) | bar E1 bar
# A -> ( L ) | e
# L -> E1 L_
# L_ -> , E1 L_ | e
#
# terminal definitions
# bar = "|"
# id = [a-zA-Z][a-zA-Z0-9]*
# num = (0|[1-9][0-9]*)(\.[0-9]+)?
# (plus other literal characters, e.g. +)
#
# first sets
# Fi(A) = ( e
# Fi(E6) = num id ( bar
# Fi(E5_) = ! e
# Fi(E5) = Fi(E6) = num id ( bar
# Fi(E4_) = ^ e
# Fi(E4) = Fi(E5) = num id ( bar
# Fi(E3) = Fi(E4) - = num id ( bar -
# Fi(E2_) = * / // % e
# Fi(E2) = Fi(E3) = num id ( bar -
# Fi(E1_) = + - e
# Fi(E1) = Fi(E2) = num id ( bar -
# Fi(P) = Fi(E1) = num id ( bar -
# Fi(L) = Fi(E1) = num id ( bar -
# Fi(L_) = , e
#
# follow sets
# Fo(E1) = ) bar Fi(L_) Fo(L) = ) bar , e
# Fo(E1_) = Fo(E1) = ) bar , e
# Fo(E2) = Fi(E1_) Fo(E1) = + - e ) bar ,
# Fo(E2_) = Fo(E2) = + - e ) bar ,
# Fo(E3) = Fi(E2_) Fo(E2) = * / // % e + - ) bar ,
# Fo(E4) = Fo(E3) = * / // % e + - ) bar ,
# Fo(E4_) = Fo(E4) = * / // % e + - ) bar ,
# Fo(E5) = Fi(E4_) Fo(E4) = ^ e * / // % + - ) bar ,
# Fo(E5_) = Fo(E5) = ^ e * / // % + - ) bar ,
# Fo(E6) = Fi(E5_) Fo(E5) = ! e ^ * / // % + - ) bar ,
# Fo(A) = Fo(E6) = ! e ^ * / // % + - ) bar ,
# Fo(L) = )
# Fo(L_) = Fo(L) = )
#
# parse table (non-terminal, list of terminals = production)
# P num id ( bar - = E1
# E1 num id ( bar - = E2 E1_
# E1_ + - = [c] E2 E1_
# E1_ ) bar , $ = e
# E2 num id ( bar - = E3 E2_
# E2_ * / // % = [c] E3 E2_
# E2_ + - $ ) bar , = e
# E3 - = - E3
# E3 num id ( bar = E4
# E4 num id ( bar = E5 E4_
# E4_ ^ = ^ E5 E4_
# E4_ * / // % $ + - ) bar , = e
# E5 num id ( bar = E6 E5_
# E5_ ! = ! E5_
# E5_ ^ $ * / // % + - ) bar , = e
# E6 num = num
# E6 id = id A
# E6 ( = ( E1 )
# E6 bar = bar E1 bar
# A ( = ( L )
# A ! e ^ * / // % + - ) bar , = e
# L num id ( bar - = E1 L_
# L_ , = , E1 L_
# L_ ) = e
