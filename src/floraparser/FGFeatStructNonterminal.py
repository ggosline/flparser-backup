__author__ = 'gg12kg'

import copy

from nltk.grammar import FeatStructNonterminal


class FGFeatStructNonterminal(FeatStructNonterminal):

    def __init__(self, features=None, **morefeatures):
        super().__init__(features, **morefeatures)
        self.span = None

    def text(self, tokens, ptext):
        starttoken, endtoken = self.span[0], self.span[1]-1
        return ptext[tokens[starttoken].slice.start: tokens[endtoken].slice.stop]

    ##////////////////////////////////////////////////////////////
    # { Copying
    ##////////////////////////////////////////////////////////////

    def __deepcopy__(self, memo):
        memo[id(self)] = selfcopy = self.__class__()
        for (key, val) in self._items():
            selfcopy[copy.deepcopy(key, memo)] = copy.deepcopy(val, memo)
        if hasattr(self, 'span'):
            selfcopy.span = self.span
        else:
            selfcopy.span = None

        return selfcopy