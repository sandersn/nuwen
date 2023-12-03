import util
import random
class Symbol:
    """A node in the tree of a CFG rule.

    CFG rules are stored like so:
    The topmost Symbol is a parenthesis, which has for children a list of alternates.
    Each alternate contains the actual Symbols which comprise that choice.
    For example: A #B# | #C# D will become
    (PAREN 
            (ALT (SYM A) (LIT B))
            (ALT (LIT C) (SYM D)))
    Parentheses, alternates, question marks, and stars are compound types and have
    children. However, parentheses and alternates must be nested in the above described manner.
    Symbols represent a non-terminal and literals represent terminals.
    Here is a more complicated example:
    A [B (C | D)] | ({B [C]} | A) | A
    (PAREN
            (ALT (QUES (SYM B) (PAREN (ALT (SYM C))
                                                                                       (ALT (SYM D)))))
            (ALT (PAREN (ALT (STAR (SYM B) (QUES (SYM C))))
                                              (ALT (SYM A))))
            (ALT (SYM A)))
    TODO:Figure a better way to make __repr__ reuse most of __str__'s code"""
    LIT=0
    SYM=1
    STAR=2
    QUES=3
    PAREN=4
    ALT=5
    def __init__(self, type=LIT, sym='', children=[]):
        self.children=children[:]#the children of this rewrite rule ( [:] creates a shallow copy in Python 2.1)
        self.sym = sym #the symbol associated with this rewrite rule
        self.type = Symbol.LIT
        if Symbol.LIT <= type <= Symbol.ALT:
            self.type = type
    def __str__(self):
        """special method produces string representation (like Java's .toString())"""
        strRepr = {Symbol.LIT:lambda sym: "#"+sym.sym+"#",
                           Symbol.SYM:lambda sym: sym.sym,
                           Symbol.STAR:lambda sym: "{",
                           Symbol.QUES:lambda sym: '[',
                           Symbol.PAREN:lambda sym: "(",
                           Symbol.ALT:lambda sym: ''}
        def joinChildren(node2, children2):
            if node2=='(':
                return node2 + ' | '.join(children2) + util.bracematch.get(node2,'')
            else:
                return node2 + ' '.join(children2) + util.bracematch.get(node2,'')
        return util.buildTree(self, lambda x: strRepr[x.type](x), lambda x: x.children, joinChildren)
    def __repr__(self):
        reprRepr = {Symbol.LIT:lambda sym: "#"+sym.sym+"#",
                           Symbol.SYM:lambda sym: sym.sym,
                           Symbol.STAR:lambda sym: "{",
                           Symbol.QUES:lambda sym: '[',
                           Symbol.PAREN:lambda sym: "(",
                           Symbol.ALT:lambda sym: "<"}
        def joinChildren(node2, children2):
            if node2=='(':
                return node2 + ' | '.join(children2) + util.bracematch.get(node2,'')
            else:
                return node2 + ' '.join(children2) + util.bracematch.get(node2,'')
        return "(%s -> %s)"  % (self.sym,util.buildTree(self, lambda x: reprRepr[x.type](x), lambda x: x.children, joinChildren))
    def __eq__(self,other):
        """This is the grand poobah correct version. It doesn't work right without. It is likely slow, but boy is it *correct*!! Wow!"""
        if other is None:
            return 0
        else:
            return self.sym==other.sym and self.type==other.type and self.children==other.children
    def add(self, x):
        """Happy alias for list append (copied from Java version)"""
        self.children.append(x)
    def addAll(self, l):
        """Happy alias for list extend (copied from Java version)"""
        self.children.extend(l)
    def isLit(self):
        return self.type==Symbol.LIT
    def isAllLiterals(self):
        """whether all children are literals(returns true for empty list)"""
        return not len(filter(lambda x: x.type!=Symbol.LIT, self.children))
    def isAllSimple(self):
        """whether all children are non-nesteds(returns true for empty list)"""
        return not len(filter(lambda x: x.type!=Symbol.LIT and x.type!=Symbol.SYM, self.children))
    def toSimple(self, grammar):
        """{str:Symbol}!->None -- Convert all extended BNF features of this symbol to simple BNF.

        Requires pointer to grammar because STAR conversion requires generating new grammar entries.
        How conversions are handled:
                PAREN: (A->a (b | c) d) -> (A-> a b d | a c d)
                QUES: (A->a [b] c) -> (A->a c | a b c)
                STAR: (A->a {b} c) -> (A->a c | a GENSYM c; GENSYM->b | b GENSYM)
        More complicated examples:
                (a [b [c]] d) -> (a d | a b d | a b c d)
                (a {(b | c)} d) -> (a G d | a d), where G is (b | c | b G | c G)
                (a (b | (c | d)) e) -> (a b e | a c e | a d e)"""
        return Symbol(Symbol.PAREN, '', util.filter_dups(self.__toSimple(grammar)))
    def __toSimple(self, grammar):
        """Private recursive worker of public toSimple (which just packages this method in usable form)"""
        if self.type==Symbol.QUES:
            return [[]]+[Symbol(Symbol.ALT, '', _flatten2D(p)) for p in util.permutations([ch.__toSimple(grammar) for ch in self.children])]
        elif self.type==Symbol.STAR:
            gen=_gensym(grammar, 'gen')
            alts=util.permutations([ch.__toSimple(grammar) for ch in self.children])
            alts+=[alt+[Symbol(Symbol.SYM, gen)] for alt in alts]
            grammar[gen]=Symbol(Symbol.PAREN, '', [Symbol(Symbol.ALT, '', _flatten2D(alt)) for alt in alts])
            return [[],Symbol(Symbol.SYM, gen)]
        elif self.type==Symbol.PAREN:
            choices=[]
            for alt in self.children:
                choices.extend([_flatten2D(p) for p in util.permutations([ch.__toSimple(grammar) for ch in alt.children])])
            return [Symbol(Symbol.ALT, '', ch) for ch in choices]
        else:#LIT | SYM
            return [self]
    def extractPOS(self):
        """None->[Symbol]  Return all literal symbols in the tree"""
        POS=[]
        if self.type==Symbol.LIT:
            POS.append(self.sym)
        for ch in self.children:
            POS.extend(ch.extractPOS())
        return POS
def gen_grammar(**grammar):
    """{str:str} -> {str:Symbol} : Convert a grammar with valid BNF strings to the equivalent symbol tree."""
    for sym in grammar.keys():
        grammar[sym] = gen_symbol(Symbol(Symbol.PAREN, sym), grammar[sym].split())
    return grammar
def gen_symbol(parent, symbols):
    """Symbol*[str]->Symbol | [str] -- Convert a grammar rule from string list into a Symbol tree

    This is an old algorithm--now that Python has lexical scoping, I would probably write it somewhat
    differently. I wrote this at the height of when Python was new to me, so I overused some of the
    flexibility of Python's dynamism without properly using its power for abstraction.
    """
    suparent = None
    if parent.type==Symbol.PAREN:
        #push everything up by one level (so suparent now tracks the PAREN)
        alt = Symbol(Symbol.ALT)
        parent.add(alt)
        suparent = parent
        parent = alt
    while len(symbols):
        sym = symbols.pop(0) #make like a queue and...never mind
        if sym=='{':
            star = Symbol(Symbol.STAR)
            parent.add(star)
            symbols = gen_symbol(star, symbols)
        elif sym=='}' and parent.type==Symbol.STAR:
            return symbols
        elif sym=='[':
            ques = Symbol(Symbol.QUES)
            parent.add(ques)
            symbols = gen_symbol(ques, symbols)
        elif sym==']' and parent.type==Symbol.QUES:
            return symbols
        elif sym=='(':
            paren = Symbol(Symbol.PAREN)
            parent.add(paren)
            symbols = gen_symbol(paren, symbols)
        elif sym==')' and (parent.type==Symbol.ALT or parent.type==Symbol.PAREN):
            return symbols
        elif sym=='|':
            alt = Symbol(Symbol.ALT)
            suparent.add(alt)
            parent = alt
        elif sym[0]==sym[-1]=="#":
            parent.add(Symbol(Symbol.LIT, sym[1:-1]))
        else:
            parent.add(Symbol(Symbol.SYM, sym))
    if suparent:
        return suparent
    else:
        return parent
def convertGrammarToSimple(grammar):
    """{str:Symbol}! -- Convert the given grammar destructively to Simple BNF form."""
    for sym in grammar.keys():
        grammar[sym]=grammar[sym].toSimple(grammar)
def extractAll(grammar):
    """{str:Symbol}->[str] -- return all LIT and SYM symbols from a grammar

    NOTE:This includes "#" as the end/beginning POS
    >>> extractAll(gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"))
    ['E', 'T', 'F', '+', '*', '(', ')', 'id', '#']
    """
    return grammar.keys() + util.flatten([grammar[x].extractPOS() for x in grammar]) + ["#"]
def _gensym(grammar, startName):
    """Returns a similar but different name by appending numbers to a starting name in a grammar."""
    offset=random.randrange(1000000)
    while startName+str(offset) in grammar.keys():
        offset=random.randrange(1000000)
    return startName+str(offset)
def _flatten2D(l):
    """A simple flattening algorithm to get rid of one level of [] and Symbol.ALT

    This function is used in the conversion from extended BNF to simple BNF.
    It can be this simple because it is called for every level of recursion in Symbol.toSimple
    I think I don't need the first clause of the elif because if x is not a list, then it must
    be a Symbol because the tree consists entirely of symbols. """
    m=[]
    for x in l:
        if isinstance(x,list):
            m+=x
        elif isinstance(x,Symbol) and x.type==Symbol.ALT:
            m+=x.children
        else:
            m.append(x)
    return m
def flatten(parent):
    """Symbol -> [[Symbol]...] Flattening algorithm assumes simple BNF, returns list of children in ALTs.

    This function is for public use *after* a grammar is in simple BNF form."""
    return [alt.children for alt in parent.children]
def product(fn, l):
    """fn*[]->int Product of a list. (Like summate)

    ***UNUSED***"""
    return reduce(lambda x,y:x*fn(y), n, 1)
def _test():
    import doctest, cfg
    doctest.testmod(cfg)
if __name__=='__main__':
    _test()
    #root = gen_symbol(Symbol(Symbol.PAREN), "#Is# ( Adj | Det ) NP VP #?# | #HELLOI!#".split())
    #root = gen_symbol(Symbol(Symbol.PAREN), "NP [ [ VP ] [ D E ] ] | #HI# #MOM#".split())
    #g={'S':root}
    #sroot = root.toSimple(g)
    #print sroot
    #print g
