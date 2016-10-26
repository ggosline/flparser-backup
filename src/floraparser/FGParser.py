__author__ = 'gg12kg'

import copy
import itertools

from nltk import featstruct
from nltk import Tree
from nltk.featstruct import FeatStruct, FeatList, FeatureValueTuple, _substitute_bindings
from nltk.grammar import FeatureGrammar, FeatStructNonterminal, FeatStructReader,\
    SLASH, TYPE, Production, \
    Nonterminal
from nltk.parse.chart import LeafEdge
from nltk.parse.earleychart import FeatureIncrementalChart, FeatureEarleyChartParser
from nltk.parse.featurechart import FeatureTreeEdge, FeatureChart
from nltk.sem import Variable
from nltk.sem.logic import SubstituteBindingsI

from floraparser.FGFeatStructNonterminal import FGFeatStructNonterminal
from floraparser.flgrammarreader import read_grammar
from floraparser.fltoken import FlToken
from floraparser.lexicon import defaultfeatures
from floraparser.lexicon import lexicon

# Try to monkeypatch the problem in FeatStruct

def _substitute_bindings(fstruct, bindings, fs_class, visited):
    # Visit each node only once:
    if id(fstruct) in visited: return
    visited.add(id(fstruct))

    if _is_mapping(fstruct): items = fstruct.items()
    elif _is_sequence(fstruct): items = enumerate(fstruct)
    else: raise ValueError('Expected mapping or sequence')
    for (fname, fval) in items:
        while (isinstance(fval, Variable) and fval in bindings):
            # old line led to problems with trying to modify frozen featstruct
            # fval = fstruct[fname] = bindings[fval]
            fval = fstruct[fname] = copy.deepcopy(bindings[fval])
        if isinstance(fval, fs_class):
            _substitute_bindings(fval, bindings, fs_class, visited)
        elif isinstance(fval, SubstituteBindingsI):
            fstruct[fname] = fval.substitute_bindings(bindings)

featstruct._substitute_bindings = _substitute_bindings

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
        # Note that overridden deepcopy loses values of our SPAN!
        if dot == len(rhs):
            # purge variables!
            lhs = remove_variables(lhs)
            unify_heads(self, span, lhs, rhs)
            lhs.span = span
        # end of added code

        # Initialize the edge.
        # TreeEdge.__init__(self, span, lhs, rhs, dot)
        self._span = span
        self._lhs = lhs
        rhs = tuple(rhs)
        self._rhs = rhs
        self._dot = dot
        self._bindings = bindings
        self._comparison_key = ((span, lhs, rhs, dot), tuple(sorted(bindings.items())))

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
        if lhs.get('H'):
            lhs['H'].span = span
        return
    rhead = head_prod[0]['H']
    rhead = remove_variables(rhead)
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

    newH.span = span
    lhs['H'] = newH

def _naive_unify(fstruct1:FeatStruct, fstruct2:FeatStruct):

    newfs = copy.copy(fstruct1)
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
        newfs = tuple([t for t in newfs if not isinstance(t, Variable)])
        return newfs # Contains the unified value.

    else:
        return None

# modify remove_variables to handle tuple types with variables
# drop them if they are empty when done!

def remove_variables(fstruct, fs_class='default'):
    """
    :rtype: FeatStruct
    :return: The feature structure that is obtained by deleting
        all features whose values are ``Variables``.
    """
    if fs_class == 'default': fs_class = FeatStruct
    return _remove_variables(copy.deepcopy(fstruct), fs_class, set())

def _remove_variables(fstruct, fs_class, visited):
    if id(fstruct) in visited:
        return
    visited.add(id(fstruct))

    if _is_mapping(fstruct):
        items = list(fstruct.items())
    elif _is_sequence(fstruct):
        items = list(enumerate(fstruct))
    else:
        raise ValueError('Expected mapping or sequence')

    for (fname, fval) in items:
        if isinstance(fval, Variable):
            del fstruct[fname]
        elif isinstance(fval, fs_class):
            _remove_variables(fval, fs_class, visited)
        elif _is_sequence(fval):
            fstruct[fname] = FeatureValueTuple([i for i in fval if not isinstance(i,Variable)])
            if not fstruct[fname]:
                del fstruct[fname]

    return fstruct

def _is_mapping(v):
    return hasattr(v, '__contains__') and hasattr(v, 'keys')

def _is_sequence(v):
    return (hasattr(v, '__iter__') and hasattr(v, '__len__') and
            not isinstance(v, str))

def _is_variable(v):
    return isinstance(v, Variable)
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

    def parse(self, phrasetokens, cleantree=True, maxtrees=200):
        '''
        :type tokens: builtins.generator
        :return:
        '''
        # check for tokens added by the POS processor -- e.g. ADV
        newprod = False
        # Add a comma and a terminal token to beginning and end of phrase
        COMMA = FGTerminal(',', 'COMMA', phrasetokens[-1].slice.stop)
        COMMA.lexentry = lexicon[(',',)]
        tokens = [FGTerminal('¢', 'EOP', 0)] + phrasetokens + [COMMA] + [FGTerminal('$', 'EOP', phrasetokens[-1].slice.stop)]

        for tokenindex, fltoken in enumerate(tokens):
            if not self._grammar._lexical_index.get(fltoken.lexword):
                newprod = True
                for lexent in fltoken.lexentry:
                    lexrhs = fltoken.lexword
                    newprod = Production(lexent, (lexrhs,))
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
                trees.append((tree, charedge.start()+1, charedge.end()))

        return [(t, self._chart._tokens[start].slice.start, self._chart._tokens[end - 1].slice.stop) for t, start, end in trees]

    def listCHARs(self, getCHR=True):
        '''
        List all trees labelled with CHAR
        Choose the longest edges!
        parse must have been called first! to generate the chart
        '''

        subjend = 0

        charedges = list(self.simple_select(is_complete=True, lhs='SUBJECT'))

        if charedges:
            charedge = max(charedges, key=lambda edge: edge.length())

            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                # trees.append((tree, charedge.start()+1 , charedge.end())) # ignore the start of phrase token
                subjend = charedge.end()

        tspans = [(None, (subjend, subjend))]  # A list of trees with span of starting and ending tokens covered
        if getCHR:
            charedges = [edge for edge in self.simple_select(is_complete=True, lhs='CHR') if edge.start() >= subjend]
        else:
            charedges = []
        charedges += [edge for edge in self.simple_select(is_complete=True, lhs='CHAR') if edge.start() >= subjend]
        for charedge in charedges:
            newspan = charedge.span()
            for tspan in tspans:
                if  treesubsumes(tspan[1], newspan) and tspan[1] != newspan:    # An existing edge covers this one; throw it out
                    newspan = tuple()
                    break
            if not newspan:
                continue                    # go to next edge here

            tspans = [t for t in tspans if (not treesubsumes(newspan, t[1])) or newspan == t[1]] # throw out subsumed edges
          # this span is new here -- add all the trees
            for tree in self._chart.trees(charedge, complete=True, tree_class=Tree):
                tspans.append((tree, newspan))
                break                      # just get the first one!

        return [(t, self._chart._tokens[start].slice.start, self._chart._tokens[end-1].slice.stop) for t, (start, end) in tspans if t]

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

def treesubsumes(t1, t2):
    """
    True if span t1 contains all the tokens of span t2
    """
    if t1[0] <= t2[0] and t1[1] >= t2[1]:  # subsumes
        return True
    else:
        return False


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
