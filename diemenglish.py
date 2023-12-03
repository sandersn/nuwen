#!/usr/bin/python
"""diemenglish.py -- specialised english Earley parser. Strictly a museum piece right now.
It will soon be coming down from the web site to be replaced by an improved diemremix.py
"""
import cgitb; cgitb.enable() #yah just in case
import cgi
import parse
import cfg #for grammar conversion
from postag import POSTagger #for POS id (probabilistic)
from util import findif, menuLoop, loadVars, pprint, split_save #for The Kitchen Sink
from web import despatch, get
def loadFile(fname):
    try:
        postagger.load(fname)
    except IOError:
        print "Can't open file for reading--nothing happens now."
def saveFile():
    try:
        postagger.save(raw_input("Part of speech training filename%"))
    except IOError:
        print "Couldn't open file for writing--nothing happened."
def specGrammar(fname):
    """Create a new POS tagger, this with a specified POS.
    Right now this must be run before loadFile, because it creates a new POSTagger. This
    is Bad and Wrong, but will be fixed Later."""
    global postagger
    global grammar
#    global POSen
    try:
        grammar, POSen = loadVars(fname, 2)
        cfg.convertGrammarToSimple(grammar)
        postagger = POSTagger(POSen)
    except IOError:
        print "Can't open file for reading--nothing happens now."
#Real Code
def addSentence(choice, training=0):
    #split it into words (two steps required for complicated splits)
    words = []
    tmpWords = choice.lower().split()
    for w in tmpWords:
        words.extend(split_save(w, POSTagger.additionalSplits))
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
        posen.append(prevPOS)
    if training:
        posen = correctPOS(words,posen)
        if posen:
            postagger.figureUnigrams(zip(words,posen))
            parseSentence(words,posen)
    else:
        parseSentence(words, posen)
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
    root = parse.parse(posen, grammar, target)
    if root:
        if not words:
            words = ['' for x in posen]
        print parse.retrieve(root,words)
    else:
        print 'No valid sentence found'
#phamnuwen
fileName = ''
#end funcs
#load things from form
formdict = cgi.FieldStorage()
input = get(formdict, 'input', '')
target = get(formdict, 'target', "S")
grammarFile = get(formdict, 'grammarFile', 'eng.grammar')
trainingFile = get(formdict, 'trainingFile', 'eng.postag')
command = get(formdict, 'command', ' ')
specGrammar(grammarFile)
loadFile(trainingFile)
print "Content-Type:text/html\n\n"
print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
	<HEAD>
		<TITLE>Hejmpagho de ZackMan</TITLE>
		<STYLE>@import url( ../../style.css ); </STYLE>
	</HEAD>
	<BODY bgColor="#000033">
	<div class="header" align='center'><h1>Earley's Parser with a Decent English Grammar</h1></div>
		<DIV class="body">

<p>For now, please click 'Unattended Parse' always. The others are advanced, and don't work yet besides.</p><p>"""
#start real code?
print postagger, '</p><p>', input, '\n</p><pre>'
#Should this print a return value or have the func print stuff?
despatch({'p':getParse, 's':saveFile,'a':lambda input: addSentence(input, training=1),
                'u':addSentence, ' ':lambda dummy: None},
               command, input)
print """</pre>
<form action='diemenglish.py'>
    Input:<input type='text' name='input'><br>
    Target:<input name='target' value='%s' ><br>
    Grammar:<input name=grammarFile value='%s' ><br>
    Training:<input name=trainingFile value='%s' ><br>
    <input type='submit' value='Unattended Parse' name='command'>
    <input type='submit' value='Parse POSen' name='command'>
    <input type='submit' value='Add Sentence' name='command'>
</form></div>
</body></html>"""  % (target, grammarFile, trainingFile)
