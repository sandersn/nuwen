"""earley.py -- implementation of Earley's CFG parser

Earley's algorithm is a dynamic programming algorithm, so it uses a table
to avoid the redundant work performed by recursion. The principal way the implementation
differs from the algorithm is that the small methods related to the states stored in the table
are object-oriented and stored in class EarleyState. Also, states know how to enqueue
themselves properly given a column from the table. This shifts functionality to State
that could properly be located in class list. However, I didn't want to subclass list
and possibly degrade performance. (This is now less of an issue with Python 2.3)

Now, new and improved with both error-correcting and non-error-correcting methods
in the SAME file! Please use the parse module to interface with earley, unless you have
a good reason to want only earley parsing.

If you insist on earley-only parsing, here is how to do it:
>>> #set up an example grammar
>>> import cfg
>>> from util import findif
>>> grammar = cfg.gen_grammar(E = "E #+# T | T", T = "T #*# F | F", F="#(# E #)# | #id#")
>>> #parse parses the tokens and returns the parse tree root
>>> chart = parse('id * id + id'.split(), grammar, "E")
>>> root = findif(lambda x:x.sym.sym=='root:', chart[-1])
>>> retrieveParse(root, 'id * id + id'.split())
'root:E(0, 5)\\n   E #+# T(0, 5)\\n      T(0, 3)\\n         T #*# F(0, 3)\\n            F(0, 1)\\n               #id#(0, 1)\\n                  id (#id#)\\n            * (#*#)\\n            #id#(2, 3)\\n               id (#id#)\\n      + (#+#)\\n      F(4, 5)\\n         #id#(4, 5)\\n            id (#id#)\\n'
>>> #or, with error correcting
>>> chart = parse_correct('id * id + id'.split(), grammar, "E")
>>> root = findif(lambda x:x.sym.sym=='root:', chart[-1])
>>> retrieveParse(root, 'id * id + id'.split())
'root:E(0, 5)e1\\n   T(0, 5)e1\\n      T #*# F(0, 5)e1\\n         T #*# F(0, 3)e0\\n            F(0, 1)e0\\n               #id#(0, 1)e0\\n                  id (#id#)\\n            * (#*#)\\n            #id#(2, 3)e0\\n               id (#id#)\\n         + (#*#)\\n         #id#(4, 5)e0\\n            id (#id#)\\n'

XXX:This is not necessarily correct...I even believe that it is INcorrect! oddly enough
it believes that it is easier to replace the + with * and than to wrap the final #id# with an F rule.
(later)Test results with a complicated grammar (french.grammar) seem to indicate that this
algorithm generally returns the correct results. Further investigation still need.
TODO:Investigate this please. e1 vs e0
"""
from cfg import Symbol, flatten
from parse_state import State
import util
class EarleyState(State):
    def __init__(self, sym=Symbol(), start=0, end=0, progress=0):
        State.__init__(self, sym, progress)
        self.start = start#begin index in word list (see parse())
        self.end = end#end index in word list
        self.parents=[]#the parent pointers are filled in by parse and retrieved by retrieveParse
    def __str__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce useful results."""
        return str(self.sym)+str((self.start,self.end))+'\n'
    def __repr__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce precise results."""
        return repr(self.sym)+"["+repr(self.progress)+'] '+repr((self.start,self.end))+'\n'
    def __eq__(self,other):
        return State.__eq__(self, other) and self.start==other.start and self.end==other.end
    def enq(self,l,p=None):
        """[]*Symbol->None -- Enqueue this state in the supplied list if it is new or least-errors.

        This promotes slightly ugly code, but means I don't have to worry about subclassing list...
        If p is provided, this is a parent pointer to be added."""
        if self not in l:
            l.append(self)
            if p: self.parents.extend(p)
        else:
            if p:
                l[l.index(self)].parents.extend(p)
    def predictor(self,grammar, chart):
        """{str:Symbol}*[[State]...]->None

        Given the progress for this state, find all the compatible grammar rewrite rule and enqueue
        them into the table--the column at the end of this state."""
        for gamma in flatten(grammar[self.next().sym]):
            EarleyState(Symbol(Symbol.ALT, self.next().sym, gamma), self.end, self.end, 0).enq(chart[self.end])
    def scanner(self, words, chart):
        """[str]*[[State]...]->None -- If this state matches the current word, update a copy of it in the next column over."""
        if self.end < len(words) and self.next().sym==words[self.end]:
            #eq (maybe second param to outer Symbol should be None)
            EarleyState(Symbol(Symbol.ALT, self.next().sym, [Symbol(Symbol.LIT, words[self.end])]), \
                  self.end,self.end+1, 1).enq(chart[self.end+1])
    def completer(self, chart):
        """[[State]...]->None -- If this state is complete, add advanced parent rewrite rules to the chart."""
        for a in chart[self.start]:
            if a.next().sym == self.sym.sym:
                #TODO:this new code doesn't work, probably because doesn't copy a.sym like
                #current code does...don't have time to make it work,
                #but I provide it for enrichment of future generations.
                #(a >> 1).enq(chart[self.end], a.parents+[self])
                EarleyState(Symbol(a.sym.type, a.sym.sym, a.sym.children),
                      a.start, self.end, a.progress+1).enq(chart[self.end],a.parents+[self])
class ErrState(EarleyState):
    __safe_for_unpickling__ = True
    def __init__(self, sym=Symbol(), start=0, end=0, progress=0, errors=0):
        EarleyState.__init__(self, sym, start, end, progress)
        self.errors = errors #the error count
    def __str__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce useful results."""
        return str(self.sym)+str((self.start,self.end))+'e'+str(self.errors)+'\n'
    def __repr__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce precise results."""
        return repr(self.sym)+"["+repr(self.progress)+'] '+repr((self.start,self.end))+'e'+repr(self.errors)+'\n'
    def __eq__(self,other):
        return EarleyState.__eq__(self,other) and self.errors==other.errors
    def eqExceptErrors(self,other):
        """Just a wrapper for EarleyState.__eq__(self, other)

        If you really want, you could call it yourself manually, so this function may disappear someday."""
        return EarleyState.__eq__(self, other)
    def enq(self,l,p=None):
        """[]*Symbol->None -- Enqueue this state in the supplied list if it is new or least-errors.

        This promotes slightly ugly code, but means I don't have to worry about subclassing list...
        If p is provided, this is a parent pointer to be added."""
        if self not in l:
            l.append(self)
            if p: self.parents.extend(p)
        else:
            if self.errors < l[l.index(self)].errors:
                l[l.index(self)] = self
            if p:
                l[l.index(self)].parents.extend(p)
    def predictor(self,grammar, chart):
        """{str:Symbol}*[[State]...]->None -- Given the progress for this state, find all the compatible grammar rewrite rule and enqueue
        them into the table--the column at the end of this state."""
        for gamma in flatten(grammar[self.next().sym]):
            ErrState(Symbol(Symbol.ALT, self.next().sym, gamma), self.end, self.end, 0).enq(chart[self.end])
    def scanner(self, words, chart):
        """[str]*[[State]...]->None -- If this state matches the current word, update a copy of it in the next column over."""
        #technically the innermost LIT symbol should be filled with self.next().sym, not words[self.end], but the second method of accessing
        #is presumed faster and we just tested for equality one line above, so I decided the tradeoff was worth it. But see lower three calls for
        #the error-accumulating method.
        if self.end < len(words):
            if self.next().sym==words[self.end]:
                    ErrState(Symbol(Symbol.ALT, self.next().sym, [Symbol(Symbol.LIT, words[self.end])]), \
                          self.end,self.end+1, 1, 0).enq(chart[self.end+1])
            else:
                #modify
                ErrState(Symbol(Symbol.ALT, self.next().sym, [Symbol(Symbol.LIT, self.next().sym)]), \
                      self.end,self.end+1, 1, 1).enq(chart[self.end+1])
            #insert
            ErrState(Symbol(Symbol.ALT, self.next().sym, [Symbol(Symbol.LIT, self.next().sym)]), \
                  self.end+1,self.end+1, 0, 1).enq(chart[self.end+1])
            #delete
            ErrState(Symbol(Symbol.ALT, self.next().sym, [Symbol(Symbol.LIT, self.next().sym)]), \
                  self.end,self.end, 1, 1).enq(chart[self.end])
    def completer(self, chart):
        """[[State]...]->None -- If this state is complete, add advanced parent rewrite rules to the chart."""
        for a in chart[self.start]:
            if a.next().sym == self.sym.sym:
                ErrState(Symbol(a.sym.type, a.sym.sym, a.sym.children),
                      a.start, self.end, a.progress+1, a.errors+self.errors).enq(chart[self.end],a.parents+[self])
def findFirst(set):
    """[State]->State -- Find the state with the earliest starting point
    
    Could be rewritten to be much more efficient if I used idiomatic Python."""
    return min([(s.start,s) for s in set])[1]
def findSames(state,set):
    """ErrState*[ErrState]->[ErrState] -- find States that are the same except for error count"""
    return [s for s in set if s.eqExceptErrors(state)]
def findLeast(set):
    """[State]->State -- find State with least errors"""
    return min([(s.errors,s) for s in set])[1]
def parse_correct(words, grammar, target='S'):
    """[str]*{str:Symbol}*str->[[ErrState]...] -- Parse with error correcting included

    words -- our supplied POS, grammar is the grammar to parse against,
    target -- the target symbol in the grammar (default 'S' of course)
    returns the parse chart without any parses retrieved"""
    chart = [[] for i in range(len(words)+1)]
    ErrState(Symbol(Symbol.SYM, "root:", [Symbol(Symbol.SYM,target)]),0,0,0).enq(chart[0])
    for col in chart:
        for state in col:
            if not state.complete():
                if state.next().isLit():
                    state.scanner(words,chart)
                else:
                    state.predictor(grammar,chart)
        col.sort(lambda x,y: cmp(x.start, y.start)) #TODO:Is there a better (faster?) way to do this?
        for state in col:
            if state.complete():
                if state is findLeast(findSames(state,col)):
                    state.completer(chart)
            else:
                if state.next().isLit():
                    state.scanner(words,chart)
                else:
                    state.predictor(grammar,chart)
        if not col:
            print 'possible error!'
            print util.filter_dups([state.sym.children[0] for state in _firstIfLit(_ifComplete(prevcol))])
            break
        prevcol = col
    return chart
def parse(words, grammar, target='S'):
    """[str]*{str:Symbol}*str->[[State]...] -- Parse with no error correcting

    words -- our supplied POS, grammar is the grammar to parse against,
    target -- the target symbol in the grammar (default 'S' of course)
    returns the parse chart without any parses retrieved"""
    chart = [[] for i in range(len(words)+1)]
    EarleyState(Symbol(Symbol.SYM, "root:", [Symbol(Symbol.SYM,target)]),0,0,0).enq(chart[0])
    for col in chart:
        for state in col:
            if not state.complete():
                if state.next().isLit():
                    state.scanner(words,chart)
                else:
                    state.predictor(grammar,chart)
            else:
                state.completer(chart)
        if not col:
            print 'possible error!'
            print util.filter_dups([state.sym.children[0] for state in _firstIfLit(_ifComplete(prevcol))])
            break
        prevcol = col
    return chart
def retrieveParse(root,wordlist):
    """State*[str]->str -- retrieve parse and build a presentable string version of it"""
    def rp(root,l):
        if root.parents:
            return ('   '*l)+str(root)+''.join([rp(ch,l+1) for ch in root.parents])
        else:
            return ('   '*l)+wordlist[root.start]+" ("+str(root.sym)+')\n'
    return rp(root,0)
def _ifComplete(col):
    """[State]->[State] -- return all incomplete states in the column"""
    return [state for state in col if not state.complete()]
def _firstIfLit(col):
    """[State]->[State] -- return all states whose first symbol is literal"""
    return [state for state in col if state.sym.children[0].isLit()]
def _test():
    import doctest, earley
    doctest.testmod(earley)
if __name__=="__main__":
    _test()
