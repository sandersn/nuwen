#!/usr/bin/python
import cgitb; cgitb.enable()
import parse
import util
grammar,posen=util.loadVars('french_simple.grammar')
#methods = ['earley', 'lr_french',  'lr_french_old', 'lr_fma_french', 'lr_both_french', 'earley_correct']
methods = ['lr_fma_french']
sentences=[(['Mes', 'camarade', 'a', 'Jeanne', '.'], ['DET-PL', 'N-F-SG', 'V-3-SG', 'N-F-SG', '.']), 
    (["J'", 'aime', 'la', 'th\xe9', 'citron', '.'], ['PRON-1-SG', 'V-1-SG', 'DET-F-SG', 'N-M-SG', 'ADJ-M-SG', '.']), 
    (['Je', 'parle', 'anglaise', '.'], ['PRON-1-SG', 'V-1-SG', 'ADJ-F-SG', '.']), 
    (['Je', 'parle', 'espagnole', '.'], ['PRON-1-SG', 'V-1-SG', 'ADJ-F-SG', '.']), 
    (['Je', 'ne', 'parle', 'pas', 'fran\xe7aise', '.'], ['PRON-1-SG', 'NE', 'V-1-SG', 'NEG', 'ADJ-F-SG', '.']), 
    (['Je', 'joue', 'basket', 'souvent', '.'], ['PRON-1-SG', 'V-1-SG', 'N-M-SG', 'ADV', '.']), 
    (['Je', 'ne', 'pas', 'aimer', '\xe9tudie', '.'], ['PRON-1-SG', 'NE', 'NEG', 'INF', 'V-1-SG', '.']), 
    (["J'", 'aimer', 'beaucoup', 'mange', '.'], ['PRON-1-SG', 'INF', 'ADV', 'V-1-SG', '.']), 
    (['Je', 'aimer', 'nager', '.'], ['PRON-1-SG', 'INF', 'INF', '.']), 
    (["J'", 'aime', 'mange', 'un', 'sandwich', '.'], ['PRON-1-SG', 'V-1-SG', 'V-1-SG', 'DET-M-SG', 'N-M-SG', '.']), 
    (['Je', 'ne', 'pas', 'aimer', 'un', 'croquemadame', '.'], ['PRON-1-SG', 'NE', 'NEG', 'INF', 'DET-M-SG', 'N-M-SG', '.']), 
    (['Je', "n'", 'aime', 'pas', '\xe9tudie', '.'], ['PRON-1-SG', 'NE', 'V-1-SG', 'NEG', 'V-1-SG', '.']), 
    (['Je', 'lire', 'beaucoupe', '.'], ['PRON-1-SG', 'INF', 'ADV', '.']), 
    (['Je', 'pr\xe9f\xe9rer', 'la', 'Am\xe9ricaine', 'litt\xe9rature', '.'], ['PRON-1-SG', 'INF', 'DET-F-SG', 'ADJ-F-SG', 'N-F-SG', '.']), 
    (["J'", 'aimer', 'beaucoup', 'un', 'jeu', 'vid\xe9o', '.'], ['PRON-1-SG', 'INF', 'ADV', 'DET-M-SG', 'N-M-SG', 'ADJ-M-SG', '.']), 
    (['Je', 'suis', 'aime', 'travaille', '.'], ['PRON-1-SG', 'COPULA-SG', 'V-1-SG', 'V-1-SG', '.']), 
    (['Je', 'ne', 'chantes', 'pas', 'bien', '.'], ['PRON-1-SG', 'NE', 'V-2-SG', 'NEG', 'ADV', '.']), 
    (['Je', 'chr\xe9tien', '.', "#"], ['PRON-1-SG', 'ADJ-M-SG', '.']), 
    (['Je', 'ne', 'parle', 'beaucoup', '.', "#"], ['PRON-1-SG', 'NE', 'V-1-SG', 'ADV', '.']), 
    (['Je', 'chante', 'pas', 'mal', '.', "#"], ['PRON-1-SG', 'V-1-SG', 'NEG', 'ADV', '.']), 
    (['Non', 'je', 'suis', 'pas', 'fume', '.'], ['NE', 'PRON-1-SG', 'COPULA-SG', 'NEG', 'V-1-SG', '.']), 
    (['Mes', 'camarade', 'a', 'Jeanne', '.'], ['DET-PL', 'N-F-SG', 'V-3-SG', 'N-F-SG', '.'])]
print "Content-Type:text/html\n\n"
print "<html><body><pre>"
for meth in methods:
    print "\t\t~~~%s~~~\n\n" % meth
    for lits,words in sentences:
        print lits
        try:
            print parse.string(lits, words, grammar, meth,"S")
        except AttributeError,e: #earley standard parse error
            print e
            continue
        except KeyError, e: #lr parse error
            print e
            continue
print "</pre></body></html>"