"""The Pham Nuwen--console edition.

This was the only console interface created *after* the GUI interface.
For you history buffs, I'm sure this is an enlightening piece of information."""
from bigram import POSTagger, TagGram
from util import pprint, splitAdditional, menuLoop
import pickle
fileName = ''
postag = POSTagger()
def loadFile():
	try:
		postag.load(raw_input("Filename%"))
	except IOError:
		print "Can't open file for reading--nothing happens now."
def saveFile():
	try:
		postag.save(raw_input("Filename%"))
	except IOError:
		print "Couldn't open file for writing--nothing happened."
def specGrammar():
	"""Create a new POS tagger, this with a specified POS.
	Right now this must be run before loadFile, because it creates a new POSTagger. This
	is Bad and Wrong, but will be fixed Later."""
	global postag
	try:
		print "Specifying a different grammar will reset the POS tagger.\nTo cancel type nothing at the prompt."
		f=open(raw_input("Filename%"),'r')
		throwAwayGrammar = pickle.load(f)
		postag = POSTagger(pickle.load(f))
	except IOError:
		print "Can't open file for reading--nothing happens now."
def addSentence():
	choice='b00'
	while choice != '':
		#get a new sentence
		choice = raw_input("Enter sentence(nothing to quit)%")
		if choice=='': break
		#split it into words (two steps required for complicated splits)
		words = []
		tmpWords = choice.lower().split()
		for w in tmpWords:
			words.extend(splitAdditional(w, POSTagger.additionalSplits))
		prevPOS = '#'
		posen=[]
		for w in words:
			prevPOS = postag.figurePOS(prevPOS, w)
			posen.append(prevPOS)
		while 1:
			#give output clues
			for i,w,pos in zip(range(len(words)), words, posen):
				print str(i)+'.', w, '\t'*2, pos
			#input desired index (wow this is ugly!)
			i = -1
			try:
				i=int(raw_input("Enter index to edit or anything else to quit%"))
			except ValueError:
				break
			if i not in range(len(words)):
				break
			#get the desired new POS
			print TagGram.POSList
			newpos='$perl vs <OCaml>'
			while newpos not in TagGram.POSList:
				newpos = raw_input('new POS%').upper()
			#set the word to its new POS
			posen[i] = newpos
		postag.figureUnigrams(zip(words,posen))
#main
menuLoop('The Pham Nuwen (Parser I: Part of Speech Identifier)',
		'E(x)it | (S)ave | (L)oad Data | Specify (G)rammar | (A)dd | (H)elp',
		{'s':saveFile, 'l':loadFile, 'a':addSentence, 'g':specGrammar})
