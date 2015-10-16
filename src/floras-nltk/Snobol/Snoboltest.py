#
# Test the Snobol module
#

import string
import sys

from Snobol import *


sys.stderr = sys.stdout

letters = string.ascii_lowercase[0:26]


class StuffedUp(Exception):
    pass


def tm(subj, pat, should_match):
    print("Subject:", repr(subj))
    print("Pattern:", pat)
    result = match(subj, pat)
    print("Result: ", result)
    print()
    check(result, should_match)


def tmp(subj, pat, pos, should_match):
    print("Subject:", repr(subj))
    print("Pattern:", pat)
    result = match(subj, pat, pos)
    print("Result: ", result)
    print()
    check(result, should_match)


def tam(subj, pat, should_match):
    m = Matcher()
    print("Subject:    ", repr(subj))
    print("Pattern:    ", pat)
    result = m.match(subj, pat)
    print("Result:     ", result)
    print("Assignments:", m)
    print()
    check(result, should_match)


def check(result, should_match):
    if (result is not None) != should_match:
        print("*** WRONG! ***")
        raise StuffedUp


try:
    if 1:
        tm("Ftang", SUCCEED, 1)
        tm("Ftang", FAIL, 0)

        p = LIT("shrubbery")
        tm("I want a shrubbery, please", p, 1)
        tm("I want a shrubbery, please", "shrubbery", 1)
        tmp("I want a shrubbery, please", p, 0, 0)
        tmp("I want a shrubbery, please", p, 8, 0)
        tmp("I want a shrubbery, please", p, 9, 1)
        tmp("I want a shrubbery, please", p, 10, 0)

        p = LIT("sh") + LIT("rubber")
        tm("A shrubber I am", p, 1)
        tm("Ash rubber I am not", p, 0)

        p = (LIT("grail") | LIT("parrot")) + " "
        tm("This grail is resting", p, 1)
        tm("The holy parrot is very elusive", p, 1)
        tm("Millennium of the stoat", p, 0)

        p = "ecky" + ARB + "splat"
        tm("Eckyeckyeckyecky", p, 0)
        tm("Ecky ecky ecky ecky", p, 0)
        tm("Ecky ecky boing ecky splat ecky ping", p, 1)
        tm("Ecky ecky boing ping", p, 0)

        p = "assoc" + REM
        tm("Word association football", p, 1)
        tm("Spanish inquisition", p, 0)

        p = ANY("AEIOU") + "L"
        tm("HOLY", p, 1)
        tm("GRAIL", p, 1)
        tm("PARROT", p, 0)

        p = " " + ARBNO(ANY("0123456789")) + " "
        tm("I want  shrubberies", p, 1)
        tm("I want 2 shrubberies", p, 1)
        tm("I want 42 shrubberies", p, 1)
        tm("I want forty-two shrubberies", p, 0)

        p = BREAK("!?")
        tm("Ni! to you, sir.", p, 1)
        tm("Ni! to you, sir.", p + "!", 1)
        tm("Ni! to you, sir.", p + "?", 0)
        tm("Shrub? Berry?", p, 1)
        tm("I want another shrubbery.", p, 0)

        p = "silly" + LEN(5) + "o"
        tm("How silly is your walk?", p, 1)
        tm("Not very silly, I'm sorry to say.", p, 0)

        p = "ta" + NOTANY("aeiou") + "g"
        tm("Ftang", p, 1)
        tm("Ftaang", p, 0)
        tm("Ftag", p, 0)

        p = "sil" + POS(12) + "ly"
        tm("Slightly silly party", p, 1)
        tm("Minister of silly walks", p, 0)

        p = "sil" + RPOS(8) + "ly"
        tm("Slightly silly party again", p, 0)
        tm("Minister of silly walks", p, 1)

        p = "i" + RTAB(17) + "silly"
        tm("Slightly silly party again", p, 1)
        tm("Minister of silly walks", p, 0)

        p = "@" + SPAN(letters) + "*"
        tm("Ecky@*ecky", p, 0)
        tm("Ecky@e*ecky", p, 1)
        tm("Ecky@ecky*ecky", p, 1)

        p = "i" + TAB(9) + "silly"
        tm("Slightly silly party", p, 1)
        tm("Minister of silly walks", p, 0)

        p = "-" + BAL() + "-"
        tm("a--walk", p, 0)
        tm("a-s-walk", p, 1)
        tm("a-()-walk", p, 1)
        tm("a-(-walk", p, 0)
        tm("a-(silly)-walk", p, 1)
        tm("a-(very(silly))-walk", p, 1)
        tm("a-(very)silly)-walk", p, 0)

        p = "-" + BAL("[]") + "-"
        tm("a-[silly]-walk", p, 1)
        tm("a-(silly]-walk", p, 0)

        p = REM.stuff
        tam("Stoat", p, 1)
        p = "(" + SPAN(letters).stuff + ")"
        tam("Very silly (spam) party", p, 1)
        tam("Very silly (spam and eggs) party", p, 0)

        word = SPAN(letters)
        expr = BAL()
        p = word.w1 + "=" + expr.w2 + "+" + expr.w3
        tam("order=spam+(bacon+eggs)", p, 1)

        p = SPAN(letters).x + "/" + VAL("x")
        tm("ftang/ftang", p, 1)
        tm("biscuit/barrel", p, 0)

        p = "<" + BREAK("|").foo + "|" + LEN(VAL("int(foo)")) + ">"
        tm("<11|inquisition>", p, 1)
        tm("<42|inquisition>", p, 0)

        p = "!" + AT.n + ARB + RPOS(VAL("n")) + "!"
        tm("Ni! A rubber shrubbery!??", p, 1)
        tm("Ni! A rubber shrubbery!???", p, 0)

    if 1:
        word = SPAN(letters)
        p = YIELD(word.w, '''"The word is '%s'" % w''')
        tm("{spam}", p, 1)
        p = word.w ^ '''"The word is now '%s'" % w'''
        tm("[eggs]", p, 1)

    if 1:
        expr = word.w ^ "w" \
               | "(" + PAT("expr").e1 + "+" + PAT("expr").e2 + ")" ^ "[e1,e2]"
        tmp("spam", expr, 0, 1)
        tmp("(spam+eggs)", expr, 0, 1)
        tmp("(spam+(bacon+eggs))", expr, 0, 1)

    if 1:
        order = POS(0) + (word.w + "=" + expr.e ^ "{w:e}") + RPOS(0)
        tm("main=(spam+(bacon+eggs))", order, 1)

except StuffedUp:
    pass
