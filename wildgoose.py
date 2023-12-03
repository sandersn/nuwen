"""wildgoose.py--the earley parser console version. The final Jython GUI is Goose.py

This version is retained for compatibility and the happiness of a console version.
It is compatible with both CPython 2.2 and JPython 2.1 and thus will run on almost
any machine, even one without JPython.
The code is so simple that it doesn't really justify commenting--it's just
console interfacing to flip booleans and call a couple of methods.
"""
import earley
from util import findif, menuLoop, loadVars, pprint
def loadFile():
    global grammar
    global POSen
    try:
        grammar, POSen = loadVars(raw_input("Grammar file%"), 2)
    except IOError:
        print "Can't open file for reading--nothing happens now."
def showChart():
    global showchart
    print 'Parse chart is:', showchart and 'on' or 'off'
    showchart = (raw_input("Show parse chart(y/n)%").lower()=='y')#default to off
def showTree():
    global showtree
    print 'Parse tree is:', showtree and 'on' or 'off'
    showparse = (raw_input("Show parse tree(y/n)%").lower()!='n')#default to on
def parseSentence():
    answer = raw_input("%")
    chart = earley.parse(answer.split(), grammar)
    if showchart: print chart
    if showtree:
        root = findif(lambda x:x.sym.sym=='root', chart[-1])
        if root:
            print earley.retrieveParse(root)
        else:
            print 'No valid sentence found'
grammar = {}
POSen = []
showchart=0
showtree=1
while grammar=={}:
    loadFile()
menuLoop("The Wild Goose (Parser II: Parser/Recogniser)",
        '(L)oad Grammar | (P)arse Sentence | List Allowed PO(S)peech\nShow Parse (C)hart? | Show Parse (T)ree? | E(x)it | (H)elp',
        {'p':parseSentence,'c':showChart,'t':showTree,'l':loadFile,'s':lambda:pprint(POSen)})