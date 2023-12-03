"""lr.py -- LR parsing, with a generalised error repairing forward move algorithm and
a hand-crafted series of error-enhanced error routines.

See parse.py for higher-level parsing interface. However, if you want fine
control of an LR parser (eg to see the parse tables) the primary usage is as follows:
>>> #set up an example grammar
>>> import cfg
>>> grammar = cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#")
>>> #parse parses the tokens and returns the parse tree root
>>> root = parse('id * id + id'.split(), grammar, "E")
Generating items...
	1 / 6
	2 / 7
	3 / 8
	4 / 8
	5 / 9
	6 / 9
	7 / 10
	8 / 11
	9 / 12
	10 / 12
	11 / 12
	12 / 12
Generating table...
	0 / 12
	1 / 12
	2 / 12
	3 / 12
	4 / 12
	5 / 12
	6 / 12
	7 / 12
	8 / 12
	9 / 12
	10 / 12
	11 / 12
Generating items...
	1 / 6
	2 / 7
	3 / 8
	4 / 8
	5 / 9
	6 / 9
	7 / 10
	8 / 11
	9 / 12
	10 / 12
	11 / 12
	12 / 12
F->#id#
T->F
F->#id#
T->T #*# F
E->T
F->#id#
T->F
E->E #+# T
hoorah
>>> #retrieve returns a string representation of the parse (HTML version coming Soon :)
>>> retrieve(root, 'x * y + z'.split())
'E\\n   E\\n      T\\n         T\\n            F\\n               x (id)\\n         * (*)\\n         F\\n            y (id)\\n   + (+)\\n   T\\n      F\\n         z (id)\\n'
>>> #Or, if you want to generate just the parse tables:
>>> table = gen_table(grammar, "E") #current version displays progress to STDOUT
Generating items...
	1 / 6
	2 / 7
	3 / 8
	4 / 8
	5 / 9
	6 / 9
	7 / 10
	8 / 11
	9 / 12
	10 / 12
	11 / 12
	12 / 12
Generating table...
	0 / 12
	1 / 12
	2 / 12
	3 / 12
	4 / 12
	5 / 12
	6 / 12
	7 / 12
	8 / 12
	9 / 12
	10 / 12
	11 / 12
>>> goto = gen_goto(grammar, "E") #current version displays progress to STDOUT
Generating items...
	1 / 6
	2 / 7
	3 / 8
	4 / 8
	5 / 9
	6 / 9
	7 / 10
	8 / 11
	9 / 12
	10 / 12
	11 / 12
	12 / 12

Sets table to a dict of lr.Cell (indicating SHIFT, REDUCE, ACCEPT or ERROR)
that is indexed like so:
>>> table[10, "#"]
rT(0)

Which means reduce rule T, alternative 0.
TODO: finish this to be more complete
"""
import cfg #flatten, gen_grammar, Symbol, split
import util
import random
from parse_state import State
class Cell:
    """A cell in an LR parse table

    SHIFT cells store only an index into table
    REDUCE cells store a sym (string index) into a grammar and the index of the alternative inside that symbol
    ACCEPT cells store nothing
    ERROR cells store an error correction function, which sym points to
    """
    SHIFT = 0
    REDUCE = 1
    ACCEPT = 2
    ERROR = 3
    to_str = {SHIFT:'s%s', REDUCE:'r%s(%s)', ACCEPT:'a%s', ERROR:'e%s'}
    def __init__(self, type=ERROR, index=0, sym=None):
        """int*int*str -- initialise a new Cell

        (xor
          (is '(index the parse table row for SHIFT actions))
          (is '(index is the nth alternative in grammar[sym] for REDUCE actions)))
        ;oops. Pardon my Lisp. ^_^ """
        self.type = type #what type of action to take
        #only SHIFT or REDUCE
        self.index = index #an index into either table or grammar
        #only REDUCE
        self.sym=sym #tells which symbol in the grammar
    def __eq__(self, other):
        return self.type==other.type and self.index==other.index and self.sym==other.sym
    def __ne__(self, other):
        return self.type!=other.type or self.index!=other.index or self.sym!=other.sym
    def __repr__(self):
        if self.type==Cell.REDUCE:
            return Cell.to_str[self.type] % (self.sym, self.index)
        else:
            return Cell.to_str[self.type] % self.index
class Entry:
    """An entry in a LR parser driver stack"""
    def __init__(self, state=None, sym=None, children=None):
        """int*str*[] -- initialise a new Entry"""
        self.state = state #an int index to a State in the grammar table
        self.sym = sym #a str index to a Symbol in the grammar dict
        if not children:
            self.children = [] #pointer to other Entries, to form the parse tree
        else:
            self.children = children #pointer to other Entries, to form the parse tree
    def __eq__(self,other):
        return self.state==other.state and self.sym==other.sym #and self.children==other.children?
    def __repr__(self):
        return "|%s, %s|" % (self.state, self.sym)
    def __str__(self):
        return str(self.sym)
class ErrEntry:
    """An entry in a error recovering forward move LR parser driver stack"""
    def __init__(self, entries, children=()):
        """[Cell]*[ErrEntry] -- TODO:Think about making a good tree class"""
        self.entries = entries
        self.children = children
    def __eq__(self, other):
        return self.entries==other.entries and self.children==other.children
    def __repr__(self):
        return `self.entries`
class CanonState(State):
    """State used to build a canonical LR parse table"""
    def __init__(self, sym=cfg.Symbol(), progress=0, ahead=''):
        """Symbol*int*str -- maybe should be *[str] for generalised LR(k)"""
        State.__init__(self, sym, progress)
        self.ahead = ahead #the lookahead str.
        #Of course for LR(1), this should always be length 1, but in general I think
        #for LR(k) it is of length (k). Technically my simple generation code could use CanonState
        #with a length of 0 always, but that would be rather wasteful.
        #oops. On reflection, it could be that ahead should be [str], and the length should be zero.
        #either way, the current representation works for LR(1)...
    def __eq__(self, other):
        return State.__eq__(self, other) and self.ahead==other.ahead
    def __str__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce useful results."""
        return "%s, %s" % (State.__str__(self), self.ahead)
    def __repr__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce precise results."""
        return "%r[%r, %r]" % (self.sym,self.progress, self.ahead)
def parse(words, grammar, target="S", canonical=False):
    """[str]*{str:Symbol}*str->Entry -- return root of parse tree

    TODO:Get gen_tables to combine to do table.update(goto) since the keys are mutex anyway
    and it would make the code easier to write. eg change to:
    table = gen_tables(grammar, target)
    table.update(gen_goto(grammar, target)
    return lr_parse(words+["#"], grammar, table)
    
    since gen_table is dependent on gen_goto anyway, you just lose the gen_goto call.
    Note of course the requisite interface changes"""
    return lr_parse(words+["#"],
                   grammar,
                   gen_table(grammar,target, canonical),
                   gen_goto(grammar, target, canonical))
def gen_table(grammar, target="S", canonical=False):
    """{str:Symbol}!*str*bool->{(int,str):Cell} -- transform a BNF grammar into an LR parse table

    If canonical is true, a full canonical LR parser table is returned, otherwise a simple one.

    WARNING:For now, also augments grammar to include a (root -> (<target>)) Symbol. This
    will likely change in the future to shift the burden onto the caller as this function worms its
    way into the private sector instead of the public. tabun

	>>> x = gen_table(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E", False)
	Generating items...
		1 / 6
		2 / 7
		3 / 8
		4 / 8
		5 / 9
		6 / 9
		7 / 10
		8 / 11
		9 / 12
		10 / 12
		11 / 12
		12 / 12
	Generating table...
		0 / 12
		1 / 12
		2 / 12
		3 / 12
		4 / 12
		5 / 12
		6 / 12
		7 / 12
		8 / 12
		9 / 12
		10 / 12
		11 / 12
    >>> x = x.items() #this whole bit is a doctest workaround 
    >>> x.sort() #to circumvent the randomness of dicts
    >>> x
    [((0, '('), s4), ((0, 'id'), s5), ((1, '#'), a0), ((1, '+'), s6), ((2, '#'), rE(1)), ((2, ')'), rE(1)), ((2, '*'), s7), ((2, '+'), rE(1)), ((3, '#'), rT(1)), ((3, ')'), rT(1)), ((3, '*'), rT(1)), ((3, '+'), rT(1)), ((4, '('), s4), ((4, 'id'), s5), ((5, '#'), rF(1)), ((5, ')'), rF(1)), ((5, '*'), rF(1)), ((5, '+'), rF(1)), ((6, '('), s4), ((6, 'id'), s5), ((7, '('), s4), ((7, 'id'), s5), ((8, ')'), s11), ((8, '+'), s6), ((9, '#'), rE(0)), ((9, ')'), rE(0)), ((9, '*'), s7), ((9, '+'), rE(0)), ((10, '#'), rT(0)), ((10, ')'), rT(0)), ((10, '*'), rT(0)), ((10, '+'), rT(0)), ((11, '#'), rF(0)), ((11, ')'), rF(0)), ((11, '*'), rF(0)), ((11, '+'), rF(0))]

    But of course the dict below is what you will get when testing manually:
    {(10, '#'): rT(0), (8, '+'): s6, (8, ')'): s11, (10, ')'): rT(0), (10, '+'): rT(0), (10, '*'): rT(0), (7, 'id'): s5, (0, '('): s4, (2, ')'): rE(1), (2, '+'): rE(1), (2, '*'): s7, (2, '#'): rE(1), (5, '#'): rF(1), (3, '#'): rT(1), (0, 'id'): s5, (3, '*'): rT(1), (3, '+'): rT(1), (3, ')'): rT(1), (5, ')'): rF(1), (5, '*'): rF(1), (5, '+'): rF(1), (11, '*'): rF(0), (11, '+'): rF(0), (11, ')'): rF(0), (9, '#'): rE(0), (9, ')'): rE(0), (9, '*'): s7, (9, '+'): rE(0), (11, '#'): rF(0), (1, '+'): s6, (6, 'id'): s5, (4, 'id'): s5, (1, '#'): a0, (6, '('): s4, (7, '('): s4, (4, '('): s4}

    This is a formatted version for viewing enjoyment:
    0 | 'id': s5, '(': s4 |
    1 | '+': s6, '#': a0 |
    2 | ')': rE(1), '+': rE(1), '*': s7,    '#': rE(1) |
    3 | ')': rT(1), '+': rT(1), '*': rT(1), '#': rT(1) |
    4 | 'id': s5, '(': s4 |
    5 | ')': rF(1), '+': rF(1), '*': rF(1), '#': rF(1) |
    6 | 'id': s5, '(': s4 |
    7 | 'id': s5, '(': s4 |
    8 | '+': s6, ')': s11 |
    9 | ')': rE(0), '+': rE(0), '*': s7,    '#': rE(0) |
    10|')': rT(0), '+': rT(0), '*': rT(0), '#': rT(0) |
    11|')': rF(0), '+': rF(0), '*': rF(0), '#': rF(0) |

	Here is an example of a canonical parse table:
	>>> gen_table(cfg.gen_grammar(S = "C C", C = "#c# C | #d#"), canonical=True)
	Generating items...
		1 / 5
		2 / 5
		3 / 8
		4 / 9
		5 / 9
		6 / 9
		7 / 10
		8 / 10
		9 / 10
		10 / 10
	Generating table...
		0 / 10
		1 / 10
		2 / 10
		3 / 10
		4 / 10
		5 / 10
		6 / 10
		7 / 10
		8 / 10
		9 / 10
	{(8, 'c'): rC(0), (3, 'c'): s3, (4, 'd'): rC(1), (4, 'c'): rC(1), (3, 'd'): s4, (5, '#'): rS(0), (6, 'c'): s6, (8, 'd'): rC(0), (6, 'd'): s7, (7, '#'): rC(1), (9, '#'): rC(0), (0, 'c'): s3, (2, 'd'): s7, (1, '#'): a0, (2, 'c'): s6, (0, 'd'): s4}

    Plus a little formattinged version:
    (0, 'c'): s3,(0, 'd'): s4
    (1, '#'): a0, 
    (2, 'd'): s7, (2, 'c'): s6,
    (3, 'c'): s3, (3, 'd'): s4, 
    (4, 'd'): rC(1), (4, 'c'): rC(1),
    (5, '#'): rS(0),
    (6, 'c'): s6,(6, 'd'): s7,
    (7, '#'): rC(1), 
    (8, 'c'): rC(0), (8, 'd'): rC(0)
    (9, '#'): rC(0)
    """
    count = -1 #what row in the table we have progressed to
    #I use a subclass of dict here that prevents writes to existing entries in the dict
    #If the grammar is too complicated for LR, it will overwrite existing entries, so
    #this is an easy way to detect that.
    action = util.dictWORM()
    grammar = augment(grammar, target)
    following = gen_follow(grammar)
    canon = items(grammar, canonical)
    if canonical:
        closure = canon_closure
    else:
        closure = simple_closure
    print 'Generating table...'
    for i in canon:
        count+=1
        print '\t', count, '/', len(canon)
        for state in i:
            try:
                if state.complete():
                    if state.sym.sym == 'root': # c) ACCEPT
                        action[count, "#"] = Cell(Cell.ACCEPT)
                    else: # b) REDUCE
                        #because of the way that the grammar stores ALTs, I have to blank out state's sym
                        #so it will be identical to the one in the grammar. This is a hack, and Bad and Wrong,
                        #but I will have to remaster most of the functions in this module to fix it (to use
                        #the proper (PAREN (ALT ...) (ALT ...) ...) structure), so it stays for now.
                        symbak = state.sym.sym; state.sym.sym = '' #THIS IS A HACK. but it works...^_^
                        index = grammar[symbak].children.index(state.sym)
                        if canonical:
                            action[count,state.ahead] = Cell(Cell.REDUCE, index, symbak)
                        else:
                            for a in following[symbak]:
                                action[count,a] = Cell(Cell.REDUCE, index, symbak)
                        state.sym.sym = symbak
                else:
                    if state.next().isLit(): # a) SHIFT
                        a = state.next().sym
                        j = canon.index(goto_closure(i, a, grammar, closure))
                        action[count,a] =  Cell(Cell.SHIFT, j)
            except NotImplementedError:
                raise NotImplementedError("Grammar is too complex to be LR.")
    return action
def gen_goto(grammar,target="S", canonical=False):
    """{str:Symbol}*str->{(str,int):int} -- extract LR goto table from a BNF grammar
	
	>>> gen_goto(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E")
	Generating items...
		1 / 6
		2 / 7
		3 / 8
		4 / 8
		5 / 9
		6 / 9
		7 / 10
		8 / 11
		9 / 12
		10 / 12
		11 / 12
		12 / 12
	{(4, 'F'): 3, (4, 'E'): 8, (7, 'F'): 10, (0, 'T'): 2, (4, 'T'): 2, (6, 'T'): 9, (6, 'F'): 3, (0, 'F'): 3, (0, 'E'): 1}
	"""
    if canonical:
        closure = canon_closure
    else:
        closure = simple_closure
    grammar = augment(grammar, target)
    canon = items(grammar, canonical)
    goto = {}
    count = -1
    for i in canon:
        count += 1
        for a in grammar:
            if goto_closure(i, a, grammar, closure) in canon:
                goto[count,a] = canon.index(goto_closure(i,a,grammar, closure))
    return goto
def augment(grammar, target="S"):
    """{str:Symbol}->{str:Symbol} -- add root->target to grammar

    >>> grammar = cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#")
    >>> augment(grammar,"E")
    {'root': (root -> (<E>)), 'E': (E -> (<E #+# T> | <T>)), 'T': (T -> (<T #*# F> | <F>)), 'F': (F -> (<#(# E #)#> | <#id#>))}
    """
    grammar["root"] = cfg.Symbol(cfg.Symbol.PAREN, "root", [cfg.Symbol(cfg.Symbol.ALT, 'root', [cfg.Symbol(cfg.Symbol.SYM,target)])])
    return grammar
def gen_follow(grammar):
    """{str:Symbol}->{str:[str]} -- generate the FOLLOW set for an augmented grammar
    
    >>> x = gen_follow(augment(cfg.gen_grammar(E = "T EP", EP = "#+# T EP", T = "F TP", TP = "#*# F TP", F = "#(# E #)# | #id#"), "E"))
    >>> x=={'E': [')', '#'], 'F': ['*'], 'TP': ['+'], 'T': ['+'], 'root': ['#'], 'EP': [')', '#']}
    True
    >>> x = gen_follow(augment(cfg.gen_grammar(E = "T | T EP", EP = "#+# T | #+# T EP", T = "F | F TP", TP = "#*# F | #*# F TP", F = "#(# E #)# | #id#"), "E"))
    >>> x=={'E': [')', '#'], 'F': [')', '#', '+', '*'], 'TP': [')', '#', '+'], 'T': [')', '#', '+'], 'root': ['#'], 'EP': [')', '#']}
    True
    >>> x = gen_follow(augment(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E"))
    >>> x=={'E': ['#', '+', ')'], 'root': ['#'], 'T': ['#', '+', ')', '*'], 'F': ['#', '+', ')', '*']}
    True

    NOTE:The first two examples are from one in Aho and Ullman's _Compilers_, but it uses null productions, which
    I don't like. The first just has the nulls removed (crippling the grammar), whereas the second one
    accurately reproduces the grammar in a different form. In extended BNF, the grammar they
    present looks like this:
    E->T {#+# T}
    T->F {#*# F}
    F->#(# E #)# | #id#

    The second example is just a hand-coded conversion to simple BNF using the algorithm I developed.
    """
    first = gen_first(grammar)
    follow = {}
    for a in grammar:
        follow[a] = []
    follow['root'].append("#")
    for a in grammar:
        for alt in grammar[a].children:
            #rule 2
            for prev,next in util.two_time(alt.children):
                if not prev.isLit():
                    follow[prev.sym].append(first[next.sym])
            #rule 3
            b = alt.children[-1]
            if not b.isLit() and b.sym != a: #TODO:and follow[a] not in follow[b.sym]
				#(could possibly eliminate filterdups later)
                follow[b.sym].append(follow[a])
    for a in follow:
        follow[a] = util.filter_dups(util.flatten(follow[a]))
    return follow
def gen_first(grammar):
    """{str:Symbol}->{str:[str]} -- generate the FIRST set for an augmented grammar
    
    >>> x=gen_first(augment(cfg.gen_grammar(E = "T EP", EP = "#+# T EP", T = "F TP", TP = "#*# F TP", F = "#(# E #)# | #id#"), "E"))
    >>> x=={'E': ['(', 'id'], 'F': ['(', 'id'], 'TP': ['*'], 'T': ['(', 'id'], 'root': ['(', 'id'], 'EP': ['+'], "(": ["("], ')': [')'], "*": ["*"], "+": ["+"], 'id': ['id'], "#": ["#"]}
    True
    >>> x=gen_first(augment(cfg.gen_grammar(E = "T | T EP", EP = "#+# T | #+# T EP", T = "F | F TP", TP = "#*# F | #*# F TP", F = "#(# E #)# | #id#"), "E"))
    >>> x=={'E': ['(', 'id'], 'F': ['(', 'id'], 'TP': ['*'], 'T': ['(', 'id'], 'root': ['(', 'id'], 'EP': ['+'], "(": ["("], ')': [')'], "*": ["*"], "+": ["+"], 'id': ['id'], "#": ["#"]}
    True
    >>> x=gen_first(augment(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E"))
    >>> x=={'E': ['(', 'id'], 'F': ['(', 'id'], ')': [')'], '(': ['('], '+': ['+'], '*': ['*'], 'T': ['(', 'id'], 'root': ['(', 'id'], 'id': ['id'], "#": ["#"]}
    True

    NOTE:The second example is included because it broke before filter_dups was added.
    Maybe it's better to prevent dups when adding, but I can't think of a good way that would catch
    everything because when adding list pointers, you can't tell what is (or will be) in there.
    """
    first = {}
    for a in cfg.extractAll(grammar):
        first[a] = []
    for a in cfg.extractAll(grammar):
        #rule 2 not handled because I don't allow null productions
        try:
            b = grammar[a]
        except KeyError: #rule 1 (lit)
            first[a].append(a)
        else: #rule 3
            for alt in b.children:
                x = alt.children[0]
                if x.isLit():
                    first[a].append(x.sym)
                else:
                    if a != x.sym:
                        first[a].append(first[x.sym])
    for a in first:
        first[a] = util.filter_dups(util.flatten(first[a]))
    return first
def simple_closure(i, grammar):
    """[State]*{str:Symbol}->[State] -- implement simple closure op

    That is, generate all related states in the grammar of the given states.
    
    NOTE:Although the states passed to closure can be either standard form (S -> (<E>))
    or stripped-down (S -> <E>) (without a surrounding PAREN), closure returns only stripped-down
    Symbols. This is because they are easier to use for the calling functions. This may change in the future.
    Please see the example.
    
    >>> grammar = cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#")
    >>> simple_closure([State(augment(grammar,"E")['root'])], grammar)
    [(root -> <E>)[0], (E -> <E #+# T>)[0], (E -> <T>)[0], (T -> <T #*# F>)[0], (T -> <F>)[0], (F -> <#(# E #)#>)[0], (F -> <#id#>)[0]]
    """
    j = list(i)
    #ensure that all are converted to stripped-down form (see docstring)
    for a in j:
        sym = a.next()
        if sym.type==cfg.Symbol.ALT:
            a.sym = sym
    #main closure generation code
    for a in j:
        b=a.next()
        if not b.isLit():
            for x in cfg.flatten(grammar[b.sym]):
                y = State(cfg.Symbol(cfg.Symbol.ALT, b.sym, x),0)
                if y not in j:
                    j.append(y)
    return j
def canon_closure(i, grammar):
    """[CanonState]*{str:Symbol}->[CanonState] -- implement canonical closure op

    That is, generate all related states in the grammar of the given states.
    
    NOTE:Although the states passed to closure can be either standard form (S -> (<E>))
    or stripped-down (S -> <E>) (without a surrounding PAREN), closure returns only stripped-down
    Symbols. This is because they are easier to use for the calling functions. This may change in the future.
    Please see the example.
    
    >>> grammar = cfg.gen_grammar(S = "C C", C = "#c# C | #d#")
    >>> canon_closure([CanonState(augment(grammar)['root'], 0, "#")], grammar)
    [(root -> <S>)[0, '#'], (S -> <C C>)[0, '#'], (C -> <#c# C>)[0, 'c'], (C -> <#c# C>)[0, 'd'], (C -> <#d#>)[0, 'c'], (C -> <#d#>)[0, 'd']]
    >>> grammar = cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#")
    >>> canon_closure([CanonState(augment(grammar,"E")['root'], 0, "#")], grammar)
    [(root -> <E>)[0, '#'], (E -> <E #+# T>)[0, '#'], (E -> <T>)[0, '#'], (E -> <E #+# T>)[0, '+'], (E -> <T>)[0, '+'], (T -> <T #*# F>)[0, '#'], (T -> <F>)[0, '#'], (T -> <T #*# F>)[0, '+'], (T -> <F>)[0, '+'], (T -> <T #*# F>)[0, '*'], (T -> <F>)[0, '*'], (F -> <#(# E #)#>)[0, '#'], (F -> <#id#>)[0, '#'], (F -> <#(# E #)#>)[0, '+'], (F -> <#id#>)[0, '+'], (F -> <#(# E #)#>)[0, '*'], (F -> <#id#>)[0, '*']]
    """
    first = gen_first(grammar)
    j = list(i)
    #ensure that all are converted to stripped-down form (see docstring)
    for a in j:
        sym = a.next()
        if sym.type==cfg.Symbol.ALT:
            a.sym = sym
    #main closure generation code
    for a in j:
        b=a.next()
        if not b.isLit():
            for x in cfg.flatten(grammar[b.sym]):
                if (a >> 1).complete():
                    beta = a.ahead
                else:
                    beta = (a >> 1).next().sym
                for lookahead in first[beta]:
                    y = CanonState(cfg.Symbol(cfg.Symbol.ALT, b.sym, x),0, lookahead)
                    if y not in j:
                        j.append(y)
    return j
def goto_closure(i,sym,grammar, closure):
    """[State]*str*{str:Symbol}*fn->[State] -- create closure of goto in i for sym

    This works by generating the closure of each State in i after incing its progress
    ach..just read the code. It's much simpler.

    NOTE:The input is expected to be the stripped-down format (ie E -> <F> not E -> (<F>) )
    because the rest of the algorithms do. This may change. See example below for usage.

    >>> grammar = augment(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E")
    >>> goto_closure([State(grammar['root'],1), State(cfg.Symbol(cfg.Symbol.ALT,"E",cfg.flatten(grammar["E"])[0]), 1)], "+", grammar, simple_closure)
    [(E -> <E #+# T>)[2], (T -> <T #*# F>)[0], (T -> <F>)[0], (F -> <#(# E #)#>)[0], (F -> <#id#>)[0]]
    """
    return util.filter_dups(util.flatten([closure([a >> 1], grammar) for a in i if a.next().sym==sym]))
goto_closure = util.memoise(goto_closure, (1,1,0,0))
def items(grammar, canonical=False):
    """{str:Symbol}->[State] -- return canonical LR(0) set of items
    
    NOTE:grammar must have a State constructed with (root->target-symbol)
    To do this, call augment on the grammar with a target specified
    TODO:Think about using dicts in closure, goto_closure and items to avoid having
    to call 'x not in y' all the time. I'm fairly sure the efficiency will be O(lg n) instead of Theta(n),
    and it will be easier to code, just take a bit more storage. And who cares about memory?"""
    if canonical:
        c = [canon_closure([CanonState(grammar['root'],0,"#")], grammar)]
        closure = canon_closure
    else:
        c = [simple_closure([State(grammar['root'],0)], grammar)]
        closure = simple_closure
    symbols = cfg.extractAll(grammar)
    print 'Generating items...'
    counter=1
    for i in c:
        for x in symbols:
            g = goto_closure(i,x, grammar, closure)
            if g and g not in c:
                c.append(g)
        print '\t', counter, '/', len(c)
        counter+=1
    return c
##items = util.memoise(items, (0,1))
#WARNING! Disable above line for use with more than one grammar per session!
#This optimisation must be *off* for tests to pass, and is recommended only for cgi situations
#where the module is reloaded for each call.
def lr_parse(words, grammar, table, goto,general_errors=True):
    """[str]*{str:Symbol}*{(str,int):Cell}*{(str,int):int}*bool->Entry -- LR parser driver that returns root of parse tree

    If general_errors is true, table should not contain any error entries:
    lr_parse will use the FMA algorithm to attempt recovery and repair.
    If general_errors is false, table should contain error entries properly
    referring to error handling routines. These routines will be passed (stack,words,ip)
    for recovery and repair.
    """
    def fma(stack,ip):
        """[Entry]*int->[Entry]*int -- forward move algorithm
        
        ErrEntry on stack tracks actual Entries instead of indices to them, using [Entry]
        """
        first = gen_first(grammar)
        ep = ip
        w = words[ep]
        #the bottom acts as a catch-all for when we empty out the stack...sort of. I'm not entirely comprehending it already.
        bottom = [Entry(col, sym) for col,sym in table] + [Entry(col,sym) for col,sym in goto]
        #init slurps just the stuff that matches the current input into the initial state set
        #perhaps the reason bottom exists is to provide this function later in the process
        init = util.filter_dups([table[col,sym] for col,sym in table if w in first[sym] and table[col,sym].type==Cell.SHIFT])
        err_stack = [ErrEntry(bottom), ErrEntry(util.filter_dups([Entry(cell.index, w) for cell in init]))]
        ep+=1
        while True:
            w = words[ep]
            #have to filter out unhandled Error entries (they take value None)
            moves = util.filter_dups(filter(None, [table.get((s.state,w)) for s in err_stack[-1].entries]))
            if Cell(Cell.ACCEPT) in moves:
                return err_stack[-1], ep
            elif util.same_bool([cell.type for cell in moves]):
                if moves[0].type==Cell.ERROR:
                    #take the advice of the error entry
                    stack,ip = moves[0].sym(stack,words,ip)
                    raise TypeError("Got an early error repair!")
                if moves[0].type==Cell.SHIFT:
                    err_stack.append(ErrEntry(util.filter_dups([Entry(cell.index,w) for cell in moves])))
                    ep+=1
                elif moves[0].type==Cell.REDUCE:
                    ref = util.same([(cell.sym, cell.index) for cell in moves])
                    if ref:
                        #do the reduce
                        sym,index = ref
                        beta = cfg.flatten(grammar[sym])[index]
                        #make sure there are enough entries on the stack to reduce,
                        #otherwise halt
                        if len(err_stack) > len(beta):
                            err_stack, children = err_stack[ : -len(beta)], err_stack[-len(beta) : ]
                            err_stack.append(ErrEntry(util.filter_dups(filter(lambda e: e.state, [Entry(goto.get((e.state,sym)), sym) for e in err_stack[-1].entries])), children))
                            print "error: %s->%s" % (cell.sym, cfg.Symbol(cfg.Symbol.ALT, '',beta))
                        else:
                            return err_stack[-1], ep
                    else:
                        return err_stack[-1], ep
            else:
                return err_stack[-1], ep
    ip = 0
    stack = [Entry(0)]
    while True:
        w = words[ip]
        s = stack[-1]
        try:
            action = table[s.state,w]
        except KeyError:
            if general_errors:
                print 'Error! Analysing what went wrong:'
                try:
                    u, ip = fma(stack, ip)
                except TypeError, e: #we got an early error repair, as advised by an Error entry
                    pass #so don't try the general repair algorithm
                else:
                    stack=general_repair(u, stack, words[ip],grammar,table,goto)
            else:
                print "Unhandled error!"
                raise
        else:
            if action.type==Cell.ERROR:
                stack,ip = action.sym(stack,words,ip)
            elif action.type==Cell.SHIFT:
                stack.append(Entry(action.index, w))
                ip+=1
            elif action.type==Cell.REDUCE:
                beta = cfg.flatten(grammar[action.sym])[action.index]
                stack,children = stack[ : -len(beta)], stack[-len(beta) : ]
                stack.append(Entry(goto[stack[-1].state,action.sym], action.sym, children))
                print "%s->%s" % (action.sym, cfg.Symbol(cfg.Symbol.ALT, '',beta))
            else: #ACCEPT
                print 'accepted'
                return s
#section of handicraft!
def add_error_cells(table):
    """{(str,int):Cell}!

    NOTE:any NotImplementedErrors that are caught and ignored just mean that
    it was easier to write a 2D loop that skips some entries than two make a func
    skip_table that generates a 2D table, except for the diagonal. Though I will probably write it someday. ^_^
    Anyway, it has to skip some entries because there are already non-ERROR Cells there."""
    pron_cols = (25,17,14,26,18,22,23,19)
    verb_cols = (65,40,34,46,56,50)
    neg_verb_cols = (161,129,98,135,153,145)
    det_cols = (95,124,115,16,28,21) #last three are for when the error is detected at the beginning of a sentence
    copula_cols = (38,45)
    neg_copula_cols = (254,261)
    verb_syms = ('V-1-SG','V-2-SG','V-3-SG','V-1-PL','V-2-PL','V-3-PL')
    noun_syms = ('N-M-SG', 'N-F-SG', 'N-M-PL', 'N-F-PL')
    adj_syms = ('ADJ-M-SG', 'ADJ-F-SG', 'ADJ-M-PL', 'ADJ-F-PL')
    pron_syms = ('PRON-1-SG', 'PRON-2-SG', 'PRON-M-3-SG', 'PRON-F-3-SG', 'PRON-1-PL', 'PRON-2-PL', 'PRON-M-3-PL', 'PRON-F-3-PL')
    det_syms = ('DET-M-SG', 'DET-F-SG', 'DET-PL')
    for col in det_cols:
        #inflexion determinant-noun mismatch (like a type error)
        for sym in noun_syms:
            try:
                table[col,sym] = Cell(Cell.ERROR, sym=DetMismatch)
            except NotImplementedError:
                continue
        #adj after determinant (should go after noun)
        for sym in adj_syms:
            try:
                table[col,sym] = Cell(Cell.ERROR, sym=SwapWords)
                #the unknown quantity. we go around with hoods over our heads.
            except NotImplementedError:
                continue
    #over inflexion of various denominations
    for sym in verb_syms:
        table[284, sym] = Cell(Cell.ERROR, sym=TwoVerbs) #after NEG
        table[110, sym] = Cell(Cell.ERROR, sym=TwoVerbs) #after ADV
        for col in verb_cols:
            table[col,sym] = Cell(Cell.ERROR, sym=TwoVerbs) 
    for col in pron_cols:
        #under-inflexion
        table[col,'INF'] = Cell(Cell.ERROR, sym=SubjectMismatch)
        #inflexion subject-verb mismatch
        for sym in verb_syms:
            try:
                table[col, sym] = Cell(Cell.ERROR, sym=SubjectMismatch)
                table[64, sym] = Cell(Cell.ERROR, sym=look_back) #after a negative
            except NotImplementedError: #because (23,V-1-SG), (17,V-2-SG), etc
                continue #are already valid transitions
        #missing copula
        for sym in adj_syms:
            table[col,sym] = Cell(Cell.ERROR, sym=MissingCopula)
    #adjective-noun confusion
    #for starters, we assume ADJ is easily confused with N by the POS identifier. There may
    #be positions where ADJ is better converted to ADV. Those will come later, if necessary.
    for sym in adj_syms:
        table[284,sym] = Cell(Cell.ERROR, sym=Adj2N)
        for col in verb_cols:
            table[col,sym] = Cell(Cell.ERROR, sym=Adj2N)
    #under-inflexion with negative verb.
    table[64,"NEG"] = Cell(Cell.ERROR, sym=NegNoVerb)
    #extra copula
    for col in copula_cols:
        for sym in verb_syms:
            table[col,sym] = Cell(Cell.ERROR, sym=ExtraWord)
    #verb after negative of a negative copula
    #ummm.....so this is a really weird error.
    for col in neg_copula_cols:
        for sym in verb_syms:
            table[col,sym] = Cell(Cell.ERROR, sym=V2Adj)
    #missing NE of ne..pas pair
    for col in verb_cols:
        table[col, "NEG"] = Cell(Cell.ERROR, sym=MissingNe)
    #missing NEG of ne...pas pair
    for col in neg_verb_cols:
        table[col, "INF"] = Cell(Cell.ERROR, sym=MissingNeg)
        table[col, "ADV"] = Cell(Cell.ERROR, sym=MissingNeg)
        table[col, "PREP"] = Cell(Cell.ERROR, sym=MissingNeg)
        for sym in noun_syms+det_syms+pron_syms:
            table[col,sym] = Cell(Cell.ERROR, sym=MissingNeg)
    #NE first...we guess that the next item is the real subject and swap them
    table[0, "NE"] = Cell(Cell.ERROR, sym=SwapWords)
def gen_neg(func):
    """Generate a function that handles looking over a NE..NEG combo to fix an error"""
    def look_back(stack,words,ip):
        top = stack.pop()
        stack,ip = func(stack,words,ip,look_back=2)
        stack.append(top)
        return stack,ip
    return look_back
def Adj2N(stack,words,ip):
    a2n = {'ADJ-M-SG':'N-M-SG',
           'ADJ-F-SG':'N-F-SG',
           'ADJ-M-PL':'N-M-PL',
           'ADJ-F-PL':'N-F-PL'}
    words[ip] = a2n[words[ip]]
    return stack,ip
def V2Adj(stack,words,ip):
    v2a = {254:'ADJ-M-SG', 261:'ADJ-M-PL'}
    words[ip] = v2a[stack[-1].state]
    return stack,ip
def SwapWords(stack,words,ip):
    """Swap this word and the next one"""
    words[ip],words[ip+1] = words[ip+1],words[ip]
    return stack,ip
def DetMismatch(stack,words,ip):
    """match noun since it's almost always right
    note that the machine language equivalent in ML just says
    "don't use determinants--we'll do it for you"
    while Lisp says
    "last time I needed determinant I was speaking English"
    and Java says
    "The french doesn't like the naked objects"""
    noun = {}
    #middle of sentence
    noun[124,'N-M-SG'] = noun[115,'N-M-SG'] = (95,'DET-M-SG')
    noun[95, 'N-F-SG'] = noun[115, 'N-F-SG'] = (124,'DET-F-SG')
    noun[95, 'N-M-PL'] = noun[124, 'N-M-PL'] = noun[95, 'N-F-PL'] = noun[124, 'N-F-PL'] = (115, 'DET-PL')
    #beginning of sentence
    noun[28,'N-M-SG'] = noun[21,'N-M-SG'] = (16,'DET-M-SG')
    noun[16, 'N-F-SG'] = noun[21, 'N-F-SG'] = (28,'DET-F-SG')
    noun[16, 'N-M-PL'] = noun[28, 'N-M-PL'] = noun[16, 'N-F-PL'] = noun[28, 'N-F-PL'] = (21, 'DET-PL')
    #then replace the top of the stack (there might be a simpler way than this)
    stack[-1] = Entry(*noun[stack[-1].state,words[ip]])
    return stack,ip
def TwoVerbs(stack,words,ip):
    """convert second verb to be an infinitive"""
    words[ip] = 'INF'
    return stack,ip
def NegNoVerb(stack,words,ip):
    """check for verb/inf after NEG and swap it in (inflect INF if necessary).
    TODO:Add missing verb correction someday."""
    if words[ip+1] in ['INF', 'V-1-SG', 'V-2-SG', 'V-3-SG', 'V-1-PL', 'V-2-PL', 'V-3-PL']:
        words[ip] = words[ip+1]
        words[ip+1] = 'NEG'
        if words[ip]=="INF":
            return SubjectMismatch(stack,words,ip,look_back=2)
        else:
            return stack,ip
def ExtraWord(stack,words,ip):
    """Get rid of a word just parsed"""
    stack.pop()
    return stack,ip
def MissingCopula(stack,words,ip,look_back=1):
    """insert missing copula"""
    copula = {}
    copula['PRON-1-SG'] = copula['PRON-2-SG'] \
                        = copula['PRON-M-3-SG'] = copula['PRON-F-3-SG'] \
                        = copula['N-M-SG'] = copula['N-F-SG'] = 'COPULA-SG'
    copula['PRON-1-PL'] = copula['PRON-2-PL'] \
                        = copula['PRON-M-3-PL'] = copula['PRON-F-3-PL'] \
                        = copula['N-M-PL'] = copula['N-F-PL'] = 'COPULA-PL'
    words.insert(ip, copula[words[ip-look_back]])
    return stack,ip
def MissingNe(stack,words,ip):
    verb_cols = (65,40,34,46,56,50)
    neg_verb_cols = (161,129,98,135,153,145)
    negify = dict(zip(verb_cols, neg_verb_cols))
    stack.insert(-1, Entry(64, "NE"))
    stack[-1].state = negify[stack[-1].state]
    return stack,ip
def MissingNeg(stack,words,ip):
	words.insert(ip, 'NEG')
	return stack,ip
def SubjectMismatch(stack,words,ip,look_back=1):
    """change forward text to a verb matching the subject (from INF)"""
    prevword = {'PRON-1-SG':'V-1-SG',
                'PRON-2-SG':'V-2-SG',
                'PRON-M-3-SG':'V-3-SG',
                'PRON-F-3-SG':'V-3-SG',
                'PRON-1-PL':'V-1-PL',
                'PRON-2-PL':'V-2-PL',
                'PRON-M-3-PL':'V-3-PL',
                'PRON-F-3-PL':'V-3-PL',
                'N-M-PL':'V-3-PL',
                'N-F-PL':'V-3-PL'}
    words[ip] = prevword.get(words[ip-look_back], 'V-3-SG')
    return stack,ip
#HACK here because only top-level funcs be can pickled
look_back = gen_neg(SubjectMismatch)
#end handicraft section
def general_repair(err_root, stack, w, grammar, table, goto):
    """Attempt a splicing operation based on the information contained in the
    already parsed context and the forward (right) context returned by fma
    """
    #regenerate moves, and since err_parse couldn't decide which move to make, just choose one
    moves = util.filter_dups(filter(None, [table.get((entry.state,w)) for entry in err_root.entries]))
    #notice that if moves is empty, err_parse has no valid reductions made, so instead
    #just guess a parent reduction
    if moves:
        reduction = random.choice(moves)
    else:
        reduction = random.choice([table[(col,sym)] for ((col,sym), cell) in table.items() if col in [e.state for e in err_root.entries]])
    target = cfg.flatten(grammar[reduction.sym])[reduction.index]
    def fnadd(parent, entries):
        parent.children.extend(entries)
        return parent
    #-1 equals errored, so should consume any input tokens
    #-2 equals replaced, so should consume (at least) 1 input token
    after_err = util.buildTree(err_root, fnconvert=lambda err: Entry(err.entries[0].state,err.entries[0].sym), fnchildren=lambda err: err.children, fnadd=fnadd)
    before_err = stack.pop()#pop the current item off the stack
    if len(target) > 2 and before_err.sym==target[-3].sym: #deletion #so insert something
        children = [before_err, Entry(-1, target[-2].sym), after_err] #not sure target[-2] is right but it's a guess ^_^
    elif len(target) > 1 and before_err.sym==target[-2].sym: #insertion #so delete something
        children = [before_err, after_err] #maybe...
    else: #mutation #so change something!
        if len(target) > 1:
            if target[-2].sym==stack[-1].sym: stack.pop() #this is really a mutation, so get rid of what was there first...sort of.
            children = [Entry(-2, target[-2].sym), after_err]
        else:
            children = [Entry(-2, target[0].sym), after_err]
        #now replace with the newly reduced item..and continue!
    stack.append(Entry(goto[stack[-1].state, reduction.sym], reduction.sym, children)) 
    return stack
def retrieve(root, words):
    """Entry*[str]->str -- retrieve parse and build a presentable string version of it"""
    def rp(root, l):
        if root.children:
            return ('   '*l) + str(root) +'\n' + ''.join([rp(ch, l+1) for ch in root.children])
        else:
            if root.state==-1: #errored!
                return ('   '*l) + '-error-' + " (" + str(root)+')\n'
            else:
                return ('   '*l) + words.pop(0) + " (" + str(root)+')\n'
    return rp(root, 0)
def _test():
    import doctest, lr
    return doctest.testmod(lr)
def main():
    #-grammar-
    ##grammar = augment(cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#"), "E")
    grammar, posen=util.loadVars('c:/documents/class/nuwen/french_simple.grammar')
    grammar = augment(grammar)
    ##print retrieve(parse('id * id + id'.split(), grammar, "E", canonical=True), 'x * y + z'.split())
    table,goto=util.loadVars('c:/documents/class/nuwen/french_canon.lr')
##    import cPickle
##    f = file('ETF.lr', 'r')
##    table=cPickle.load(f)
##    goto=cPickle.load(f)
##    f.close()
    ##print retrieve(lr_parse('( ) #'.split(), grammar, table, goto), '( ) #'.split())
    ##add_error_cells(table)
    ##print retrieve(lr_parse('PRON-1-SG V-1-SG DET-F-SG N-M-SG . #'.split(), grammar, table, goto, False), "j' aime la the . #".split())
    #this one has a problem in that it can generate the correct repair, (by generating a NP-1-SG from target),
    #but cannot restart parsing because there is already a NP-1-SG on the stack. Now, I guess we could check the
    #stack for a match and slurp it off there instead of genning a new one. That might work. (It would probably have to
    #be in a loop, since this could happen an arbitrary number of times, I think)
    ##print retrieve(lr_parse('PRON-M-3-PL NE V-3-PL NEG INF DET-M-SG N-M-SG . #'.split(), grammar, table, goto, False), "nous n' aimons pas manger un sandwich . #".split())
    ##print retrieve(lr_parse('PRON-M-3-PL V-3-PL V-1-PL DET-M-SG N-M-SG . #'.split(), grammar, table, goto, False), "nous aimons mange un sandwich . #".split())
    ##print retrieve(lr_parse('PRON-1-SG NE V-1-SG NEG . #'.split(), grammar, table, goto, False), "je ne nage pas . #".split())
    ##print retrieve(lr_parse('PRON-1-SG INF ADV . #'.split(), grammar, table, goto, False), "je lire beaucoup . #".split())
    #print retrieve(lr_parse(['PRON-1-SG', 'V-1-SG', 'N-M-SG', 'ADV', '.', "#"], grammar, table, goto, False), ['Je', 'joue', 'basket', 'souvent', '.', "#"])
    print retrieve(lr_parse(['PRON-1-SG', 'V-1-SG', 'ADJ-F-SG', '.', "#"], grammar, table, goto, True), ['Je', 'parle', 'espagnole', '.', "#"])
    #grammar=augment(cfg.gen_grammar(S = "C C", C = "#c# C | #d#"))
    #grammar = cfg.gen_grammar(E = "T | T EP", EP = "#+# T | #+# T EP", T = "F | F TP", TP = "#*# F | #*# F TP", F = "#(# E #)# | #id#")
    #I would represent this as E->T {#+# T}; T->F {#*# F}; F->#(# E #)# | #id#
    #but I don't like null alternatives and would prefer to make two wordier rules. But I have an extended
    #BNF converter also...these guys are going without that and it makes representation difficult sometimes
    #print gen_goto(grammar, "E")
    #print gen_table(grammar, "E")
    #grammar = augment(grammar, "E")
    #print gen_first(grammar)
    #print gen_follow(grammar)
    #print items(grammar)
    #print goto_closure([State(grammar['root'],1), State(cfg.Symbol(cfg.Symbol.ALT,"E",cfg.flatten(grammar["E"])[0]), 1)], "+", grammar)
    #print closure([State(grammar['root'],0)], grammar)
    #print retrieve(lr_parse('id * id + id #'.split(), grammar, gen_table(grammar, "E"), gen_goto(grammar, "E")), 'id * id + id #'.split())
    #print retrieve(parse('c d c d'.split(), grammar, canonical=True), 'x ; y ;'.split())
    _test()
if __name__=='__main__':
    main()
    #below here, one can find a hand-made parse table and goto table. Enjoy!
##    table = {} # {(int,str):Cell}
##    #-0-
##    table[0,'id'] = Cell(Cell.SHIFT, 5)
##    table[0,'('] = Cell(Cell.SHIFT, 4)
##    #-1-
##    table[1,"+"] = Cell(Cell.SHIFT,6)
##    table[1,"#"] = Cell(Cell.ACCEPT)
##    #-2-
##    table[2,"+"] = Cell(Cell.REDUCE, 1, "E")
##    table[2,"*"] = Cell(Cell.SHIFT,7)
##    table[2,")"] = Cell(Cell.REDUCE,1,"E")
##    table[2,"#"] = Cell(Cell.REDUCE,1,"E")
##    #-3-
##    table[3,"+"] = Cell(Cell.REDUCE,1,"T")
##    table[3,"*"] = Cell(Cell.REDUCE,1,"T")
##    table[3,")"] = Cell(Cell.REDUCE,1,"T")
##    table[3,"#"] = Cell(Cell.REDUCE,1,"T")
##    #-4-
##    table[4,'id'] = Cell(Cell.SHIFT, 5)
##    table[4,'('] = Cell(Cell.SHIFT, 4)
##    #-5-
##    table[5,"+"] = Cell(Cell.REDUCE,1,"F")
##    table[5,"*"] = Cell(Cell.REDUCE,1,"F")
##    table[5,")"] = Cell(Cell.REDUCE,1,"F")
##    table[5,"#"] = Cell(Cell.REDUCE,1,"F")
##    #-6-
##    table[6,'id'] = Cell(Cell.SHIFT, 5)
##    table[6,'('] = Cell(Cell.SHIFT, 4)
##    #-7-
##    table[7,'id'] = Cell(Cell.SHIFT, 5)
##    table[7,'('] = Cell(Cell.SHIFT, 4)
##    #-8-
##    table[8,"+"] = Cell(Cell.SHIFT,6)
##    table[8,")"] = Cell(Cell.SHIFT,11)
##    #-9-
##    table[9,"+"] = Cell(Cell.REDUCE,0,"E")
##    table[9,"*"] = Cell(Cell.SHIFT,7)
##    table[9,")"] = Cell(Cell.REDUCE,0,"E")
##    table[9,"#"] = Cell(Cell.REDUCE,0,"E")
##    #-10-
##    table[10,"+"] = Cell(Cell.REDUCE,0,"T")
##    table[10,"*"] = Cell(Cell.REDUCE,0,"T")
##    table[10,")"] = Cell(Cell.REDUCE,0,"T")
##    table[10,"#"] = Cell(Cell.REDUCE,0,"T")
##    #-11-
##    table[11,"+"] = Cell(Cell.REDUCE,0,"F")
##    table[11,"*"] = Cell(Cell.REDUCE,0,"F")
##    table[11,")"] = Cell(Cell.REDUCE,0,"F")
##    table[11,"#"] = Cell(Cell.REDUCE,0,"F")
##    #-goto!-
##    goto = {}
##    goto[0,"E"] = 1
##    goto[0, "T"] = 2
##    goto[0,"F"]=3
##    goto[4,"E"] = 8
##    goto[4,"T"] = 2
##    goto[4,"F"] = 3
##    goto[6,"T"] = 9
##    goto[6,"F"] = 3
##    goto[7,"F"] = 10
