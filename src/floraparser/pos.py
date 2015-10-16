# -*- coding: utf-8 -*-
__author__ = 'George'

import re
import copy

from floraparser.inflect import singularize

from floraparser.lexicon import lexicon, multiwords
from nltk.grammar import FeatStructNonterminal, TYPE, SLASH
from nltk.sem import Expression

read_expr = Expression.fromstring
Expression._logic_parser.quote_chars = [('"', '"', r'\\', True)]

PREFIX = re.compile(r'\b(?P<prefix>ab|ad|bi|deca|dis|dodeca|hemi|hetero|hexa|homo|infra|inter|'
                    r'macro|mega|meso|micro|'
                    r'mid|mono|multi|ob|octo|over|penta|poly|postero|post|ptero|pseudo|quadri|quinque|semi|sub|sur|syn|'
                    r'tetra|tri|uni|multi|xero)(?P<root>.+)\b')

# SUFFIX = re.compile(r"\b(?P<root>\w*)(?P<suffix>er|est|fid|form|ish|less|like|ly|merous|most|shaped)\b")
SUFFIX = re.compile(r"\b(?P<root>\w+)(?P<suffix>form|ish|merous|most|shaped|like)\b")

PLENDINGS = re.compile(r"(?:[^aeiou]ies|i|ia|(x|ch|sh)es|ves|ices|ae|s)$")

NUMBERS = re.compile(r'^[–0-9—.·()\s/]+$')


class FlTagger():
    def rootword(self, word):
        # hyphenated word
        # return list of words with last word first (the root?)
        if '-' in word:
            wrds = word.split('-')
            if NUMBERS.match(wrds[0]):
                rootw = '_' + wrds[1]
                return rootw, [wrds[1]]
            return wrds[-1], wrds[0:-1]

        # prefix or suffix
        m = PREFIX.match(word)
        if m:
            return m.group('root'), m.group('prefix')

        ms = SUFFIX.match(word)
        if ms:
            return ms.group('root'), ms.group('suffix')

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
                # need to delete the words here but in the middle of a for loop
                return wlist

        return (word,)

    def tag_word(self, flword):
        """
        :param flword: fltoken.FlWord
        """
        if flword.text == '':
            return None, '', None, None

        word = flword.text.lower()

        if word in multiwords:  # multi word phrase
            ws = self.multiwordtokenize(flword, word)
        else:
            ws = (word,)

        if ws in lexicon:
            return flword, lexicon[ws][0][TYPE], lexicon[ws], ws

        # lexicon matches punctuation, including single parentheses; so do before numbers
        if NUMBERS.match(word):
            return flword, 'NUM', [
                FeatStructNonterminal(
                    features={TYPE: 'NUM', 'numeric': True, 'orth': word, 'sem': read_expr('num("' + word + '")')})], (
                       word,)

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

        # Try taking the word apart at dashes
        root = self.rootword(word)
        if root:
            if (root[0],) in lexicon:  # xxx not handling synonym entries here !
                le = lexicon[(root[0],)][0]
                return root, le[TYPE], [le], (root[0],)
            if ('-' + root[0],) in lexicon:  # suffix
                le = lexicon[('-' + root[0],)][0]
                return root, le[TYPE], [le], ('-' + root[0],)

        if word.endswith('ly'):
            return flword, 'ADV', [
                FeatStructNonterminal(features={TYPE: 'ADV', 'timing': False, 'orth': word, 'sem': read_expr(word)})], (
                   word,)

        # Didn't find in fnaglossary; try WordNet
        # synsets = word.synsets
        # for sy in synsets:
        # pass

        return flword, 'UNK', [FeatStructNonterminal(features={TYPE: 'UNK', 'orth': word})], (word,)

        # def tag(self, blob):
        # return [self.tag_word(word) for word in blob.words]


if __name__ == "__main__":
    tagger = FlTagger()
    testword = "3-locular"
    print(tagger.tag_word(testword))
    # print(posfromglossary(word))