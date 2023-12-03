"""parse.py -- provide a uniform interface to parsing methods

TODO:Change earley.parse and parse_correct to avoid having these baroque lambdas just
to get them to return the root. really!
TODO:Decide what exception to throw from retrieve if passed null root.
(remember parse returns None if it can't find a parse (still may change this tho))
TODO:Make tests, esp for string"""
import lr
import earley
import util
#the Grand Poobah Official List of supported parse methods.
#"The results of changing this are undefined, but could cause demons to fly out of the
#offender's nose"
methods = ['earley', 'earley_correct', 'lr', 'slr', 'lr_fma_french', 'lr_french', 'lr_french_old', 'lr_both_french', 'lr_both_french_old']
#and a nice description of each. ditto!
methods_desc = ['Earley', 'Earley - Correcting', 'Canonical LR(1) - FMA Correcting',
                'Simple LR - FMA Correcting',
                'Canonical LR - FMA French Only', 'Canonical LR - Hand Crafted French',
                'Canonical LR - Old Hand Crafted French',
                'Canonical LR - Both French Only', 'Canonical LR - Both French Only (Old)']
#specific hacks that obviate normal interface to parsers
def _lr_hack(lr_table,general_errors,words,grammar,target):
    table,goto = util.loadVars(lr_table)
    return lr.lr_parse(words+["#"],grammar,table,goto,general_errors)
#end hacks section
#individual function mappings.
_meth = {'lr': lambda words,grammar,target: lr.parse(words,grammar,target, canonical=True),
        'slr':lr.parse, 'lr_fma_french':lambda words,grammar,target:_lr_hack('french_canon.lr',True,words,grammar,target),
        'lr_french':lambda words,grammar,target: _lr_hack('french_canon_err.lr',False,words,grammar,target),
        'lr_both_french':lambda words,grammar,target:_lr_hack('french_canon_err.lr',True,words,grammar,target),
        'lr_french_old':lambda words,grammar,target:_lr_hack('preliminary_err.lr',False,words,grammar,target),
        'lr_both_french_old':lambda words,grammar,target:_lr_hack('preliminary_err.lr',True,words,grammar,target),
        'earley_correct':lambda words,grammar,target: util.findif(lambda x:x.sym.sym=='root:', earley.parse_correct(words,grammar,target)[-1]),
        'earley':lambda words,grammar,target: util.findif(lambda x:x.sym.sym=='root:', earley.parse(words,grammar,target)[-1])}
_retrievalmeth = {'lr':lr.retrieve, 'slr':lr.retrieve,
                'lr_fma_french':lr.retrieve, 'lr_french':lr.retrieve, 'lr_both_french':lr.retrieve,
                'lr_french_old':lr.retrieve, 'lr_both_french_old':lr.retrieve,
                'earley_correct':earley.retrieveParse,
                'earley':earley.retrieveParse}
def parse(words, grammar, target="S", method='earley'):
    """[str]*{str:Symbol}*str->State -- return the root of the parse tree

    words - the parts of speech
    grammar - the BNF grammar in cfg.Symbol tree form
    target - the target symbol of the grammar that is returned as root
    method - the desired parse method (see parse.methods and parse.methods_desc for valid choices)"""
    return _meth[method](words,grammar,target)
def retrieve(root, wordlist, method='earley'):
    """State*[str]*str->str -- give a simple string representation of a parse

    TODO:Decide if this can be written here (generalised) or delegated to various modules to do each their own way.
    TODO:After generalisation (or before), see if util.buildTree can be improved to use here. It needs to track recursion depth"""
    return _retrievalmeth[method](root,wordlist)
def retrieve_html(root, wordlist, method='earley'):
    """NOT IMPLEMENTED -- give a simple string representation of a parse"""
    raise NotImplementedError()
def string(words,lits,grammar,method='earley', target="S"):
    """[str]*[str]*{str:Symbol}*str*str->str -- parse sentence with POS and return a tree in string form

    words - the words for from the source text
    lits - the parts of speech for the text
    grammar - the BNF grammar
    method - the desired parse method (see parse.methods and parse.methods_desc for valid choices)
    target - the target symbol of the grammar that is returned as root"""
    return retrieve(parse(lits,grammar,target, method), list(words), method)
def html(words,lits,grammar,method='earley', target="S"):
    """NOT IMPLEMENTED -- parse sentence with POS and return a tree in string form

    words - the words for from the source text
    lits - the parts of speech for the text
    grammar - the BNF grammar
    method - the desired parse method (see parse.methods and parse.methods_desc for valid choices)
    target - the target symbol of the grammar that is returned as root"""
    raise NotImplementedError()
    return retrieve_html(parse(lits,grammar,target, method), words, method)
if __name__=='__main__':
    grammar, posen = util.loadVars('c:/documents/class/nuwen/french_simple.grammar')
    print string("je nager . #".split(), 'PRON-1-SG INF . #'.split(), grammar, method='lr_french')
##I have decided I don't like white space
##So either this will be like a free-form poem
##(I think they're called ...parseable)
##
##Sometimes I wonder
##If we just did what the machine
##told us, ca ira...?
##
##Descent musicians
##They must have been under the
##influence of greatness
##
##Five seven five is 
##The ultimate in awkward
##only in English
##
##English limerick
##and Japanese Haiku
##language customised
