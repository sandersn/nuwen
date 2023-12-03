"""A collection of all the utilities I have created in the process of making the parser

Some of these are improvements on things Python has. Others are things Python may actually
have, and I didn't know about. Anyway, here they are. enjoy!
Note on docstrings. I use a notation to describe passing/returning types which is similar to ML's
notation. Here is how it works:
type*type -> returntype
int, str, float are the basic scalar types.
[], (), {} are the basic compound types.
fn, file, Any and None are some other ones.
type... indicates that an arbitrary number of type can be passed in that position.
Classes are represented by their class names, e.g. Symbol and Node.
Compound types (while actually heterogenous) are indicated as to what type they should contain,
if there is any homogeneaity to speak of, e.g. [Symbol].
This system can be nested arbitrarily deeply. Here are some examples:
    This example does not care what is in the list, although presumably fn might
        fn*[] -> []
    This function might obtain a string list from a transform specified by fn over the int list.
        fn*[int] -> [str]
    This function takes a list of int 2-tuples and returns an int list
        [(int*int)...] -> [int]
    This function has a variable arglist, but expects them all to be ints:
        int... -> int
TODO:Figure out how best to split these into two files.
Right now I'm thinking IO ops and list/tree/string ops is the best split
pprint,menuLoop,loadVars,saveVars should be io, everything else in the other.
the good clues are that the IO funcs don't return anything
TODO:Change all frontends to use loadVars and saveVars for their file I/O"""
from __future__ import nested_scopes
import types
import pickle
#provides a handy dict in case you want to make decisions which require matching one brace type
#to another. I may add more exotic matches later.
bracematch={'[':']', "{":"}", "(":")", "<":">"}
def pprint(o):
	"""Pretty prints dicts, lists, and tuples each element on its own line. Otherwise just prints object

	This is less complicated than the pprint module and loses some information"""
	if type(o)==types.DictType:
		for sym,struct in o.items():
			print sym, '\t', struct
	elif type(o)==types.ListType or type(o) == types.TupleType:
		for i in o:
			print i
	else:
		print o
def menuLoop(splash, help, menuitems, menufn=None):
	"""str*str*{str:func}*func -> None

	Does a simple menu loop with x or blank leaving it.
	splash is the splash string. List product name and version, etc.
	help is the help string. List the functions and which letter goes with what, preferably
	menuitems is a hash with key the string one types bound to the function it invokes.
	Strings should be one lowercase letter. This may change to something more flexible tho.
	(something like Unixes least-typing-required cmd line args)
	The optional menufn is called at each iteration of the menu display
	Functions should take no arguments and return None"""
	if menufn is None:
		menufn = lambda: None
	choice = 'blah'
	print splash
	print help
	while 1:
		menufn()
		choice = raw_input('%')
		if choice=='' or choice.lower()=='x': return
		choice = choice.lower()[0]
		if choice in menuitems:
			menuitems[choice]()
		else:
			print help
def loadVars(fname, n):
    """str*int->[] Load (unpickle) n variables from fname"""
    f = open(fname, 'r')
    return [pickle.load(f) for i in range(n)]
    f.close()
def saveVars(fname, *vars):
    """str*any... -> None Save (pickle) vars to fname"""
    f = open(fname, 'w')
    for v in vars:
        pickle.dump(v,f)
    f.close()
def splitAdditional(word, splits):
	"""str*(str|[str])->[str] Splits a given word recursively based on the string array of splits

	Pass a string for the second argument to use one-character splits. Pass a list of strings
	to split on any length of string."""
	answer=[]
	for spl in splits:
		idx = word.find(spl)
		if idx > -1:
			if word[:idx] != '':
				answer.extend(splitAdditional(word[:idx],splits))
			answer.append(spl)
			if word[(idx+len(spl)):] != '':
				answer.extend(splitAdditional(word[(idx+len(spl)):],splits))
			return answer
	return [word]
def bipartiteFilter(fn, l):
	"""fn*[]->([],[]) Returns the two halves of a list, divided on whether fn returns true or false.

	True half is returned first so as to mimic filter if you want to ignore the second half.
	Same as
	return filter(fn, l), filter(not fn, l)
	WARNING:This is the current version because I'm not sure which is faster. But the first is clearer."""
	return filter(fn, l), filter(lambda x:not fn(x), l)
#	t = []; f = []
#	for x in l:
#		if fn(x): t.append(x)
#		else: f.append(x)
#	return t,f
def stepSplit(l, step):
	"""Divides l into step sublists. Each sublist contains every stepth element of l.

	This is a replacement for the code [l[i:len(l):step] for i in range(step)]. Unfortunately, I couldn't get
	extended slice notation to work. Maybe it is only available to NumPython implementations?"""
	return [[l[j] for j in range(i,len(l),step)] for i in range(step)]
def findif(fn, l):
	"""Returns first item in l for which fn is true, None if none are."""
	for i in l:
		if fn(i): return i
def avg(l):
	"""Average a list of numbers."""
	if len(l):	return reduce(lambda x,y: x+y, l, 0) / float(len(l))
	else: return 0
def avglists(*lists):
	"""Averages multiple lists of numbers"""
	return [avg(l) for l in lists]
def permutations(n):
	"""[[]...] -> [[]...] Return all permutations of lists in n.

	Examples:
	>>> util.permutations([[1],[2,3],[3]])
	[[1, 2, 3], [1, 3, 3]]
	>>> util.permutations([[1,2,3],[2],[3]])
	[[1, 2, 3], [2, 2, 3], [3, 2, 3]]"""
	if not cdr(n):
		return [[x] for x in car(n)]
	else:
		P=permutations(cdr(n))
		answer=[]
		for x in car(n):
			answer.extend([[x]+rest for rest in P])
		return answer
def car(l):
	"""Yeah, so I broke down and wrote car and cdr functions. Leave me alone!"""
	return l[0]
def cdr(l):
	"""I'm not addicted! errrrr I lie. Maybe I *am* addicted. -_-"""
	return l[1:]
def areAllEqual(first,second):
	"""Returns true if all items in lists first and second are equal, false otherwise"""
	return reduce(lambda x,y: x and y, map(lambda primero,segundo: primero==segundo, first, second), 1)
def merge(l1,l2):
	"""Append only the items in l2 to l1 that are not already in l1. []*[]->[]"""
	return l1 + filter(lambda x: x not in l1, l2)
def filterDuplicates(l):
	"""Remove all duplicates from list l. [] -> []"""
	m=[]
	for x in l:
		if x not in m:
			m.append(x)
	return m
def buildTree(root, fnconvert, fnchildren, fnadd):
	"""Build one tree from another, given root<a>. Returns root<b>.

	root is the root of the tree<a>.
	fnconvert(node<a>) -> node<b>
	fnchildren(node<a>) -> sequence of children<a>
	fnadd(node<b>, sequence of children<b> to be added) -> node<b> with children<b> added
	Note that despite the template syntax used in this description, Python does *not* enforce types
	ahead of time, so there isn't any compile-time checking going on (unlike OCaML or something)."""
	def build(node1):
		return fnadd(fnconvert(node1), [build(ch) for ch in fnchildren(node1)])
	return build(root)
def addAll(node, l):
	"""Provides an iteration over an add function (required method of node)

	This is provided because Java doesn't have addAll everywhere I thought it did,
	so I had to implement it myself for some classes -_-
	I didn't want to subclass DefaultMutableTreeNode because that would be too much work
	just for adding a single method, so I compromised by adding the function here."""
	for x in l:
		node.add(x)
	return node