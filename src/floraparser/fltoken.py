# -*- coding: utf-8 -*-

__author__ = 'gg12kg'

import re
from floraparser import botglossary, pos
fltagger = pos.FlTagger()

class FlTaxon():
    '''
    Flora taxon
    '''
    _sent_tokenizer = None

    def __init__(self, trec,
                 sentence_tokenizer=None):
        self.flora = trec['flora_name']
        self.taxonNO = trec['taxonNo']
        self.rank = trec['rank']
        self.family = trec['family']
        self.genus = trec['genus']
        self.species = trec['species']
        self.infrarank = trec['infrarank']
        self.infraepi = trec['infraepi']
        self.description = trec['description']
        if self.rank != None:
            self.description = 'Plant is ' + self.description
        self.sentences = [FlSentence(self, sl[0], sl[1]) for sl in
                          sentence_tokenizer(self.description)] if self.description else []

    def __repr__(self):
        return ' '.join(
            [f for f in (self.flora, self.rank, self.family, self.genus, self.species, self.infrarank, self.infraepi) if
             f])

    def gettext(self, span):
        return self.description[span[0]:span[1]]

class FlSentence():
    def __init__(self, taxon, fromchar, tochar):
        self.taxon = taxon
        self.slice = slice(fromchar, tochar)
        self.fromchar = fromchar
        self.tochar = tochar
        self._words = None
        self._tokens = None
        self._phrases = None

    def __repr__(self):
        return self.taxon.description[self.slice]

    @property
    def text(self):
        return self.taxon.description[self.slice]

    @property
    def words(self):
        if not self._words:
            self._words = [FlWord(self, sl) for sl in FlTokenizer().span_tokenize(self.text)]
            if self._words[-1].text.endswith('.'):  # Punkt leaves the full-stop attached to last word
                ts = self._words[-1].slice
                self._words[-1].slice = slice(ts.start, ts.stop - 1)
        return self._words

    @property
    def tokens(self):
        if not self._tokens:
            self._tokens = [FlToken(self, word) for word in self.words]
            # eliminate null tokens
            self._tokens = [tk for tk in self._tokens if tk.slice.start != tk.slice.stop]
        return self._tokens

    @property
    def phrases(self):
        if not self._phrases:
            self._phrases = FlPhrase.split(self, self.tokens, ';')
        return self._phrases


class FlWord():
    def __init__(self, sentence, slice):
        self.sentence = sentence
        self.slice = slice

    @property
    def text(self):
        return self.sentence.text[self.slice]

    def __repr__(self):
        return self.text


class FlToken():
    def __init__(self, sentence, word):
        self.sentence = sentence
        self.word = word
        self.lexword = ''
        self.lexentry = None
        self.POS = None
        # tagger can leave tokens with slice(0,0) from multiword processing
        self.flRoot, self.POS, self.lexentry, wordtuple = fltagger.tag_word(self.word)
        if wordtuple:
            self.lexword = '_'.join(wordtuple)
        self.slice = word.slice

    def __eq__(self, other):
        return (isinstance(other, str)
                and self.lexword == other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.lexword)

    @property
    def text(self):
        return self.sentence.text[self.slice]

    def __repr__(self):
        return self.text

    def __getitem__(self, slice):
        return self.text[slice]


class FlPhrase():
    def __init__(self, sentence, tokens):
        self.sentence = sentence
        self.slice = slice(tokens[0].slice.start, tokens[-1].slice.stop)
        self.tokens = tokens

    @property
    def text(self):
        return self.sentence.text[self.slice]

    @staticmethod
    def split(sentence, tokens, separator):
        '''
        Split a phrase based on a character string
        Returns slices for the substring with the separator omitted
        '''
        locations = [i for i, val in enumerate(tokens) if val.text == separator]
        locations.insert(0, -1)
        locations.append(None)
        return [FlPhrase(sentence, tokens[locations[i] + 1:locations[i + 1]]) for i in range(0, len(locations) - 1)]

class FlTokenizer():
    '''
    Taken from Punkttokenizer
    '''

    _re_number_range = r'''(?=[\(0-9])
                            (?:\(\d+(?:[.·]\d+)?–?\))?
                            \s?
                            \d+(?:[.·]\d)?
                            (?:[--–]\d+(?:[.·]\d+)?)?
                            \s?
                            (?:\(–?\d+(?:[.·]\d+)?\))?
                            (?<=[\)0-9])
                        '''

    _re_word_start = r"[^\(\"\`{\[:;&\#\*@\)}\],]"
    """Excludes some characters from starting word tokens"""

    _re_non_word_chars = r"(?:[?!)\";}\]\*:@\'\({\[])"
    """Characters that cannot appear within words"""

    _re_multi_char_punct = r"(?:\-{2,}|\.{2,}|(?:\.\s){2,}\.)"
    """Hyphen and ellipsis are multi-character punctuation"""

    _word_tokenize_fmt = r'''(
        %(MultiChar)s
        |
        %(NumberRange)s
        |
        (?=%(WordStart)s)\S+?  # Accept word characters until end is found
        (?= # Sequences marking a word's end
            \s|                                 # White-space
            $|                                  # End-of-string
            %(NonWord)s|%(MultiChar)s|          # Punctuation
            ,(?=$|\s|%(NonWord)s|%(MultiChar)s) # Comma if at end of word
        )
        |
        \S
    )'''
    """Format of a regular expression to split punctuation from words,
    excluding period."""

    def _word_tokenizer_re(self):
        """Compiles and returns a regular expression for word tokenization"""
        try:
            return self._re_word_tokenizer
        except AttributeError:
            self._re_word_tokenizer = re.compile(
                self._word_tokenize_fmt %
                {
                    'NonWord': self._re_non_word_chars,
                    'MultiChar': self._re_multi_char_punct,
                    'WordStart': self._re_word_start,
                    'NumberRange': self._re_number_range,
                },
                re.UNICODE | re.VERBOSE
            )
            return self._re_word_tokenizer

    def word_tokenize(self, s):
        """Tokenize a string to split off punctuation other than periods"""
        return self._word_tokenizer_re().findall(s)

    def tokenize(self, text):
        return self.word_tokenize(text)

    def span_tokenize(self, text):
        """
        Given a text, returns a list of the slices (start, end) spans of words
        in the text.
        """
        return [sl for sl in self._slices_from_text(text)]

    def _slices_from_text(self, text):
        last_break = 0
        contains_no_words = True
        for match in self._word_tokenizer_re().finditer(text):
            contains_no_words = False
            context = match.group()
            yield slice(match.start(), match.end())
        if contains_no_words:
            yield slice(0, 0)  # matches PunktSentenceTokenizer's functionality

if __name__ == '__main__':
    tryme = FlTokenizer().word_tokenize('c. (0.5)1·5-2·3(4) × 1·5-2·7 cm.')

    # tryme = FlToken('glabrous',1,4)
    pass

