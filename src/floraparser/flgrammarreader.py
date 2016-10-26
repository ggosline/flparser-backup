# -*- coding: utf-8 -*-
# Natural Language Toolkit: Context Free Grammars
#
# Copyright (C) 2001-2015 NLTK Project
# Author: Steven Bird <stevenbird1@gmail.com>
#         Edward Loper <edloper@gmail.com>
#         Jason Narad <jason.narad@gmail.com>
#         Peter Ljunglöf <peter.ljunglof@heatherleaf.se>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT
#
# modifications by g.gosline@kew.org
#

"""
Copied from nltk grammar
Adds optional nodes to grammar definition
"""
from __future__ import print_function, unicode_literals

import re
from itertools import chain, combinations

from nltk.grammar import Production, ProbabilisticProduction

_ARROW_RE = re.compile(r'\s* -> \s*', re.VERBOSE)
_PROBABILITY_RE = re.compile(r'( \[ [\d\.]+ \] ) \s*', re.VERBOSE)
_TERMINAL_RE = re.compile(r'( "[^"]+" | \'[^\']+\' ) \s*', re.VERBOSE)
_DISJUNCTION_RE = re.compile(r'\| \s*', re.VERBOSE)
_OPTIONAL_RE = re.compile(r'\[\s*', re.VERBOSE)
_OPTIONAL_END_RE = re.compile(r'\]\s*', re.VERBOSE)

def _read_production(line, nonterm_parser, probabilistic=False):
    """
    Parse a grammar rule, given as a string, and return
    a list of productions.
    """
    pos = 0

    # Parse the left-hand side.
    lhs, pos = nonterm_parser(line, pos)

    # Skip over the arrow.
    m = _ARROW_RE.match(line, pos)
    if not m: raise ValueError('Expected an arrow')
    pos = m.end()

    # Parse the right hand side.
    probabilities = [0.0]
    rhsides = [[]]
    optionals =[[]]              # keep track of optional productions
    while pos < len(line):
        # Probability.
        m = _PROBABILITY_RE.match(line, pos)
        if probabilistic and m:
            pos = m.end()
            probabilities[-1] = float(m.group(1)[1:-1])
            if probabilities[-1] > 1.0:
                raise ValueError('Production probability %f, '
                                 'should not be greater than 1.0' %
                                 (probabilities[-1],))

        # Vertical bar -- start new rhside.
        elif line[pos] == '|':
            m = _DISJUNCTION_RE.match(line, pos)
            probabilities.append(0.0)
            rhsides.append([])
            optionals.append([])
            pos = m.end()

       # String -- add terminal.
        elif line[pos] in "\'\"":
            m = _TERMINAL_RE.match(line, pos)
            if not m: raise ValueError('Unterminated string')
            rhsides[-1].append(m.group(1)[1:-1])
            optionals[-1].append(False)
            pos = m.end()

        # Opening bracket -- start optional production.
        elif line[pos] == '[':
            m = _OPTIONAL_RE.match(line, pos)   # just get rid of spaces

            pos = m.end()
            # should refactor out the following
            if line[pos] in "\'\"":
                m = _TERMINAL_RE.match(line, pos)
                if not m: raise ValueError('Unterminated string')
                rhsides[-1].append(m.group(1)[1:-1])
                pos = m.end()
            else:
                nonterm, pos = nonterm_parser(line, pos)  # Eats the spaces
                rhsides[-1].append(nonterm)
            # end of refactor
            optionals[-1].append(True)
            if line[pos] != ']':
                raise ValueError('Unterminated optional bracket')
            m = _OPTIONAL_END_RE.match(line, pos)
            pos = m.end()

        # Anything else -- nonterminal.
        else:
            nonterm, pos = nonterm_parser(line, pos)  # Eats the spaces
            rhsides[-1].append(nonterm)
            optionals[-1].append(False)

    # Expand productions with optional elements
    rhsides_temp = []

    for (optionality, rhs) in zip (optionals, rhsides):   # in case there were more than one separated by | (disjunction)
        if True in optionality:
            if  probabilistic: raise ValueError('Optional terms not allowed in probalistic grammar')
            optterms = [i for (i, isopt) in enumerate(optionality) if isopt]
            opttermlists = powerset(optterms)              # all possible combinations of optionals
            for optlist in opttermlists:
                rhstemp = rhs[:]
                for i in sorted(optlist, reverse=True):
                    del rhstemp[i]
                rhsides_temp.append(rhstemp)
            pass
        else:
            rhsides_temp.append(rhs)
    # probablities won't work with optionality!
    if probabilistic:
        return [ProbabilisticProduction(lhs, rhs, prob=probability)
                for (rhs, probability) in zip(rhsides, probabilities)]
    else:
        return [Production(lhs, rhs) for rhs in rhsides_temp]


#################################################################
# Reading Phrase Structure Grammars
#################################################################

def read_grammar(input, nonterm_parser, probabilistic=False, encoding=None):
    """
    Return a pair consisting of a starting category and a list of
    ``Productions``.

    :param input: a grammar, either in the form of a string or else
        as a list of strings.
    :param nonterm_parser: a function for parsing nonterminals.
        It should take a ``(string, position)`` as argument and
        return a ``(nonterminal, position)`` as result.
    :param probabilistic: are the grammar rules probabilistic?
    :type probabilistic: bool
    :param encoding: the encoding of the grammar, if it is a binary string
    :type encoding: str
    """
    if encoding is not None:
        input = input.decode(encoding)
    if isinstance(input, str):
        lines = input.split('\n')
    else:
        lines = input

    start = None
    productions = []
    continue_line = ''
    for linenum, line in enumerate(lines):
        line = continue_line + line.strip()
        if line.startswith('#') or line=='': continue
        if line.endswith('\\'):
            continue_line = line[:-1].rstrip()+' '
            continue
        continue_line = ''
        try:
            if line[0] == '%':
                directive, args = line[1:].split(None, 1)
                if directive == 'start':
                    start, pos = nonterm_parser(args, 0)
                    if pos != len(args):
                        raise ValueError('Bad argument to start directive')
                else:
                    raise ValueError('Bad directive')
            else:
                # expand out the disjunctions on the RHS
                productions += _read_production(line, nonterm_parser, probabilistic)
        except ValueError as e:
            raise ValueError('Unable to parse line %s: %s\n%s' %
                             (linenum+1, line, e))

    if not productions:
        raise ValueError('No productions found!')
    if not start:
        start = productions[0].lhs()
    return (start, productions)

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))