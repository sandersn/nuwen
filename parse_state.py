"""parse_state.py -- a module for just the State class, which is used in multiple parsers
Other possible names for this module:
_parse
parsen
parse_class
parsers
state
parse_state
"""
from cfg import Symbol
from copy import copy #so I don't have to write copy constructors! huzzah!
class State:
    def __init__(self, sym=Symbol(), progress=0):
        #TODO: Think about changing these varnames to something like rule and maybe cfg.Symbol's also
        #to something like lhand and rhand (or just l r) instead of 
        self.sym = sym#the rewrite rule being used by this state.
        self.progress = progress#index in symbols list
    def __str__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce useful results."""
        return str(self.sym)
    def __repr__(self):
        """None->str
        
        Built-in method to produce string representation. Overidden to produce precise results."""
        return "%r[%r]" % (self.sym,self.progress)
    def __eq__(self,other):
        return (self is other) or (self.sym==other.sym and self.progress==other.progress)
    def __hash__(self):
        return id(self.sym) ^ id(self.progress)
    def __rshift__(self, delta):
        """int->State -- Return a new State with its dot incremented n characters

        Someday State may sprout __lshift__ to dec the dot, too, but not yet.
        You can cheat and rshift negative values, but on your own head be the results!
        Also, on your own head be the exceptions which will result when shifting a non-int delta.
        
        Usage:
        >>> s = State(Symbol(Symbol.ALT, 'A', [Symbol(Symbol.LIT, 'alpha'), Symbol(Symbol.SYM, 'B'), Symbol(Symbol.LIT, 'beta')]), 1)
        >>> s
        (A -> <#alpha# B #beta#>)[1]
        >>> s >> 1
        (A -> <#alpha# B #beta#>)[2]
        >>> #shifting past end just takes dot to end
        >>> s >> 5
        (A -> <#alpha# B #beta#>)[3]
        """
        t = copy(self) #shallow copy kthx
        t.progress += min(delta, len(self.sym.children)-self.progress)
        return t
    def next(self):
        """None->Symbol -- Return the next Symbol in this state's rewrite rule."""
        if self.complete():
            return Symbol() #TODO:Soon change this to return None.
        #...I would do it sooner if it didn't break lr.simple_closure so badly.
        else:
            return self.sym.children[self.progress]
    def complete(self):
        """None->bool -- Return whether this State is complete."""
        return self.progress==len(self.sym.children)
def _test():
    import doctest, parse_state
    doctest.testmod(parse_state) #verbose=True # a little verbose for me ^_^
if __name__=='__main__':
    _test()
