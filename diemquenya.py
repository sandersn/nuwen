#!/usr/bin/python
"""diemquenya.py

A web based interface to the quenya parser.
Notes:
1.POS is short for 'part of speech'
2.a # indicates that an aside to the reader will follow
3.lighter, triple quoted text at the beginning of a file, function (def)
or class (class) indicates documentation for that section of code.
For the non-technical reader this will of course be the most interesting
reading.
4.#!/usr/bin/python is a magical incantation telling the computer
that one's code is runnable. It is required to be the first line of code in
the first file of one's program. It is pronounced
"hash bang slash user, slash bin, slash python" """
import cgitb; cgitb.enable() #to display errors in the browser
import cgi #for web-based code
import parse #for parsing
import cfg #for grammar conversion
from postag import POSTagger #for POS id (probabilistic)
from util import findif, menuLoop, loadVars, pprint, split_save #for The Kitchen Sink
from web import despatch, get #for web-based menu handling
def loadFile(fname):
    try:
        postagger.load(fname)
    except IOError:
        print "Can't open file for reading--nothing happens now."
def specGrammar(fname):
    """str -- Create a new POS tagger, this with a specified POS.
    Right now this must be run before loadFile, because it creates a new POSTagger.
    This is Bad and Wrong, but will be fixed Later."""
    global postagger
    global grammar
    try:
        grammar, POSen = loadVars(fname, 2)
        cfg.convertGrammarToSimple(grammar)
        postagger = POSTagger(POSen)
    except IOError:
        print "Can't open file for reading--nothing happens now."
#Real Code
def addSentence(choice):
    """str*bool -- add a sentence by identifying the POSen and parsing the sentence"""
    #split it into words (two steps required for complicated splits)
    words = []
    tmpWords = choice.lower().split()
    for w in tmpWords:
        words.extend(split_save(w, POSTagger.additionalSplits))
    prevPOS = '#'
    posen=[]
    for w in words:
        try:
            prevPOS = postagger.figurePOS(prevPOS, w, False)
        except KeyError, correctedWord:
            if correctedWord.args:
                print 'misspelled word "%s" corrected to "%s"' % (w,correctedWord)
                prevPOS = postagger.figurePOS(prevPOS, correctedWord.args[0], False)
                #score-=1 #^_^
            else:
                print 'error: "%s" is not a word in the current lexicon' % w
        posen.append(prevPOS)
    parseSentence(words, posen)
def parseSentence(words,posen):
    """[str]*[str] -- use the Earley parser to parse the sentence"""
    root = parse.parse(posen, grammar, target)
    if root:
        if not words:
            words = ['' for x in posen]
        print parse.retrieve(root,words)
    else:
        print 'No valid sentence found'
#end funcs

#load things from form
formdict = cgi.FieldStorage()
input = get(formdict, 'input', '')
target = get(formdict, 'target', "S")
grammarFile = get(formdict, 'grammarFile', 'quenya.grammar')
trainingFile = get(formdict, 'trainingFile', 'quenya.postag')
showchart = get(formdict, 'showchart', '')
showtree = get(formdict, 'showtree', '')
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
    <div class="header" align='center'>
        <h1>Highly Impressive Quenya Parser</h1>
    </div>
    <DIV class="body">

<p>Please enter a valid Quenya sentence to see the resulting parse.</p><p>"""
#echo input
print postagger, '</p><p>', input, '\n</p><pre>'
#and then print the output
despatch({'u':addSentence, ' ':lambda dummy: None},
               command, input)
print """</pre>
<form action='diemquenya.py'>
    Input:<input type='text' name='input'><br>
    Target:<input name='target' value='%s' ><br>
    Grammar:<input name=grammarFile value='%s' ><br>
    Training:<input name=trainingFile value='%s' ><br>
    <input type='submit' value='Unattended Parse' name='command'>
</form></div>
</body></html>"""  % (target, grammarFile, trainingFile)
