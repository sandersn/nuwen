"""postag.py -- Provides POS tagging and spelling correction"""
from gram import TagGram, Unigram, Bigram, Gram #for various statistical magic
import cPickle

class POSTagger:
    """ Class provides a learning POS tagger and unigram/bigram/trigram analyser

    All data is pickled to a file and loaded from said file in the following order:
    unigram, prev, prevtotals, POSfreq, POStotal (although not tupled)
    bigram is _not_ saved or restored because
        1)its size is too large
        2)it can be generated from available unigram data
        3)its use is not pertinent to the current application I am developing"""
    #provides data on non-whitespace splitting chars
    #TODO:Declare french (euro?) encoding  for the french quotes to obviate warning
    additionalSplits = ['.', ',', '!', ':','?','"','(','[','{',')',']','}',"j'", "t'", "l'", "m'", "n'", "d'",'«','»'] 
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
        self.POSList = POSList
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
        #load file after initialisation (if provided)
        if fileName != '':
            self.load(fileName)
            self.loaded = 1
    def __str__(self):
        temp = self.unigram.keys()
        temp.sort()
        return "Lexicon size:%d\t\tLexicon:\n%s" % (len(self.unigram), ' | '.join(temp))
    def load(self,fileName):
        """str -- Unpickle required class data from fileName. USE ONLY ONCE PER INSTANCE."""
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
        """str -- Pickle required class data to fileName"""
        f = open(fileName,'wb')
        cPickle.dump(self.unigram,f, True)
        cPickle.dump(self.prev,f, True)
        cPickle.dump(self.prevtotals,f, True)
        cPickle.dump(self.POSfreq,f, True)
        cPickle.dump(self.POStotal,f, True)
        f.close()
        self.loaded=1
    def figureUnigrams(self, words):
        """[(str,str)...]->{str:Unigram} -- words is a list of doubles thus: (word,POS)

        This is nearly the first Python code I ever wrote, except for some later additions.
        This might explain my use of comments instead of docstrings and the way the
        thing is so ugly."""
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
    The answer is right, but the actual values are consistently 1 or 2 less than the book's.
    ("the book" here means Jurafsky and Martin's Speech and Language Processing, 2000)"""
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