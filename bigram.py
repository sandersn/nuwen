#import re
import sys
from math import log
import cPickle
"""module bigram:Classes for bigram POS analysis

Classes on which my bigram part of speech analyser is based:
Gram, the base class for any sequence of words--the only thing we care about now is frequency
TagGram, the class that connects a gram with a POS
Unigram, holder of a single word plus its TagGram
Bigram, holder of two Unigrams
--Trigram may eventually be implemented--
POSTagger is the controlling class which implements smoothing and bigram generation based
"""

class Gram:
    """Base class for grams of various denominations

    The only common functionality right now is the ability to hold a count
    and figure probabilities and logprobs from that count.
    Being a Gram does not imply that a class directly contains strings.
    I think most Grams include a Unigram within themselves

    Anyway, Gram is parent to a very linked class hierarchy: TagGrams are held in dict inside of Unigrams.
    Two Unigrams are held within every Bigram (and soon three within every Trigram)"""
    __safe_for_unpickling__ = True
    def __init__(self, count = 1):
        self.count = count
        self.freq = 0.0
        self.logfreq = 0.0
    def figFreq(self, total):
        """ Figure frequency of this gram given the total count
        
        NOTE:self.count must be > 0 or a MathError will be thrown.
        However, I am not catching it at this level because I assume that you
        *want* all frequencies to be > 0 (eg via smoothing or something)."""
        self.freq = self.count / float(total)
        self.logfreq = -log(self.freq)
    def __str__(self):
        return 'Count: ' + str(self.count) + ' Freq: ' + str(self.freq) + ' Log Freq: ' + str(self.logfreq)
class TagGram(Gram):
    """Holds a part of speech and its frequency.

    Not associated with a word. It can thus be useful
    for things that are non-terminal symbols in a CFG, too.
    """
    #here we have the C5 POS list (for English) so that the POS can be valid
    C5POS = ['AJ0','AJC','AJS','AT0','AV0','AVQ',
             'CJC','CJS','CJT','CRD','DPS','DT0','DTQ','EX0','ITJ','NN0',
             'NN1','NN2','NP0','ORD','PN1','PNP','PNQ','PNX','POS','PRF',
             'PRP','PUL','PUN','PUQ','PUR','TO0','UNC','VBB','VBD','VBG',
             'VBI','VBN','VBZ','VDB','VDD','VDG','VDI','VDN','VDZ','VHB',
             'VHD','VHG','VHI','VHN','VHZ','VM0','VVB','VVD','VVG','VVI',
             'VVN','VVZ','XX0','ZZ0','#']
    #this is the 'Restricted' POS list from Chanod et Tapanainen, 1995
    #They were using a different method of tagging, however.
    FRRESPOS = ['DET-SG', 'DET-PL', 'ADJ-INV', 'ADJ-SG', 'ADJ-PL',
                'NOUN-INV', 'NOUN-SG', 'NOUN-PL', 'VAUX-INF', 'VAUX-PRP',
                'VAUX-PAP', 'VAUX-P1P2', 'VAUX-P3SG', 'VAUX-P3PL',
                'VERB-INF', 'VERB-PRP', 'VERB-P1P2', 'VERB-P3SG',
                'VERB-P3PL', 'PAP-INV', 'PAP-SG', 'PAP-PL', 'PC', 'PRON', 'PRON-P1P2',
                'VOICILA', 'ADV', 'NEG', 'PREP', 'CONN', 'COMME', 'CONJQUE', 'NUM',
                'HEURE', 'MISC', 'CM', 'PUNCT', '#']
    POSList = FRRESPOS
    __safe_for_unpickling__ = True
    def __init__(self, POS = "", count = 1):
        Gram.__init__(self, count)
        #if POS in TagGram.C5POS:
        if POS in TagGram.POSList:
            self.POS = POS
        else:
            #raise ValueError('C5 tagset POS required. See Garside, et al., 1997 for complete list')
            #raise ValueError(POS + ':"Restricted" tagset POS required.\nSee Chanod and Tapanainen, 1995 for complete list')
            raise ValueError(POS + ':not in valid list of of POSen. See bigram.TagGram.POSList for valid options.')
    def __str__(self):
        return Gram.__str__(self) + ' POS: ' + self.POS

class Unigram(Gram):
    """Holds a unigram (id est, only cares about one word at a time)

    Tracks a word, holds a list of seen parts of speech for this word, and
    holds a list of words that come *after* this word.
    
    NOTE:Since a unigram contains other Gram objects, changing its count should alter the count
    of the contained objects. However, the current implementation does not do this. Be aware of this.
    """
    __safe_for_unpickling__ = True
    def __init__(self, word = "", count = 1):
        Gram.__init__(self, count)
        self.word = word
        self.__POS = {} #{str:TagGram}. Key may eventually become an enum of legal POSen
        self.__afterWords = [] #list of unigrams that came after this unigram
    def __str__(self):
        return str(self.word) + ': ' + Gram.__str__(self) #no POS display right now -_-
    def figFreq(self, total):
        Gram.figFreq(self, total)
        for pos in self.__POS.values():
            pos.figFreq(self.count)
    def addPOS(self, POS):
        """Increment(or add) a part of speech for this unigram"""
        if self.__POS.has_key(POS):
            self.__POS[POS].count += 1
        else:
            self.__POS[POS] = TagGram(POS)
        #(re)figure frequency, based on this unigram's total(no smoothing yet)
        self.__POS[POS].figFreq(self.count)
    def overwritePOS(self, POS):
        """Nuke the current POS list and replace with a new one"""
        self.__POS = POS
    def getPOS(self):
        """Return a TagGram dict of possible parts of speech for this unigram"""
        return self.__POS
    def addAfterWord(self, uni):
        """Add a unigram that appears after this unigram"""
        self.__afterWords.append(uni)
    def getAfterWords(self):
        """Return an list of unigrams after which this unigram occurred """
        return self.__afterWords

class Bigram(Gram):
    """Holds a bigram
    
    This contains two unigrams. Other than that, this class is, uh, pretty boring."""
    __safe_for_unpickling__ = True
    def __init__(self, uni1, uni2, count = 1):
        Gram.__init__(self, count)
        self.words = (uni1,uni2) #store the words in a tuple so they're immutable
    def __str__(self):
        return self.words[0].word  + ' / ' + self.words[1].word + ': ' + Gram.__str__(self)
class POSTagger:
    """ Class provides a learning POS tagger and unigram/bigram/trigram analyser

    All data is pickled to a file and loaded from said file in the following order:
    unigram, prev, prevtotals, POSfreq, POStotal (although not tupled)
    bigram is _not_ saved or restored because
        1)its size is too large
        2)it can be generated from available unigram data
        3)its use is not pertinenent to the current application I am developing"""
    #provides data on non-whitespace splitting chars
    #TODO:Declare french (euro?) encoding  for the french quotes
    additionalSplits = ['-','.', ',', '!', ':','?',"'",'"','(','[','{',')',']','}','«','»'] 
    additionalSplitsEN = ['--','.', ',', '!', ':','?','"','(','[','{',')',']','}', "n't"]

    __safe_for_unpickling__ = True
    def __init__(self, POSList=TagGram.FRRESPOS, fileName=''):
        """fileName provides an initial load, but of course this isn't strictly required."""
        self.loaded = 0
        #these are the previously acquired data, if any
        self.unigram= {} # {unigram text:Unigram}
        self.bigram = {} #{bigram text:Bigram}
        #setup probability P(POS|prevPOS)
        self.prev = {}
        self.prevtotals = {}
        TagGram.POSList=POSList
        for ppos in POSList:
            self.prev[ppos] = {}
            self.prevtotals[ppos] = 0
            for pos in POSList:
                self.prev[ppos][pos] = Gram()
        self.prevtotals['#']=1  #for the first sentence, so it doesn't crash with ArithmeticError
        #setup probability P(POS|"word")
        self.POSfreq = {}
        self.POStotal = 0
        for pos in POSList:
            self.POSfreq[pos] = Gram()
        #load file after initilisiation (if provided)
        if fileName != '':
            self.load(fileName)
            self.loaded = 1
    def __str__(self):
        #TODO:Sort self.unigram.keys() first? Except that the built-in sort is destructive, so I would have to write
        #temp = self.unigram.keys()
        #temp.sort()
        #and that's just ugly(esp ~temp~..what kind of name is *that*?), but....
        return "Lexicon size:%d\t\tLexicon:\n%s" % (len(self.unigram), ' | '.join(self.unigram.keys()))
    def load(self,fileName):
        """Unpickle required class data from fileName. USE ONLY ONCE PER INSTANCE."""
        if self.loaded:
            raise Exception("This object already has loaded state. Please create a new instance of POSTagger")
        else:
            f = open(fileName, 'rb')
            self.unigram = cPickle.load(f)
            self.prev = cPickle.load(f)
            self.prevtotals = cPickle.load(f)
            self.POSfreq = cPickle.load(f)
            self.POStotal = cPickle.load(f)
            f.close()
            self.loaded=1
    def save(self,fileName):
        """Pickle required class data to fileName"""
        f = open(fileName,'wb')
        cPickle.dump(self.unigram,f, True)
        cPickle.dump(self.prev,f, True)
        cPickle.dump(self.prevtotals,f, True)
        cPickle.dump(self.POSfreq,f, True)
        cPickle.dump(self.POStotal,f, True)
        f.close()
        self.loaded=1
    def figureUnigrams(self, words):
        """[(str,str)...] -- words is a list of doubles thus: (word,POS)"""
        prevUni = Unigram('#') #the beginning unigram
        prevUni.addPOS("#")
        prevPOS='#'
        #process unigrams
        for word,POS in words:
            if self.unigram.has_key(word):
                self.unigram[word].count += 1
            else:
                self.unigram[word] = Unigram(word)
            uni=self.unigram[word] #alias for efficiency and readability
            uni.addPOS(POS)
            #now add this unigram to the list of ones that the previous word has seen
            #and then set current to be the previous unigram
            prevUni.addAfterWord(uni)
            prevUni = uni
            #maintain P(POS|prevPOS)
            self.prevtotals[POS]+=1
            self.prev[prevPOS][POS].figFreq(self.prevtotals[prevPOS])
            prevPOS = POS
            #maintain P(POS|"word")
            self.POStotal+=1
            self.POSfreq[POS].figFreq(self.POStotal)
        thend = Unigram('#')
        thend.addPOS('#')
        prevUni.addAfterWord(thend)
        for uni in self.unigram.values():
            uni.figFreq(len(self.unigram))
        return self.unigram #for happiness!
    
    def figureBigrams(self):
        """Figures the bigram probability given a complete list of unigrams
        
        New and improved! Dependent solely on unigram being persistent--bigram is rebuilt into memory
        from it due to the fact that Unigrams maintain a pointer to the previous word. Unigram would have to change
        to accomodate a class Trigram tho.
            #the grand poobah Witten-Bell Method C smoothing equations:
            #   in bigram:
            #count * (N / (N + T))
            #   not in bigram:
            #(T / Z) * (N / (N+T))
            #       where...
            #   N = unigram[uni].count
            #   T = cBigramTypes
            #   Z = len(unigram) - T
        """
        for uni in self.unigram.values():
            #add bigrams that we've seen in the corpus
            cBigramTypes = 0
            for second in uni.getAfterWords():
                bigramtext = ' '.join((uni.word, second.word))
                if(self.bigram.has_key(bigramtext)):
                    self.bigram[bigramtext].count += 1
                else:
                    self.bigram[bigramtext] = Bigram(uni, second)
                    cBigramTypes += 1
            #normalise the bigrams and smooth the ones we've never seen in the corpus
            for k in self.unigram.values():
                #I really *should* put code in here to skip the case where k==uni. I really would, if I could -strums guitar-
                temp = ' '.join((uni.word, k.word))
                if(self.bigram.has_key(temp)):
                    #exists, so depreciate by the count
                    self.bigram[temp].count *= uni.count / (uni.count + float(cBigramTypes))
                else:
                    #!exists, so smooth
                    self.bigram[temp] = Bigram(uni, k)
                    self.bigram[temp].count = (cBigramTypes / (len(self.unigram) - float(cBigramTypes))) \
                                                    * (uni.count / (uni.count + float(cBigramTypes)))
                #now normalise the bigram
                self.bigram[temp].figFreq(uni.count)
                print self.bigram[temp]
        return self.bigram #yizza.
    def figurePOS(self,prevPOS,w,training):
        """str*str*bool->str-- Figures out the best POS for a given word.

        Throws KeyError when w is not in the lexicon and training is False.
        The string associated with the KeyError is NOT w, but the closest word
        to w in the lexicon, or None if there are no close matches.
        
        This is based on its unigram and bigram frequencies. If the word does not yet
        exist in the unigram hash, it is guessed to be the most common POS that comes after the
        previous POS.
        If the word does exist, it is guessed on three successively better premises.
        First, it is set to be NOUN-SG as the 'most common' POS.
        Next it is given the POS with the highest unigram frequency for that word.
        This is right about 90% of the time [Jurafsky and Martin].
        Then, I use the bigram frequencies given in the code to choose an even
        better possibility. This should be right about 96% of the time [also Jurafsky and Martin], although
        I hope to obtain even better values because of the restricted problem domain."""
        if not self.unigram.has_key(w):
            if training: #make a guess based on prev pos (allowing addition of new word)
                return max([(v.freq,k) for (k,v) in self.prev[prevPOS].items()])[1]
            else: #be strict, and maybe give warning about closest word available
                closewords = []
                for k in self.unigram.keys():
                    temp=editDistance(w,k)
                    if temp < 3:
                        closewords.append((temp,k))
                if closewords:
                    raise KeyError, min(closewords)[1]
                else:# completely misspelled word
                    raise KeyError, None
        else:
            #0.choose 'most common' tag (this has to be a tag present in every grammar)
            selectedPOS = '#'
            #1.determine a simple unigram frequency based tag
            selectedPOS = max([(v.freq,k) for (k,v) in self.unigram[w].getPOS().items()])[1]
            #2.determine bigram frequency of various things to provide '96% quality POS identification'
            maxFreq = 0.0
            #could be:
            #selectedPOS = max([self.prev[prevPOS][key].freq * \
            #                                   (self.unigram[w].freq / self.POSfreq[key].freq) \
            #                                   for (key,val) in self.unigram[w].getPOS().items()])[1]
            #but I think we all agree that's a bit of an overkill.
            #Maybe if we were using prefix math ops and Lisp it would be understandable.
            for (key,val) in self.unigram[w].getPOS().items():
                #P(POS|prevPOS)=
                newFreq = self.prev[prevPOS][key].freq
                #P(POS|"word")=
                newFreq *= self.unigram[w].freq / self.POSfreq[key].freq
                if newFreq > maxFreq and self.prev[prevPOS][key].count > 1:
                    selectedPOS = key
                    maxFreq = newFreq
            return selectedPOS
def editDistance(s,t):
    """str*str->int -- give the edit distance between two words

    Insertion and deletion cost 1 each
    Substitution costs 0 if chars identical, 2 otherwise
    These might someday become more complicated, but I doubt it unless there
    is a problem with the accuracy of this function's results.
    
    NOTE:There is a still lingering difference between the chart in the book of
    >>> editDistance('intention','execution')
    8
    The answer is right, but the actual values are consistently 1 or 2 less than the book's."""
    n = len(s)
    m = len(t)
    dist = [[x for x in range(m+1)]]
    for y in range(n):
        dist.append([y+1]+[0 for x in range(m)])
    for i in range(1,n+1):
        for j in range(1,m+1):
            dist[i][j] = min([dist[i-1][j]+1,
                              dist[i-1][j-1]+((s[i-1]!=t[j-1])*2),
                              dist[i][j-1]+1])
    return dist[n][m]