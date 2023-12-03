"""diem.py--The Johnny Diem, the combined POS identifier and parser

Constructed from the remains of the Pham Nuwen and the excess of the Wild Goose,
the Johnny Diem assumes that you have trained your grammar/pos probabilities enough
that you really have to correct the POS identifier very little. And of course, the Earley
algorithm that I implemented is deterministic, so doesn't need training, just a good grammar.
TODO:Figure a way for proper nouns to be skipped or ided"""
import parse
import cfg #for grammar conversion
from postag import POSTagger #for POS id (probabilistic)
import util #for The Kitchen Sink
#bookkeeping
def loadFile():
    try:
        postagger.load(raw_input("Part of speech training filename%"))
    except IOError:
        print "Can't open file for reading--nothing happens now."
def saveFile():
    try:
        postagger.save(raw_input("Part of speech training filename%"))
    except IOError:
        print "Couldn't open file for writing--nothing happened."
def specGrammar():
    """Create a new POS tagger, this with a specified POS.
    Right now this must be run before loadFile, because it creates a new POSTagger. This
    is Bad and Wrong, but will be fixed Later."""
    global postagger
    global grammar
    try:
        grammar, POSen = util.loadVars(raw_input("Grammar file%"))
        cfg.convertGrammarToSimple(grammar)
        postagger = POSTagger(POSen)
    except IOError:
        print "Can't open file for reading--nothing happens now."
def specTarget():
    global target
    target = raw_input("Parse target POS(default is 'S')%")
    if not target:
        target='S'
def specMethod():
    global method
    method = raw_input("Method(%s)%%" % " | ".join(parse.methods))
    if not method:
        method = "earley"
def showChart():
    global showchart
    print 'Parse chart is:', showchart and 'on' or 'off'
    showchart = (raw_input("Show parse chart(y/n)%").lower()=='y')#default to off
def showTree():
    global showtree
    print 'Parse tree is:', showtree and 'on' or 'off'
    showtree = (raw_input("Show parse tree(y/n)%").lower()!='n')#default to on
#Real Code
def addSentence(training=0):
    choice='b00'
    while choice != '':
        #get a new sentence
        choice = raw_input("Enter sentence(nothing to quit)%")
        if choice=='': break
        #split it into words (first on whitespace, then using re for everything else)
        words = util.flatten([util.split_save(w, POSTagger.additionalSplits) for w in choice.lower().split()])
        prevPOS = '#'
        posen=[]
        for w in words:
            try:
                prevPOS = postagger.figurePOS(prevPOS, w, training)
            except KeyError, correctedWord:
                if correctedWord.args:
                    print 'misspelled word "%s" corrected to "%s"' % (w,correctedWord)
                    prevPOS = postagger.figurePOS(prevPOS, correctedWord.args[0], training)
                    #score-=1 #^_^
                else:
                    print 'error: "%s" is not a word in the current lexicon' % w
                    return
            posen.append(prevPOS)
        if training:
            posen = correctPOS(words,posen)
            if posen:
                postagger.figureUnigrams(zip(words,posen))
                parseSentence(words,posen)
        else:
            parseSentence(words, posen)
            if raw_input("Add this sentence to training data?").lower()[0]=='y':
                #TODO:Give the option to correct POS (but this is very low priority)
                postagger.figureUnigrams(zip(words,posen))
def getParse():
    parseSentence([],raw_input("%").split())
def correctPOS(words,posen):
    while 1:
        #give output clues
        print '\n'.join(["%s.%s\t\t%s" % (i,w,pos) for i,w,pos in zip(range(len(words)), words, posen)])
        #input desired index (wow this is ugly!)
        i = -1
        try:
            i=int(raw_input("Enter index to edit, oorange to cancel or anything else to parse sentence%"))
        except ValueError:
            break
        if i not in range(len(words)):
            return None
                #get the desired new POS
        print postagger.POSList
        newpos='$perl vs <OCaml>'
        while newpos not in postagger.POSList:
            newpos = raw_input('new POS%').upper()
        #set the word to its new POS
        posen[i] = newpos
    return posen
def parseSentence(words,posen):
    root = parse.parse(posen, grammar, target, method)
    if showtree:
        if root:
            if not words:
                words = ['' for x in posen]
            print parse.retrieve(root,words, method)
        else:
            print 'No valid sentence found'
#phamnuwen
fileName = ''
postagger = POSTagger()
#wildgoose
grammar = {}
target = "S"
method = "earley" #The Easy Way
showchart=0
showtree=1
while grammar=={}:
    specGrammar()
util.menuLoop("The Johnny Diem (Parser II+III: POS ID+Parser)",
        """(S)ave POS training | (L)oad POS | Load (G)rammar | (A)dd Sentence
(P)arse POSen | (U)nattended Parse | Specify Ta(r)get POS | Specify Parse (M)ethod
Show Parse (C)hart? | Show Parse (T)ree? | E(x)it | (H)elp""",
        {'p':getParse,'c':showChart,'t':showTree,'g':specGrammar,
         's':saveFile,'l':loadFile,'a':lambda: addSentence(training=1),'u':addSentence,
         'r':specTarget,'m':specMethod},
         lambda: util.pprint(postagger))
