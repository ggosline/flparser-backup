from nltk.compat import total_ordering
from nltk.featstruct import CustomFeatureValue, UnificationFailure

@total_ordering
class SpanFeature(CustomFeatureValue):
    def __init__(self, low, high):
        assert low <= high
        self.low = low
        self.high = high
        self._hash = hash((low, high))
        self._default = (0, 0)

    def unify(self, other):
        if not isinstance(other, SpanFeature):
            return UnificationFailure
        low = min(self.low, other.low)
        high = max(self.high, other.high)
        if low <= high:
            return SpanFeature(low, high)
        else:
            return UnificationFailure

    def __repr__(self):
        return '(%s<x<%s)' % (self.low, self.high)

    def __eq__(self, other):
        if not isinstance(other, SpanFeature):
            return False
        return (self.low == other.low) and (self.high == other.high)

    def __lt__(self, other):
        if not isinstance(other, SpanFeature):
            return True
        return (self.low, self.high) < (other.low, other.high)

    def __hash__(self):
        self._hash = hash((self.low, self.high))
        return self._hash
