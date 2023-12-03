#!/usr/bin/python
"""diemremix.py -- The Johnny Diem, the combined POS identifier and parser"""
import cgitb; cgitb.enable() #for nice web-based error reporting
import cgi
import parse
import cfg #for grammar conversion
from postag import POSTagger#for POS id (probabilistic)
import util #for The Kitchen Sink
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
    try:
        grammar, POSen = util.loadVars(fname)
        cfg.convertGrammarToSimple(grammar)
        postagger = POSTagger(POSen)
    except IOError:
        print "Can't open file for reading--nothing happens now."
#Real Code
def addSentence(choice, training=0):
    #split it into words (two steps required for complicated splits)
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
    root = parse.parse(posen, grammar, target, method)
    if root:
        if not words:
            words = ['' for x in posen]
        print parse.retrieve(root,words, method)
    else:
        print 'No valid sentence found'
#phamnuwen
fileName = ''
#end funcs
#load things from form
formdict = cgi.FieldStorage()
input = get(formdict, 'input', '')
target = get(formdict, 'target', "S")
grammarFile = get(formdict, 'grammarFile', 'french_simple.grammar')
trainingFile = get(formdict, 'trainingFile', 'french.postag')
method = get(formdict, 'method', 'earley')
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
    <div class="header" align='center'><h1>Compiler Error Detection and Correction Algorithms applied to Natural Language</h1></div>
        <DIV class="body">

<p>Warning! Right now the error-correcting earley and canonical LR code is <i>very slow</i> since it is experimental only.
So, if you really want to play with the
error correcting parser, please <a href='../nuwen.zip'>download the source</a>. Advantages include having the source,
having the extra grammar files, being able to run the program at 100% CPU instead of 10%, and a bonus
<a href='http://www.wxwindows.org'>wxWindows</a> based grammar
editor. It's extra fruity! For now, the code is released under the
<a href='http://www.xfree86.org/3.3.6/COPYRIGHT2.html#5'>revised BSD licence</a>. (I have done five minutes research
to determine that this is the one that allows users to do anything with the code as long as the author isn't held responsible
(thank you, <a href="http://www.gnu.org/philosophy/license-list.html">gnu.org</a>!)).<p>"""
#start real code?
print postagger, """</p>
<button id='toggleVis' name='toggleVis' onclick="showhide(this);">Advanced &gt;&gt;</button>
<form action='diemremix.py'>
<table border=0 cellpadding=0 cellspacing=0>
    <tr>
        <td>Input:</td><td colspan=3><input type='text' name='input' size='50' value="%s"></td>
    </tr>
    <tr id='methodrow' name='methodrow'>
        <td>Method:</td>
        <td>
            <select id='method' name='method'>
                %s
            </select>
        </td>
    </tr>
    <tr id='targetrow' name='targetrow' style="display:none">
        <td>Target:</td><td><input name='target' size='10' value='%s' ></td><td></td><td></td>
    </tr>
    <tr id='filerow' name='filerow' style="display:none">
        <td>Grammar:</td><td><input name=grammarFile value='%s' ></td>
        <td>Training:</td><td><input name=trainingFile value='%s' ></td>
    </tr>
    <tr>
        <td></td><td><input type='submit' value='Unattended Parse' name='command'></td>
        <td></td><td><input type='submit' value='Parse POSen' name='command' title="Remember to enter POSen!"></td>
    </tr>
</table>
<script language="javascript">
//yes, I am now not only meta-displaying, but meta-programming.
//eval-time has been delayed w00t!
vis = false
function showhide(button) {
  vis = !vis
  var itsa = 'none'
  if(vis)
    itsa = 'inline'
  targetrow.style.display = itsa
  filerow.style.display = itsa
  if(vis)
    button.innerText = "Advanced <<"
  else
    button.innerText = "Advanced >>"
}
</script>
</form><p>"""  % (input, '\n                '.join(["<option value='%s' %s>%s</option>" % \
                     (meth, ['','SELECTED'][(meth==method)], desc) \
                     for meth,desc in zip(parse.methods, parse.methods_desc)]),
                  target, grammarFile, trainingFile)
#sorry for the tricky code. live with it. the second param just makes the current method SELECTED
print input, '</p><pre>'
if input!='':
    despatch({'p':getParse, 's':saveFile,'a':lambda input: addSentence(input, training=1),
                    'u':addSentence, ' ':lambda dummy: None},
                   command, input)
print """</pre>
</div>
</body></html>"""