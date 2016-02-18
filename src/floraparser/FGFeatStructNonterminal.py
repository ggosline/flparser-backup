__author__ = 'gg12kg'

from nltk.grammar import FeatStructNonterminal

class FGFeatStructNonterminal(FeatStructNonterminal):

    def __init__(self, features=None, **morefeatures):
        self.tokens = []
        self.span = (0,0)
        super().__init__(features, **morefeatures)

    def text(self, ptext):
        starttoken, endtoken = self.span[0], self.span[1]-1
        return ptext[self.tokens[starttoken].span.start: self.tokens[endtoken].span.end]

