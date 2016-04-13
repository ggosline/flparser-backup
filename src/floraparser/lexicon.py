# -*- coding: utf-8 -*-

__author__ = 'gg12kg'

import csv
import pickle
import os
from nltk.featstruct import Feature,  FeatStructReader
from floraparser.FGFeatStructNonterminal import FGFeatStructNonterminal

# read_expr = Expression.fromstring

lexicon = {}

multiwords = {}

# Our features with default values (usually False)
position =  Feature('position', default=False)
timing   =  Feature('timing', default=False)
posit    =  Feature('posit', default='')
makecomp =  Feature('makecomp', default=False)
compar   =  Feature('compar', default=False)
adjectival   = Feature('adjectival', default=False)
counted      = Feature('counted', default=False)
conditional  = Feature('conditional', default=False)
group        = Feature('group', default=False)    # nouns

defaultfeatures = (position, timing, posit, makecomp, compar, adjectival, counted, conditional, group)

def pickle_lexicon():

    global lexicon, multiwords
    # class LexEntry():
    # def __init__(self, POS, wordlist, category=None, appliesto=None):
    # self.POS = POS
    # self.wordlist = wordlist
    #         self.category = category
    #         self.appliesto = appliesto
    featurereader = FeatStructReader(fdict_class=FGFeatStructNonterminal)

    def addlexicon(words, POS, morefeatures):
        for word in words:
            addlexentry(word, POS, morefeatures)

    def addlexentry(word, POS, morefeatures):

        if word.startswith('_'):
            word = word.replace('_', '-', 1)
            morefeatures[counted] = True
        ws = word.split('_')
        if len(ws) > 1:
            firstword = ws[0]
            if firstword in multiwords:
                multiwords[firstword] += [tuple(ws)]
            else:
                multiwords[firstword] = [tuple(ws)]
        if 'category' not in morefeatures:
            category = ""
        else:
            category = morefeatures['category']
        # if 'sem' not in morefeatures:
        #     morefeatures['sem'] = read_expr(word.replace('.', ''))
        # lexicon[tuple(ws)] = LexEntry(POS, tuple(ws), category, appliesto)

        featstring = POS + "[H=[ category= '" + category + "', orth='" + word + "']] "
        newfeature = featurereader.fromstring(featstring)
        newfeature.update(morefeatures)

        # head = FeatStructNonterminal({'orth': word})
        # if 'category' in morefeatures:
        #     head['category'] = morefeatures['category']
        # features = {TYPE: POS, 'H': head}
        # for item in morefeatures.items():  # avoid null values
        #     # if item[1]:
        #     features[item[0]] = item[1]
        lexicon.setdefault(tuple(ws), []).append(newfeature)

    def readcpglossary(gfile=r'..\resources\glossarycp.csv'):
        with open(gfile) as csvfile:
            mydictreader = csv.DictReader(csvfile)
            for gentry in mydictreader:
                if gentry['ID'] == '#':
                    continue
                morefeatures = {}
                gid, term, category, appliesto = gentry['ID'], gentry['term'], gentry['category'].lower(), gentry[
                    'appliesTo'].lower()
                # semterm = term.replace('-', '_').strip('.')
                POS = gentry['POS']
                if POS == 'N':
                    # semexpr = read_expr(semterm)
                    if category == 'structure-infl':
                        morefeatures = {group: True}
                elif POS == 'A':
                    if category == 'structure-infl':
                        morefeatures = {'group': True}
                    # semexpr = read_expr(category.replace('-', '_') + '(' + semterm + ')')
                    # morefeatures = {position: False, timing: False, compar: False}
                else:
                    POS = 'UNK'
                morefeatures['category']=category    # semexpr = None
                addlexentry(term, POS,  morefeatures)
                if '-' in term:     # assume people may have left the dash out of terms (see colours)
                    addlexentry(term.replace('-','_'), POS, morefeatures)

    COORDCONJUNCTION = 'and|and_also|or|and/or|neither|nor|otherwise|but|except|except_for|×|x'.split('|')
    for word in COORDCONJUNCTION:
        addlexentry(word, 'CONJ', dict(conj=word, coord=True))
    SUBCONJUNCTION = 'but|for|yet|so|although|because|since|unless|if'.split('|')
    for word in SUBCONJUNCTION:
        addlexentry(word, 'CONJ', dict(conj=word, coord=False))
    ARTICLE = 'the|a|an'.split('|')
    addlexicon(ARTICLE, 'ART', {})
    DETERMINER = 'each|every|some|all|other|both|their|its'.split('|')
    addlexicon(DETERMINER, 'DET', {})
    PUNCTUATION = [';', '(', ')']
    for char in PUNCTUATION:
        addlexentry(char, 'PUNC', dict(punc=char))
    addlexicon([','], 'COMMA', {})
    PRONOUN = 'it|one|ones|form|forms|part|parts'.split('|')
    addlexicon(PRONOUN, 'PRO', {})

    # should 'on' be here?
    PREPOSITION = 'as|during|for|from|off|onto|out|over|per|through|throughout|' \
                    'towards|up|upward|when|owing_to|due_to|according_to|on_account_of|' \
                    'united_with|joined_to|' \
                    'tipped_by|to_form|attached_to|immersed_in'.split('|')
    for word in PREPOSITION:
        addlexentry(word, 'P', dict(prep=word)) #, sem=read_expr(r'\x.' + word + '(x)'))

    CONDITIONP = 'when|if'.split('|')
    for word in CONDITIONP:
        addlexentry(word, 'P', dict(prep=word, conditional=True)) #, sem=read_expr(r'\x.' + word + '(x)'))

    addlexentry('with', 'WITH', {'presence':True})
    addlexentry(':', 'WITH', {'presence':True})
    addlexentry('without', 'WITH', {'presence':False})

    GROUPS = "group|groups|clusters|cluster|arrays|array|series|" \
             "pairs|pair|row|rows|number|numbers|colonies|whorl|whorls".split('|')
    addlexicon(GROUPS, 'N', dict(group=True, category='grouping'))
    LITNUMBERS = "zero|one|two|three|four|" \
                 "five|six|seven|eight|" \
                 "nine|ten|" \
                 "few|many|numerous|several".split('|')
    addlexicon(LITNUMBERS, 'NUM', dict(literal=True))
    FRACTIONS = "twice|third|fourth|fifth|sixth|seventh|eighth|tenth|" \
                "half|thirds|fourths|quarter|" \
                 "fifths|sixths|sevenths|eighths|ninths|tenths" \
                 "|1/2|1/3|2/3|1/4|1/5|2/5|3/5|4/5".split('|')
    addlexicon(FRACTIONS, 'FRACTION', {})
    ORDNUMBERS = "principal|primary|secondary|tertiary|1st|2nd|3rd|first|second|third|fourth|fifth|sixth|seventh|eigth|ninth|tenth".split(
        '|')
    addlexicon(ORDNUMBERS, 'A', dict(ordinal=True))
    UNITS = "mm.|cm.|dm.|m.|km.|in.|ft.|mm|cm|dm|m|km".split('|')
    addlexicon(UNITS, 'UNIT', {})
    DIMENSION = "high|tall|long|wide|across|thick|diam.|diameter|diam|in_height|in_width|in_diameter|in_diam".split(
        '|')
    addlexicon(DIMENSION, 'DIM', {})
    RANGE = 'up_to|at_least|to|more_than|less_than|attaining'.split('|')
    addlexicon(RANGE, 'RANGE', {})

    POSITIONPRE = 'upper|lower|under|uppermost|lowermost|superior|inferior|outer|inner|outermost|innermost|various'.split('|')
    addlexicon(POSITIONPRE, 'A', {position:True, 'category':'position', 'fix':'pre'})
    POSITIONPOST = 'above_and_beneath|at_the_apex|at_the_base|at_the_top|elsewhere|' \
                    'outside|inside|above|below|beneath|within|throughout|upward'.split('|')
    addlexicon(POSITIONPOST, 'A', {position: True, 'category': 'position', 'fix':'post'})

    POSITIONN = 'top|bottom|underside|base|apex|margin|edge|front|back|both_sides|under_surfaces|' \
               'outside|inside|' \
               'upper_surfaces|both_surfaces|each_side|section|rest_of|junction'.split('|')
    addlexicon(POSITIONN, 'N', {'category':'position'})

    # 'in' poosibly should be in following lists, but masks IN below
    PREP_POSITION = 'at|among|amongst|around|at|between|beyond|by|' \
                    'from|into|near|on|onto|out_of|over|through|throughout|toward|' \
                    'outside|inside|between|before|after|behind|across|along|from|' \
                    'towards|up'.split('|')
    for word in PREP_POSITION:
        addlexentry(word, 'P', {'prep':word, position:True, adjectival:False}) #, sem=read_expr(r'\x.' + word + '(x)'))

    # POSITIONADJ = 'outside|inside|above|below|beneath|within|throughout|upward'.split('|')
    # for word in POSITIONADJ:
    #     addlexentry(word, 'P', {'prep':word, position:True, adjectival:True})
        #addlexentry(word, 'P', prep=word, position=True, sem=read_expr(r'\x.' + word + '(x)'))


    ACCURACY = "c.|about|more_or_less|±|exactly|almost|nearly|appearing".split('|')
    addlexicon(ACCURACY, 'DEG', dict(category='accuracy'))
    FREQUENCY = "very|a_little|not_much|sometimes|often|usually|rarely|more_rarely|more_often|generally|never|always|" \
                "mostly|frequently|soon|also|even|especially|?".split('|')
    addlexicon(FREQUENCY, 'DEG', dict(category='frequency'))
    DEGREE = "sparsely|densely|slightly|narrowly|widely|markedly|extremely|somewhat|rather|shallowly|scarcely|partly|partially|much|well".split('|')
    addlexicon(DEGREE, 'ADV', {})
    COLOURDEG = "dark|light|deep|bright|pale".split('|')
    addlexicon(COLOURDEG, 'ADV', dict(category='coloration'))
    COMPARISON = "older|younger|" \
                 "exceeding|equalling|indistinguishable_from|similar".split('|')
    addlexicon(COMPARISON, 'A', {compar:True, 'category':'compar'})
    COLOURCOMP = "paler|darker|lighter|duller|shinier".split('|')
    addlexicon(COLOURCOMP, 'A', {compar:True, 'category':'coloration'})
    SIZECOMP = "shorter|longer|wider|narrower|bigger|smaller|higher|larger".split('|')
    addlexicon(SIZECOMP, 'A', {compar:True, 'category':'size'})
    COMPADJ = "more|less|most|least".split('|')
    addlexicon(COMPADJ, 'ADV', {makecomp:True})
    TIMING = "at_first|when_young|becoming|tending_to_become|" \
             "remaining|turning|in_age|at_maturity|later|at_length|eventually|when_fresh|when_dry|drying".split('|')
    addlexicon(TIMING, 'A', {timing:True})
    PRESENCE = "present|absent".split('|')
    addlexicon(PRESENCE, 'A', dict(category='presence'))
    ISA = "is|is_a|consisting_of".split('|')
    addlexicon(ISA, 'IS', dict(category='ISA'))
    GERUND = "covering|closing|enveloping|surrounding|forming|terminating_in|dehiscing_by|dividing|" \
             "ending|varying_in|arranged_in|prolonged_beyond|alternating_with|" \
             "united_to_form|unitied_into|enclosing".split('|')
    addlexicon(GERUND, 'P', dict(verb=True))

    addlexicon(['to'], 'TO', {})
    addlexicon(['not'], 'DEG', dict(frequency=True, timing=False))
    addlexicon(['no'], 'NO', {})
    addlexicon(['in'], 'IN', {})
    addlexicon(['than'], 'THAN', {})
    addlexicon(['for'], 'FOR', {})
    addlexicon(['that'], 'RCOMP', {})
    addlexicon(['that'], 'COMP', {})
    addlexicon(['times'], 'TIMES', {})
    addlexicon(['NUM'], 'NUM', {})
    addlexicon(['of'], 'OF', {})
    addlexicon(['in_outline'], 'NULL', {})
    addlexicon(['either'], 'NULL', {})
    addlexicon(['situated'], 'NULL', {})
    addlexicon(['located'], 'NULL', {})
    addlexicon(['borne'], 'NULL', {})

    readcpglossary()
    # for wlist in multiwords.values():
    # wlist = sorted(wlist, key=len)
    with open('lexicon.pickle', 'wb') as f:
        pickle.dump(lexicon, f)
    with open('multiwords.pickle', 'wb') as f:
        pickle.dump(multiwords, f)


if __name__ == '__main__':
    lexicon = {}
    multiwords = {}
    pickle_lexicon()
else:
    savedir = os.curdir
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    with open('lexicon.pickle', 'rb') as f:
        lexicon = pickle.load(f)
    with open('multiwords.pickle', 'rb') as f:
        multiwords = pickle.load(f)
    os.chdir(savedir)