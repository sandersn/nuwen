from math import log
"""module gram:Classes for bigram POS analysis

Classes on which my bigram part of speech analyser is based:
Gram, the base class for any sequence of words--the only thing we care about now is frequency
TagGram, the class that connects a gram with a POS
Unigram, holder of a single word plus its TagGram
Bigram, holder of two Unigrams
--Trigram may eventually be implemented--
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
        if POS in TagGram.POSList:
            self.POS = POS
        else:
            #raise ValueError('C5 tagset POS required. See Garside, et al., 1997 for complete list')
            #raise ValueError(POS + ':"Restricted" tagset POS required.\nSee Chanod and Tapanainen, 1995 for complete list')
            raise ValueError(POS + ':not in valid list of of POSen. See gram.TagGram.POSList for valid options.')
    def __str__(self):
        return Gram.__str__(self) + ' POS: ' + self.POS
class Unigram(Gram):
    """Holds a unigram (id est, only cares about one word at a time)

    Tracks a word, holds a list of seen parts of speech for this word, and
    holds a list of words that come *after* this word.
    
    NOTE:Since a unigram contains other Gram objects, changing its count should alter the count
    of the contained objects. However, the current implementation does not do this. Be aware of this.
    NOTE:This is some really ancient code I wrote while still mostly using Java. There are some weird
    idioms, as a result, like a private list with Java-style accessor methods. I also mention converting
    things to an enum. I have since realised there are better ways to
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
