"""The Invisible Hand. Interface to my context free grammar code.

Allows one to add, remove, update, and delete grammar entries. Yes indeed.
I only commented addSym because it's the only one with enough code to justify it.
"""
import cfg
import util
import sys
grammar = {}
POSen = ['#'] #this list still might better be represented as a dict to allow easier singleton enforcement
#(just set POSen['POS']=1 if it exists)
def loadFile():
	global grammar
	global POSen
	try:
		grammar, POSen = util.loadVars(raw_input("Filename%"))
	except IOError:
		print "Can't open file for reading--nothing happens now."
def saveFile(fname=None):
	if not fname:
		fname=raw_input("Filename%")
	try:
		util.saveVars(fname, grammar, POSen)
	except IOError:
		print "Couldn't open file for writing--nothing happened."
def convertTextFile(fname=None):
    global POSen
    if not fname:
        fname=raw_input("Textfilename%")
    for line in file(fname, 'r'):
        line = line.strip()
        #check for blanks or comments
        if not line or line[0]==';' or line[0]=='#':
            continue
        choice, symbols = line.split('->')
        #first split on whitespace, then on punctuation (saving it)
        symlist = util.flatten([util.split_save(w, "(){}[]|") for w in symbols.split()])
        sym = cfg.gen_symbol(cfg.Symbol(cfg.Symbol.PAREN,choice), symlist)
        grammar[choice] = sym
        POSen = util.merge(POSen, util.filter_dups(sym.extractPOS()))
    print 'Parts of speech:'
    POSen.sort()
    util.pprint(POSen)
    print 'Grammar:'
def convertToSimpleBNF():
    cfg.convertGrammarToSimple(grammar)
def addSym():
	"""Procedure: Get symbol, then equivalence symbols.
	Parse them into a tree representation, then display for confirmation.
	If the item already exists in the grammar, allow one to cancel, overwrite the existing, or add as an alternate (|)"""
	global POSen
	choice='b00'
	while choice != '':
		choice = raw_input("Enter symbol(nothing to quit)%")
		if choice=='': break
		#first split on whitespace, then on punctuation (saving it)
		symlist = util.flatten([util.split_save(w, "(){}[]|") for w in raw_input("Enter equivalence symbols%").split()])
		sym = cfg.gen_symbol(cfg.Symbol(cfg.Symbol.PAREN,choice), symlist)
		print sym
		promptGood=raw_input("Koreha,iidesuka%").lower()
		if not promptGood or promptGood[0] != 'n':
			if choice in grammar:
				ans = raw_input("Konoerabuha,grammardearu. (A)dd, (O)verwrite, (C)ancel%").lower()[0]
				if ans=='a':
					temp = cfg.Symbol(cfg.Symbol.ALT)
					temp.add(sym)
					grammar[choice].add(temp)
				elif ans=='o':
					grammar[choice]=sym
			else:
				grammar[choice]=sym
			POSen = util.merge(POSen, util.filter_dups(sym.extractPOS()))
			#for those of you interested in the thought process of functional vs imperative, here is the imperative version:
			#for pos in extractPOS(sym):
			#   if pos not in POSen:
			#       POSen.append(pos)
def removeSym():
	choice = raw_input("Enter symbol%")
	if choice=='': return
	if grammar.has_key(choice):
		print grammar[choice]
		if raw_input("Delete this%").lower()[0]=='y':
			del grammar[choice]
	else:
		print 'Symbol not found in grammar'
def addPOS():
	choice='pikabu!~~'
	while choice!='':
		choice=raw_input("Enter part of speech(nothing to quit)%")
		if choice=='':break
		POSen.append(choice)
def removePOS():
	choice = raw_input("Enter symbol%")
	if choice=='': return
	if choice in POSen:
		print POSen[POSen.index(choice)]
		if raw_input("Delete this%").lower()[0]=='y':
			POSen.remove(choice)
	else:
		print 'POS not found in list'
def main():
	if len(sys.argv) > 1:
		convertTextFile(sys.argv[1])
		if len(sys.argv) > 2:
			saveFile(sys.argv[2])
			sys.exit(0)
	util.menuLoop('The Invisible Hand (Parser III: CFG Builder)',
		"""E(x)it | (S)ave | (L)oad | (A)dd | (D)elete
(V)iew POS | Add (P)OS | (R)emove POS
Convert Text (F)ile | (C)onvert to Simple BNF | (H)elp

command line usage:
invisiblehand.py [in_grammar.txt [out_grammar.grammar]]
Each line of input should follow form
S->NP VP""",
		{'s':saveFile, 'l':loadFile, 'a':addSym, 'd':removeSym,
			'v':(lambda: util.pprint(POSen)), 'p':addPOS, 'r':removePOS,'c':convertToSimpleBNF,'f':convertTextFile},
		lambda: util.pprint(grammar))
if __name__=='__main__':
	main()
	
