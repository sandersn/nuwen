#!/usr/bin/python
"""web.py -- common web functions that I use in Diem"""
def despatch(fdict, command, input):
    """quick and dirty version of the menuLoop function from util.py

    doesn't check for empty or bad input since input is guaranteed to
    come either from buttons or *very* smart users. Probably the first. ^_^"""
    return fdict[command[0].lower()](input)
def get(formdict, key, alt):
    """This get may be redundant. It's possible."""
    if formdict.has_key(key):
        return formdict[key].value
    else:
        return alt