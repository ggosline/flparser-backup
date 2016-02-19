__author__ = 'gg12kg'

from nltk.parse.featurechart import FeatureSingleEdgeFundamentalRule, FeatureTreeEdge, FeatureChart, \
    BU_LC_FEATURE_STRATEGY, FeatureBottomUpPredictCombineRule, FeatureEmptyPredictRule, FeatureChartParser

from nltk.grammar import FeatureGrammar, FeatStructNonterminal, FeatStructReader,\
    read_grammar, SLASH, TYPE, Production, \
    Nonterminal
from nltk.sem import Variable
from nltk.parse.chart import TreeEdge, FundamentalRule, SingleEdgeFundamentalRule, LeafInitRule, EdgeI
from nltk.grammar import FeatureValueType, is_nonterminal
from nltk.featstruct import FeatStruct, Feature, FeatList, FeatDict, unify, FeatureValueTuple
from floraparser.fltoken import FlToken
from floraparser.lexicon import lexicon
from floraparser.lexicon import defaultfeatures
from floraparser.FGFeatStructNonterminal import FGFeatStructNonterminal
from nltk import Tree
from nltk.parse.chart import LeafEdge
from nltk.parse.earleychart import FeatureIncrementalChart, FeatureEarleyChartParser
import copy
import itertools

class FGFeatureTreeEdge(FeatureTreeEdge):

    def __init__(self, span, lhs, rhs, dot=0, bindings=None):

        """
        Most code just a copy of FeatureTreeEdge.__init__
        Construct a new edge.
        If complete copy head features in addition to the bindings
        """
        if bindings is None: bindings = {}

        # If the edge is complete, then substitute in the bindings,
        # and then throw them away.  (If we didn't throw them away, we
        # might think that 2 complete edges are different just because
        # they have different bindings, even though all bindings have
        # already been applied.)
        if dot == len(rhs) and bindings:
            lhs = self._bind(lhs, bindings)
            rhs = [self._bind(elt, bindings) for elt in rhs]
            bindings = {}

        # Added code
        if dot == len(rhs):
            unify_heads(self, span, lhs, rhs)
        # end of added code

        # Initialize the edge.
        TreeEdge.__init__(self, span, lhs, rhs, dot)
        self._bindings = bindings
        self._comparison_key = (self._comparison_key, tuple(sorted(bindings.items())))

def unify_heads(self, span, lhs, rhs):
    """
    If the edge is a ``FeatureTreeEdge``, and it is complete,
    then unify the head feature on the LHS with the head feature
    in the head daughter on the RHS.
    Head daughter marked with feature +HD.
    Head feature is H.

    Save the span in the feature structure
    """

    #lhs['span'] = ((self.tokens[span[0]].slice.start), self.tokens[span[1] - 1].slice.stop)
    #lhs['span'] = span

    head_prod = [prod for prod in rhs if isinstance(prod, FeatStruct) and prod.has_key("HD")]  # should be just one

    if not head_prod:
        return
    rhead = head_prod[0]['H']
    lhead = lhs.get('H', FGFeatStructNonterminal([]))
    try:
        # newH = lhead.unify(rhead, trace=0)
        newH = _naive_unify(lhead, rhead)
        if not newH:
            newH = rhead
            print('FAIL to unify heads', lhs, rhs)
        #   lhs['span'] = span

    except:
        newH = FGFeatStructNonterminal('H[]')

    newH.remove_variables()     # get rid of unresolved variables
    newH.span = span
    lhs['H'] = newH

def _naive_unify(fstruct1:FeatStruct, fstruct2:FeatStruct):

    newfs = copy.deepcopy(fstruct1)
    if _is_mapping(fstruct1) and _is_mapping(fstruct2):

    # Unify any values that are defined in both fstruct1 and
    # fstruct2.  Copy any values that are defined in fstruct2 but
    # not in fstruct1 to fstruct1.  Note: sorting fstruct2's
    # features isn't actually necessary; but we do it to give
    # deterministic behavior, e.g. for tracing.
        for fname, fval2 in sorted(fstruct2.items()):
            if fname in fstruct1:
                newfs[fname] = _naive_unify(fstruct1[fname], fval2)
            else:
                newfs[fname] = fval2

        return newfs # Contains the unified value.

    # Unifying two sequences:
    elif _is_sequence(fstruct1) and _is_sequence(fstruct2):
        # Concatenate the values !!
        # Don't unify corresponding values in fstruct1 and fstruct2.
        newfs += fstruct2
        return newfs # Contains the unified value.

    else:
        return None

def _is_mapping(v):
    return hasattr(v, '__contains__') and hasattr(v, 'keys')

def _is_sequence(v):
    return (hasattr(v, '__iter__') and hasattr(v, '__len__') and
            not isinstance(v, str))
#
# Monkey patch the  init with unify_heads
#  This avoids duplicating all the FeatureChart code with FeatureTreeEdge replace by FGFeaturTreeEdge
#  See commented out code below
#
FeatureTreeEdge.__init__ = FGFeatureTreeEdge.__init__

#EdgeI.nextsym_isvar = FGFeatureTreeEdge.nextsym_isvar
#FeatureTreeEdge.nextsym_isvar = FGFeatureTreeEdge.nextsym_isvar

class FGChart(FeatureChart):

    def pretty_format_edge(self, edge, width=None):
        """
        override to limit the mumber of characters printed
        """
        line = FeatureIncrementalChart.pretty_format_edge(self, edge)
        return line[0:400]

    def _trees(self, edge:FGFeatureTreeEdge, complete, memo, tree_class):
        """
        A helper function for ``trees``.

        :param memo: A dictionary used to record the trees that we've
            generated for each edge, so that when we see an edge more
            than once, we can reuse the same trees.
        """
        # If we've seen this edge before, then reuse our old answer.
        if edge in memo:
            return memo[edge]

        # when we're reading trees off the chart, don't use incomplete edges
        if complete and edge.is_incomplete():
            return []

        # Leaf edges.
        if isinstance(edge, LeafEdge):
            leaf = self._tokens[edge.start()]
            memo[edge] = [leaf]
            return [leaf]

        # Until we're done computing the trees for edge, set
        # memo[edge] to be empty.  This has the effect of filtering
        # out any cyclic trees (i.e., trees that contain themselves as
        # descendants), because if we reach this edge via a cycle,
        # then it will appear that the edge doesn't generate any trees.
        memo[edge] = []
        trees = []

        ### only addition to overridden method
        lhs = edge.lhs().symbol()
        # lhs = edge.lhs().symbol().copy()
        # lhs.span = edge.span()
        # lhs.tokens = self._tokens       # make pointer to tokens available
        ###

        # Each child pointer list can be used to form trees.
        for cpl in self.child_pointer_lists(edge):
            # Get the set of child choices for each child pointer.
            # child_choices[i] is the set of choices for the tree's
            # ith child.
            child_choices = [self._trees(cp, complete, memo, tree_class)
                             for cp in cpl]

            # For each combination of children, add a tree.
            for children in itertools.product(*child_choices):
                trees.append(tree_class(lhs, children))

        # If the edge is incomplete, then extend it with "partial trees":
        if edge.is_incomplete():
            unexpanded = [tree_class(elt,[])
                          for elt in edge.rhs()[edge.dot():]]
            for tree in trees:
                tree.extend(unexpanded)

        # Update the memoization dictionary.
        memo[edge] = trees

        # Return the list of trees.
        return trees


class FGGrammar(FeatureGrammar):
    def __init__(self, start, productions):
        """
        Create a new feature-based grammar, from the given start
        state and set of ``Productions``.

        :param start: The start symbol
        :type start: FGFeatStructNonterminal
        :param productions: The list of productions that defines the grammar
        :type productions: list(Production)
        """
        FeatureGrammar.__init__(self, start, productions)


    @classmethod
    def fromstring(cls, input, features=None, logic_parser=None, fstruct_reader=None,
                   encoding=None):
        """
        Return a feature structure based ``FeatureGrammar``.

        :param input: a grammar, either in the form of a string or else
        as a list of strings.
        :param features: a tuple of features (default: SLASH, TYPE)
        :param logic_parser: a parser for lambda-expressions,
        by default, ``LogicParser()``
        :param fstruct_reader: a feature structure parser
        (only if features and logic_parser is None)
        """
        if features is None:
            features = (TYPE, SLASH)

        if fstruct_reader is None:
            fstruct_reader = FeatStructReader(features, FGFeatStructNonterminal, FeatListNonterminal,
                                              logic_parser=logic_parser)
        elif logic_parser is not None:
            raise Exception('\'logic_parser\' and \'fstruct_reader\' must '
                            'not both be set')

        start, productions = read_grammar(input, fstruct_reader.read_partial,
                                          encoding=encoding)

        # Add the whole lexicon

        # for wordtuple, featlist in lexicon.lexicon.items():
        #     for lexent in featlist:
        #         lexlhs = lexent
        #         newprod = Production(lexlhs, ['_'.join(wordtuple)])
        #         productions.append(newprod)

        return FGGrammar(start, productions)

    def check_coverage(self, tokens):
        '''
        Override the checking of lexical entries since we have already
        :param tokens:
        :return:
        '''
        pass

# BU_LC_FEATURE_STRATEGY = [LeafInitRule(),
#                           FeatureEmptyPredictRule(),
#                           FeatureBottomUpPredictCombineRule(),
#                           FGFeatureSingleEdgeFundamentalRule()]

# def patch__init__(self, grammar, **parser_args):
#         FeatureChartParser.__init__(self, grammar, BU_LC_FEATURE_STRATEGY, **parser_args)

# FeatureBottomUpLeftCornerChartParser.__init__ = patch__init__

class FGParser():

    def __init__(self, grammarfile='flg.fcfg', trace=1, parser=FeatureEarleyChartParser):
        with open(grammarfile, 'r', encoding='utf-8') as gf:
            gs = gf.read()
        self._grammar = FGGrammar.fromstring(gs, features=(TYPE, SLASH) + defaultfeatures)

        self._parser = parser(self._grammar, trace=trace, chart_class=FGChart)
        self._chart = None

    def parse(self, tokens, cleantree=True, maxtrees=200):
        '''
        :type tokens: builtins.generator
        :return:
        '''
        # check for tokens added by the POS processor -- e.g. ADV
        newprod = False
        # Add a comma and a terminal token to beginning and end of phrase
        COMMA = FGTerminal(',', 'COMMA', tokens[-1].slice.stop)
        COMMA.lexentry = lexicon[(',',)]
        tokens = [FGTerminal('¢', 'EOP', 0)] + tokens + [COMMA] + [FGTerminal('$', 'EOP', tokens[-1].slice.stop)]

        for tokenindex, fltoken in enumerate(tokens):
            if not self._grammar._lexical_index.get(fltoken.lexword):
                newprod = True
                for lexent in fltoken.lexentry:
                    lexrhs = fltoken.lexword
                    newprod = Production(lexent, (lexrhs,))
                    # newprod._lhs.span = (tokenindex, tokenindex+1)
                    # newprod._lhs.tokens = tokens
                    self._grammar._productions.append(newprod)
        if newprod:
            self._grammar.__init__(self._grammar._start, self._grammar._productions)

        self._chart = self._parser.chart_parse([tk for tk in tokens if tk.POS != 'NULL'])
        # self._chart = self._parser.chart_parse([FGLeaf(tk) for tk in tokens if tk.POS != 'NULL'])
        treegen = self._chart.parses(self._grammar.start(), tree_class=Tree)
        trees = []
        for i, tree in enumerate(treegen):
            if i >= maxtrees:
                break
            if cleantree:
                cleanparsetree(tree)
            if tree not in trees:
                trees.append(tree)
        return trees

    def partialparses(self):
        '''
        In a failed parse check for candidate trees labelled with CHAR
        parse must have been called first! to generate the chart
        '''

        trees = []

        charedges = list(self.simple_select(is_complete=True, lhs='SUBJECT'))
        for charedge in charedges:
            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                trees.append((tree, charedge.start(), charedge.end()))

        charedges = list(self.simple_select(is_complete=True, lhs='CHAR'))

        for charedge in charedges:
            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                newtree = False
                if not trees:
                    trees.append((tree, charedge.start(), charedge.end()))
                else:
                    for (t, tstart, tend) in trees[:]:
                        if charedge.start() <= tstart and charedge.end() >= tend:  # subsumes
                            trees.remove((t, tstart, tend))
                        elif (charedge.start() >= tstart and charedge.end() < tend) \
                                or (
                                                charedge.start() > tstart and charedge.end() <= tend):  # subsumed
                            newtree = False
                            continue
                        newtree = True
                    if newtree:
                        trees.append((tree, charedge.start(), charedge.end()))

        return [t for t, _, _ in trees]

    def listSUBJ(self):
        '''
        List all trees labelled with SUBJECT
        Choose the longest edges!
        parse must have been called first! to generate the chart
        '''

        trees = []
        subjend = 0

        charedges = list(self.simple_select(is_complete=True, lhs='SUBJECT'))
        for charedge in charedges:
            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                trees.append((tree, charedge.start(), charedge.end()))
        return [(t, self._chart._tokens[start].slice.start, self._chart._tokens[end-1].slice.stop) for t, start, end in trees]

    def listCHARs(self):
        '''
        List all trees labelled with CHAR
        Choose the longest edges!
        parse must have been called first! to generate the chart
        '''

        trees = []
        subjend = 0

        charedges = list(self.simple_select(is_complete=True, lhs='SUBJECT'))

        if charedges:
            charedge = max(charedges, key=lambda edge: edge.length())

            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                trees.append((tree, charedge.start(), charedge.end()))
                subjend = charedge.end()

        charedges = [edge for edge in self.simple_select(is_complete=True, lhs='CHAR') if edge.start() >= subjend]

        for charedge in charedges:
            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                newtree = False
                if not trees:
                    trees.append((tree, charedge.start(), charedge.end()))
                else:
                    for (t, tstart, tend) in trees[:]:
                        if charedge.start() <= tstart and charedge.end() >= tend:  # subsumes
                            trees.remove((t, tstart, tend))
                        elif (charedge.start() >= tstart and charedge.end() < tend) \
                                or (charedge.start() > tstart and charedge.end() <= tend):  # subsumed
                            newtree = False
                            continue
                        newtree = True
                    if newtree:
                        trees.append((tree, charedge.start(), charedge.end()))

        return [(t, self._chart._tokens[start].slice.start, self._chart._tokens[end-1].slice.stop) for t, start, end in trees]

    def simple_select(self, **restrictions):
        """
        Returns an iterator over the edges in this chart.
        See ``Chart.select`` for more information about the
        ``restrictions`` on the edges.
        """
        # If there are no restrictions, then return all edges.
        if restrictions == {}:
            yield self._chart.edges()
            return

        # Make sure it's a valid index.
        # for key in restrictions.keys():
        # if not hasattr(EdgeI, key):
        #         raise ValueError('Bad restriction: %s' % key)

        for edge in self._chart.edges():
            matched = True
            for key, val in restrictions.items():
                edval = self._chart._get_type_if_possible(getattr(edge, key)())
                if val != edval:
                    matched = False
                    break
            if matched:
                yield edge


class FGTerminal(FlToken):

    def __init__(self, char, type, position):
        self.lexword = char
        self.POS = 'EOP'
        self.slice = slice(position, position)

    @property
    def text(self):
        return self.lexword

    def __repr__(self):
        return self.text


def cleanparsetree(tree):
    purgenodes(tree, ['CTERMINATOR'])
    flattentree(tree, 'CHARLIST')
    collapse_unary(tree)


def collapse_unary(tree, collapsePOS=False, collapseRoot=False, joinChar="+"):
    """
    Collapse subtrees with a single child (ie. unary productions)
    into a new non-terminal (Tree node) joined by 'joinChar'.
    This is useful when working with algorithms that do not allow
    unary productions, and completely removing the unary productions
    would require loss of useful information.  The Tree is modified
    directly (since it is passed by reference) and no value is returned.

    :param tree: The Tree to be collapsed
    :type  tree: Tree
    :param collapsePOS: 'False' (default) will not collapse the parent of leaf nodes (ie.
                        Part-of-Speech tags) since they are always unary productions
    :type  collapsePOS: bool
    :param collapseRoot: 'False' (default) will not modify the root production
                         if it is unary.  For the Penn WSJ treebank corpus, this corresponds
                         to the TOP -> productions.
    :type collapseRoot: bool
    :param joinChar: A string used to connect collapsed node values (default = "+")
    :type  joinChar: str
    """

    if collapseRoot == False and isinstance(tree, Tree) and len(tree) == 1:
        nodeList = [tree[0]]
    else:
        nodeList = [tree]

    # depth-first traversal of tree
    while nodeList != []:
        node = nodeList.pop()
        if isinstance(node, Tree):
            if len(node) == 1 and isinstance(node[0], Tree) and (collapsePOS == True or isinstance(node[0, 0], Tree)):
                node[0:] = [child for child in node[0]]
                # since we assigned the child's children to the current node,
                # evaluate the current node again
                nodeList.append(node)
            else:
                for child in node:
                    nodeList.append(child)


def purgenodes(tree, typelist):
    if isinstance(tree, Tree):
        for i, child in enumerate(tree):
            if isinstance(child, Tree) and isinstance(child.label(), FeatStructNonterminal) and child.label()[
                TYPE] in typelist:
                del tree[i]
            else:
                purgenodes(child, typelist)


def flattentree(tree: Tree, listnodetype):
    # Traverse the tree-depth first keeping a pointer to the parent for modification purposes.
    nodeList = [(tree, [])]
    while nodeList != []:
        node, parent = nodeList.pop()
        if isinstance(node, Tree):
            # if the node contains the 'childChar' character it means that
            # it is an artificial node and can be removed, although we still need
            # to move its children to its parent
            if isinstance(node.label(), FeatStructNonterminal) and node.label()[TYPE] == listnodetype:
                nodeIndex = parent.index(node)
                del parent[nodeIndex]
                # Generated node was on the left if the nodeIndex is 0 which
                # means the grammar was left factored.  We must insert the children
                # at the beginning of the parent's children
                if nodeIndex == 0:
                    parent.insert(0, node[0])
                    if len(node) > 1:
                        parent.insert(1, node[1])
                else:
                    parent.extend(node[:])

                # parent is now the current node so the children of parent will be added to the agenda
                node = parent

            for child in node:
                nodeList.append((child, node))


def FindNode(lab: str, tree: Tree) -> Tree:
    if tree.label()[TYPE] == lab:
        return tree
    for t in tree:
        if isinstance(t, Tree):
            return FindNode(lab, t)


class FeatListNonterminal(FeatList, Nonterminal):
    """A feature structure that's also a nonterminal.  It acts as its
    own symbol, and automatically freezes itself when hashed."""

    def __hash__(self):
        self.freeze()
        return FeatStruct.__hash__(self)

    def symbol(self):
        return self
