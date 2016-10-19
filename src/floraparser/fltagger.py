# -*- coding: utf-8 -*-
__author__ = 'George'

import logging
import re

from nltk.featstruct import FeatStructReader
from nltk.grammar import FeatStructNonterminal, TYPE

from floraparser.FGFeatStructNonterminal import FGFeatStructNonterminal
from floraparser.enginflect import singularize
from floraparser.lexicon import lexicon, multiwords

# read_expr = Expression.fromstring
# Expression._logic_parser.quote_chars = [('"', '"', r'\\', True)]

PREFIX = re.compile(r'\b(?P<prefix>ab|ad|bi|deca|dis|dodeca|hemi|hetero|hexa|homo|infra|inter|'
                    r'macro|mega|meso|micro|'
                    r'mid|mono|multi|ob|octo|over|penta|poly|postero|post|ptero|pseudo|quadri|quinque|semi|sub|sur|syn|'
                    r'tetra|tri|uni|multi|xero)(?P<root>.+)\b')

# SUFFIX = re.compile(r"\b(?P<root>\w*)(?P<suffix>er|est|fid|form|ish|less|like|ly|merous|most|shaped)\b")
SUFFIX = re.compile(r"\b(?P<root>\w+)(?P<suffix>form|ish|merous|most|shaped|like)\b")

PLENDINGS = re.compile(r"(?:[^aeiou]ies|i|ia|(x|ch|sh)es|ves|ices|ae|s)$")

NUMBERS = re.compile(r'^[-–0-9—.·()\s/]+$')

NUMWORD = re.compile(r'(?P<prefix>[0-9](?:-[0-9]))(?P<root>[-–][-a-z]*)')

featurereader = FeatStructReader(fdict_class=FGFeatStructNonterminal)

class FlTagger():

    def rootword(self, word):
        # hyphenated word
        # return list of words with last word first (the root?)
        if '-' in word:
            m = NUMWORD.match(word)
            if m:
                return m.group('root'), m.group('prefix')
            else:
                parts = word.split('-')
                if (parts[-1],) in lexicon or ('-'+parts[-1],) in lexicon:
                    return parts[-1], word[0:word.rindex('-')]

        # prefix or suffix
        m = PREFIX.match(word)
        if m:
            return m.group('root'), m.group('prefix')

        ms = SUFFIX.match(word)
        if ms:
            return ms.group('root'), ms.group('suffix')

        return None

    def singularize(self, word):  # Using textblob Word here
        """
        :param word: str
        """
        if PLENDINGS.search(word):
            return singularize(word)

    def multiwordtokenize(self, flword, word):
        sent = flword.sentence
        words = sent.words
        mwlist = multiwords[word]
        iword = words.index(flword)
        for wlist in mwlist:  # Could optimize
            for windx in range(0, len(wlist)):
                match = None
                if iword + windx < len(words) and wlist[windx] == words[iword + windx].text:
                    match = slice(iword, windx + iword)
                else:
                    match = None
                    break
            if match:
                flword.slice = slice(words[iword].slice.start, words[windx + iword].slice.stop)
                for wn in words[iword + 1: windx + iword + 1]:
                    wn.slice = slice(0, 0)  # mark as null word
                # need to delete the words here but in the middle of a for loop so can't
                return wlist

        return (word,)

    def tag_word(self, word, flword=None):
        """
        :param flword: fltoken.FlWord
        """
        if word == '':
            return None, '', None, None

        word = word.lower()

        if word in multiwords:  # multi word phrase
            ws = self.multiwordtokenize(flword, word)
        else:
            ws = (word,)

        if ws in lexicon:
            return word, lexicon[ws][0][TYPE], lexicon[ws], ws

        # lexicon matches punctuation, including single parentheses; so do before numbers
        if NUMBERS.match(word):
            return flword, 'NUM', [featurereader.fromstring(
                "NUM[H=[+numeric, orth='" + word +"']]")], (word,)
                    # features={TYPE: 'NUM', 'numeric': True, 'orth': word, 'sem': read_expr('num("' + word + '")')})], \
                    #     (word,)
        ws = FlTagger.singularize(self, word)
        if ws:
            ws = (ws,)
            if ws in lexicon:
                lexent = []
                for gc in lexicon[ws]:
                    if gc[TYPE] == 'N':  # plurals must be nouns
                        # gc['plural'] = True
                        lexent.append(gc)
                if lexent:
                    return flword, 'NP', lexent, ws

        # Try taking the word apart at dashes or prefix, suffix
        root = self.rootword(word)
        if root:
            if (root[0],) in lexicon:  # xxx not handling synonym entries here !
                le = lexicon[(root[0],)][0].copy()
                le['H', 'mod'] = root[1]
                #return root, le[TYPE], [le], (root[0],)
                return root, le[TYPE], [le], (word,)
            if ('-' + root[0],) in lexicon:  # suffix
                le = lexicon[('-' + root[0],)][0].copy()
                le['H', 'mod'] = root[1]
                return root, le[TYPE], [le], ('-' + root[0],)

        if word.endswith('ly'):
            logging.info ("UNK adverb:" + word)
            return flword, 'ADV', [
                featurereader.fromstring(
                "ADV[H=[orth='" + word +"']]")], \
                   (word,)
                # FeatStructNonterminal(features={TYPE: 'ADV', 'timing': False, 'orth': word, 'sem': read_expr(word)})], (
                #    word,)

        # Didn't find in fnaglossary; try WordNet
        # synsets = word.synsets
        # for sy in synsets:
        # pass

        logging.info ("UNK word:  " + word)
        return word, 'UNK', [FeatStructNonterminal(features={TYPE: 'UNK', 'orth': word})], (word,)

        # def tag(self, blob):
        # return [self.tag_word(word) for word in blob.words]


if __name__ == "__main__":
    tagger = FlTagger()
    testword = "bilocular"
    print(tagger.tag_word(testword))
    # print(posfromglossary(word))