The principal executable files are
invisiblehand.py -- Grammar builder
diem.py -- POS trainer and parser
waApp1.py -- Bonus grammar builder GUI (requires wxWindows and wxPython)

waApp1.py is in the very early stages of development (as it doesn't even have a name yet).
It may never become any more advanced, because The Invisible Hand can parse
correctly formatted text files in one go, which is really easier.

The actual work is performed in the following files:
cfg.py -- Extended BNF grammar support
earley.py -- Implementation of Earley's parser (and error-correcting modification)
gram.py -- Statistical word-counting classes
lr.py -- Implementation of LR parsing (with error-correcting FMA)
parse.py -- Interface to parsing
parse_state.py -- Just the parent class for holding parse trees.
postag.py -- Part of speech identification
util.py -- Many small utility functions
web.py -- A few cgi specific utilities
----
french.grammar -- Example of small grammar 
frgrammar.txt -- Source for said grammar
french.postag -- *extremely* small POS training corpus.

I have not included the web equivalents to diem.py. I might later.
The names of the executable files are ship names
from Vernor Vinge's novel _A Deepness in the Sky_.

No documentation other than what's in the source so far.
I'm investigating the documentation generator capabilities that come with the
Python distro, and will probably modify that.