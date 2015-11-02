__author__ = 'gg12kg'

from nltk.parse.featurechart import FeatureSingleEdgeFundamentalRule, FeatureTreeEdge, FeatureChart,\
    BU_LC_FEATURE_STRATEGY, FeatureBottomUpPredictCombineRule, FeatureEmptyPredictRule, FeatureChartParser

from nltk.grammar import FeatureGrammar, FeatStructNonterminal, FeatStructReader,\
    read_grammar, SLASH, TYPE, Production, \
    Nonterminal
from nltk.sem import Variable
from nltk.parse.chart import TreeEdge, FundamentalRule, SingleEdgeFundamentalRule, LeafInitRule, EdgeI
from nltk.grammar import FeatureValueType, is_nonterminal
from nltk.featstruct import FeatStruct, Feature, FeatList, FeatDict, unify
from floraparser.fltoken import FlToken
from nltk import Tree
from nltk.parse.earleychart import FeatureIncrementalChart, FeatureEarleyChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser

class FGFeatureSingleEdgeFundamentalRule(SingleEdgeFundamentalRule):
    """
    A specialized version of the completer / single edge fundamental rule
    that operates on nonterminals whose symbols are ``FeatStructNonterminal``s.
    Rather than simply comparing the nonterminals for equality, they are
    unified.
    """
    #_fundamental_rule = FGFeatureFundamentalRule()

    def _apply_complete(self, chart, grammar, right_edge):
        fr = self._fundamental_rule
        for left_edge in chart.select(end=right_edge.start(),
                                      is_complete=False,
                                      nextsym=right_edge.lhs()):
            for new_edge in fr.apply(chart, grammar, left_edge, right_edge):
                yield new_edge

        for left_edge in chart.select(end=right_edge.start(),
                                      is_complete=False,
                                      nextsym_isvar=True):
            for new_edge in fr.apply(chart, grammar, left_edge, right_edge):
                yield new_edge

    def _apply_incomplete(self, chart, grammar, left_edge):
        fr = self._fundamental_rule
        for right_edge in chart.select(start=left_edge.end(),
                                       is_complete=True,
                                       lhs=left_edge.nextsym()):
            for new_edge in fr.apply(chart, grammar, left_edge, right_edge):
                yield new_edge


class FGFeatureTreeEdge(FeatureTreeEdge):

    def __init__(self, span, lhs, rhs, dot=0, bindings=None):
        """
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

        if dot == len(rhs):
            unify_heads(span, lhs, rhs)

        # Initialize the edge.
        TreeEdge.__init__(self, span, lhs, rhs, dot)
        self._bindings = bindings
        self._comparison_key = (self._comparison_key, tuple(sorted(bindings.items())))

    def nextsym_isvar(self):
        ns = self.nextsym()
        if not isinstance(ns, FeatStruct): return False
        if isinstance(ns.get('*type*'), Variable): return True
        return False

def unify_heads(span, lhs, rhs):
    """
    If the edge is a ``FeatureTreeEdge``, and it is complete,
    then unify the head feature on the LHS with the head feature
    in the head daughter on the RHS.
    Head daughter marked with feature +HD.
    Head feature is H.
    """
    # if span[0] != span[1]:
    #     lhs.update(span=((tokens[span[0]].slice.start), tokens[span[1] - 1].slice.stop-1))

    head_prod = [prod for prod in rhs if isinstance(prod, FeatStruct) and prod.has_key("HD")]  # should be just one

    if not head_prod: return
    rhead = head_prod[0]['H']
    lhead = lhs.get('H', FeatStructNonterminal([]))
    newH = lhead.unify(rhead, trace=0)
    if newH:
        lhs['H'] = newH
    else:
        lhs['H'] = rhead
        print('FAIL to unify heads')
    lhs['span'] = span
    # if not isinstance(rhead, FeatDict):
    #     lhs['H'] = rhead
    # else:
    #     lhs['H'].update(head_prod[0]['H'])   # copy rather than unify which has trouble with lists

FeatureTreeEdge.__init__ = FGFeatureTreeEdge.__init__
EdgeI.nextsym_isvar = FGFeatureTreeEdge.nextsym_isvar
FeatureTreeEdge.nextsym_isvar = FGFeatureTreeEdge.nextsym_isvar

class FGChart(FeatureChart):

    def pretty_format_edge(self, edge, width=None):
        line = FeatureIncrementalChart.pretty_format_edge(self, edge)
        return line[0:400]

class FGFeatureFundamentalRule(FundamentalRule):
    """
    A specialized version of the fundamental rule that operates on
    nonterminals whose symbols are ``FeatStructNonterminal``s.  Rather
    tha simply comparing the nonterminals for equality, they are
    unified.  Variable bindings from these unifications are collected
    and stored in the chart using a ``FeatureTreeEdge``.  When a
    complete edge is generated, these bindings are applied to all
    nonterminals in the edge.

    The fundamental rule states that:

    - ``[A -> alpha \* B1 beta][i:j]``
    - ``[B2 -> gamma \*][j:k]``

    licenses the edge:

    - ``[A -> alpha B3 \* beta][i:j]``

    assuming that B1 and B2 can be unified to generate B3.
    """
    def apply(self, chart, grammar, left_edge, right_edge):
        # Make sure the rule is applicable.
        if not (left_edge.end() == right_edge.start() and
                left_edge.is_incomplete() and
                right_edge.is_complete() and
                isinstance(left_edge, FeatureTreeEdge)):
            return
        found = right_edge.lhs()
        nextsym = left_edge.nextsym()
        if isinstance(right_edge, FeatureTreeEdge):
            if not is_nonterminal(nextsym): return
            # if nextsym()[TYPE] != found[TYPE]: return
            # Create a copy of the bindings.
            bindings = left_edge.bindings()
            # We rename vars here, because we don't want variables
            # from the two different productions to match.
            found = found.rename_variables(used_vars=left_edge.variables())
            # Unify B1 (left_edge.nextsym) with B2 (right_edge.lhs) to
            # generate B3 (result).
            result = unify(nextsym, found, bindings, rename_vars=False)
            if result is None: return
        else:
            if nextsym != found: return
            # Create a copy of the bindings.
            bindings = left_edge.bindings()

        # Construct the new edge.
        new_edge = left_edge.move_dot_forward(right_edge.end(), bindings)

        # Add it to the chart, with appropriate child pointers.
        if chart.insert_with_backpointer(new_edge, left_edge, right_edge):
            yield new_edge

FGFeatureSingleEdgeFundamentalRule._fundamental_rule = FGFeatureFundamentalRule

class FGGrammar(FeatureGrammar):
    def __init__(self, start, productions):
        """
        Create a new feature-based grammar, from the given start
        state and set of ``Productions``.

        :param start: The start symbol
        :type start: FeatStructNonterminal
        :param productions: The list of productions that defines the grammar
        :type productions: list(Production)
        """
        FeatureGrammar.__init__(self, start, productions)

    def _calculate_indexes(self):
        super()._calculate_indexes()
        self._lhs_var_productions = []
        self._rhs_var_productions = []
        for prod in self._productions:
            # Left hand side.
            lhs = self._get_type_if_possible(prod._lhs)
            if isinstance(lhs, FeatureValueType) and isinstance(lhs._value, Variable):
                self._lhs_var_productions.append(prod)
            if prod._rhs:
                # First item in right hand side.
                rhs0 = self._get_type_if_possible(prod._rhs[0])
                if isinstance(rhs0, FeatureValueType) and isinstance(rhs0._value, Variable):
                    self._rhs_var_productions.append(prod)

    def productions(self, lhs=None, rhs=None, empty=False):
        """
        Return the grammar productions, filtered by the left-hand side
        or the first item in the right-hand side.

        :param lhs: Only return productions with the given left-hand side.
        :param rhs: Only return productions with the given first item
            in the right-hand side.
        :param empty: Only return productions with an empty right-hand side.
        :rtype: list(Production)
        """
        if rhs and empty:
            raise ValueError("You cannot select empty and non-empty "
                             "productions at the same time.")

        # no constraints so return everything
        if not lhs and not rhs:
            if empty:
                return self._empty_productions
            else:
                return self._productions

        # only lhs specified so look up its index
        elif lhs and not rhs:
            if empty:
                return self._empty_index.get(self._get_type_if_possible(lhs), [])
            else:
                return self._lhs_index.get(self._get_type_if_possible(lhs), []) + \
                            self._lhs_var_productions

        # only rhs specified so look up its index
        elif rhs and not lhs:
            return self._rhs_index.get(self._get_type_if_possible(rhs), []) + \
                            self._rhs_var_productions

        # intersect
        else:
            return [prod for prod in self._lhs_index.get(self._get_type_if_possible(lhs), [])
                    if prod in self._rhs_index.get(self._get_type_if_possible(rhs), [])]


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
            fstruct_reader = FeatStructReader(features, FeatStructNonterminal, FeatListNonterminal,
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

BU_LC_FEATURE_STRATEGY = [LeafInitRule(),
                          FeatureEmptyPredictRule(),
                          FeatureBottomUpPredictCombineRule(),
                          FGFeatureSingleEdgeFundamentalRule()]

def patch__init__(self, grammar, **parser_args):
        FeatureChartParser.__init__(self, grammar, BU_LC_FEATURE_STRATEGY, **parser_args)

FeatureBottomUpLeftCornerChartParser.__init__ = patch__init__

class FGParser():

    def __init__(self, grammarfile='flg.fcfg', trace=1, parser=FeatureEarleyChartParser):
        with open(grammarfile, 'r', encoding='utf-8') as gf:
            gs = gf.read()
        self._grammar = FGGrammar.fromstring(gs)

        self._parser = parser(self._grammar, trace=trace, chart_class=FGChart)
        self._chart = None

    def parse(self, tokens, cleantree=True, maxtrees=200):
        '''
        :type tokens: builtins.generator
        :return:
        '''
        # check for tokens added by the POS processor -- e.g. ADV
        newprod = False
        for fltoken in tokens:
            if not self._grammar._lexical_index.get(fltoken.lexword):
                newprod = True
                for lexent in fltoken.lexentry:
                    lexrhs = fltoken.lexword
                    newprod = Production(lexent, (lexrhs,))
                    self._grammar._productions.append(newprod)
        if newprod:
            self._grammar.__init__(self._grammar._start, self._grammar._productions)

        # Add a terminal token to beginning and end of pharase
        tokens = [FGTerminal('¢', 0)] + tokens + [FGTerminal('$', tokens[-1].slice.stop)]

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

    def listCHARs(self):
        '''
        List all trees labelled with CHAR
        Choose the longest edges!
        parse must have been called first! to generate the chart
        '''

        trees = []

        charedges = list(self.simple_select(is_complete=True, lhs='SUBJECT'))
        for charedge in charedges:
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
    def __init__(self, char, position):
        self.lexword = char
        self.POS = 'EOP'
        self.slice = slice(position, position)

    @property
    def text(self):
        return self.lexword

    def __repr__(self):
        return 'EOPHRASE'


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

def PrintStruct(struct, indent: int = 0):
    if isinstance(struct,FeatDict):
        for (fname, fval) in struct._items():
            print('\t'*indent, fname.upper())
            PrintStruct(fval, indent+1)
    elif isinstance(struct, tuple) or isinstance(struct, frozenset):
        for listitem in struct:
            PrintStruct(listitem, indent+1)
    else:
        print ('\t'*indent, struct)

