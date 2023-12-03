"""unification.py -- a simple unification implementation.

TODO:Figure out how to create feature structures at runtime.
This is a great mystery
1.Only simple features can be associated with leaves (id est POSen)
2.<NP head agreement> = <VP head agreement> means you should gen a Feature
at the end and point both to it. Maybe this is best. But you have to implement follow
for more general rules, like
<S head> = <VP head> so they will pick up existing structure and point to it.
3.hhmm this might be possible. ^_^"""
def unify(f1,f2):
    """Feature*Feature->Feature -- Implement unification

    Example:
    >>> realx=Feature('number','sg')
    >>> realy=Feature('person','3')
    >>> x=Feature(content={'number':realx})
    >>> y=Feature(content={'person':realy})
    >>> unification.unify(x,y)
     number sgperson 3
    """
    f1real = _deref(f1)
    f2real = _deref(f2)
    if f1real is None:
        f1.p = f2
        return f2
    elif f2real is None:
        f2.p = f1
        return f1
    elif isinstance(f1real, dict) and isinstance(f2real, dict):#other possibility is of course isinstance(f1real,str)
        f2.p = f1
        for f in f2real:
            other = None
            if f in f1real:
                other = f1real[f]
            else:
                other = Feature(f2real[f].name)
                f1real[f] = other
            if not unify(f2real[f], other): return None
        return f1
    #ergo, f1real and f2real must be at least one of them be a simple (string)
    elif f1real is f2real:
        f1.pointer = f2
        return f2
    else:
        return None
def _deref(f):
    while f.p: f = f.p
    return f.content
def follow(prefix,f): #maybe call this depref..?
    """Feature*Feature->Feature -- return the part of f which prefix specifies

    Should prefix be a series of Feature with nothing but singleton complex content fields?"""
    pass
class Feature:
    def __init__(self, name='', content=None, pointer=None):
        self.content = content
        self.p = pointer
        self.name = name
    def __str__(self):
        msg = ''
        real = _deref(self)
        if real:
            if isinstance(real,dict):
                msg += '['+', '.join(map(str,real.values()))+']'
            else:#should be instance of str
                msg += real
        return self.name + ' '+msg
    __repr__=__str__
    def add(self,feature):
        real = _deref(self)
        if isinstance(real, str):
            raise ValueError, "Can't add features to a simple feature"
        else:
            real[feature.name] = feature
            #code here to figure out things like where should things be merged or something
        return self # :-D (so you can chain these things)
##    def __eq__(self,other):
##        """NOTE:This equality is ONLY used in unify and does not return valid results otherwise
##
##        The primary reason is that the rest of the equality test takes places in recursion of unify,
##        so if __eq__ does too much work, it breaks unify."""
##        return self.name==other.name #and self.content==other.content
#
# these are junk lines
# created so that
# my screen is all grey
# background.
# do not despise them,
# but rather do them
# honour for their
# simple uselessness
# and calm simplicity.
# ph33r and enjoy...
#
# laughter ceases now
# and there are women weeping
# shuriken attack
def main(argv):
    num=Feature('number','sg')
    agr=Feature('agreement',{'number':num})
    agr2=Feature('agreement',pointer=agr)
    sub=Feature('subject',{'agreement':agr2})
    x=Feature(content={'agreement':agr,'subject':sub})
    y=Feature(content={'subject':Feature('subject',{'agreement':Feature('agreement',{'person':Feature('person','3')})})})
    z=unify(x,y)
    #for S -> NP VP
    # <NP Head Agreement> = <VP Head Agreement>
    # <S Head> = <VP Head>
    #becomes
    p2 = Feature()
    agr=Feature('agreement', {'':p2})
    np = Feature('np', {'head':Feature('head', {'agreement':Feature('agreement',{'':p2})})})
    vp = Feature('vp', {'head':Feature('head', {'agreement':agr})})
    s=Feature('s',{'head':Feature('head', {'agreement':agr})})
    constraint = Feature(content={'s':s,'np':np,'vp':vp})
    print constraint
##    print z
##    print x
##    print y
if __name__=='__main__':
    import sys
    main(sys.argv)