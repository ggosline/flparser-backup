# ###############################################################################
#
#   SNOBOL-style pattern matching
#
#   by Gregory Ewing <greg.ewing@canterbury.ac.nz>
#   Free software. May be used without restriction.
#
################################################################################

class Matcher:
    """Matcher() creates a pattern-matching context object. The
    instance dictionary of the matcher object receives the results of any 
    dot-assignments performed during matching, and when evaluating unevaluated
    expressions, it is used as the local namespace."""

    def __init__(self, glob=None):
        if glob is not None:
            self._globals = glob
            # else:
            #    self._globals = globals()

    def match(self, subj, pat, start=None):
        """match(SUBJ, PAT, START=None) attempts to match the string SUBJ 
        against the pattern PAT. If START is specified, the pattern must
        match starting at that position, otherwise it may match anywhere.
        On success, returns a tuple (BEGIN, END[, VALUE]) indicating the matching 
        substring and its yielded value, if any; on failure, returns None. After a 
        successful match, the results of any dot-assignments may be retrieved 
        as attributes of the Matcher instance."""

        pat = _to_pattern(pat)
        if start is not None:
            result = pat.match(subj, start, self.__dict__, (), _succeed)
            if result is not None:
                return (start,) + result
            else:
                return None
        else:
            pos = 0
            max = len(subj)
            while pos <= max:
                result = pat.match(subj, pos, self.__dict__, (), _succeed)
                if result is not None:
                    return (pos,) + result
                pos = pos + 1
            return None

    # George Gosline extension 
    def findall(self, subj, pat, start=None):
        """ Find all sequential matches of PAT in the subject
            Return a list of tuples with the match result plus the dot assignment dictionary (begin, end, value, __dict__)
        """
        pat = _to_pattern(pat)
        mlist = []
        stpos = 0
        maxlen = len(subj)
        while stpos < maxlen:
            # self.__dict__= {}   # variable carry across all the matches???
            result = pat.match(subj, stpos, self.__dict__, (), _succeed)
            if result:
                # mlist.append((stpos,) + result + (self.__dict__.copy(),))
                yield (stpos,) + result + (self.__dict__.copy(),)
                stpos = result[0]
            else:
                stpos = stpos + 1
                # return mlist


    def __str__(self):
        import string

        dict = self.__dict__
        lst = []
        for name in list(dict.keys()):
            if name[:1] != "_":
                lst.append("%s = %s" % (name, repr(dict[name])))
        return "Matcher{%s}" % (", ").join(lst)


def match(subj, pat, start=None):
    """match(SUBJ, PAT, START=None) provides a simplified interface to
    the match method of the Matcher class for when the results of
    dot-assignments are not required. See the docstring of Snobol.Matcher.match
    for full details."""
    return Matcher().match(subj, pat, start)


################################################################################

def _succeed(pos, val):
    """Continuation for successfully terminating a pattern match."""
    return (pos,) + val


def _to_pattern(x):
    """Coerce argument to pattern."""
    if isinstance(x, _Pattern):
        return x
    elif isinstance(x, _UnevaluatedExpression):
        return _UnevaluatedPattern(x)
    else:
        return LIT(x)


################################################################################

class _Formattable:
    def __str__(self):
        return self.format(str)

    def __repr__(self):
        return "Snobol." + self.format(repr)


################################################################################

class _Pattern(_Formattable):
    """
    Base class for Snobol patterns. 
    
    Subclasses must implement a match(SUBJ, POS, ENV, CONT)
    method which attempts to match the pattern against SUBJ starting at POS.
    If successful, it should return the result of calling CONT(POS2) 
    where POS2 is the starting position of the remainder of the string; 
    otherwise, it should return None. ENV is the local namespace dictionary
    for dot-assigments and unevaluated expressions.
    
    Pattern objects support the following pattern construction operators:
    
        pat + pat        sequencing
        pat | pat        alternation
        pat . name        assignment
        pat ^ expr        yielding a value
    """

    def __init__(self):
        pass

    def __add__(self, other):
        return _Seq(self, _to_pattern(other))

    def __radd__(self, other):
        return _Seq(_to_pattern(other), self)

    def __or__(self, other):
        return _Alt(self, _to_pattern(other))

    def __ror__(self, other):
        return _Alt(_to_pattern(other), self)

    def __getattr__(self, name):
        # Following test prevents infinite recursion when the interpreter
        # tries to look up special methods.
        if name[:2] == "__":
            raise AttributeError
        return _Dot(self, name)

    def __xor__(self, expr):
        return _Yield(self, expr, _caller_globals())

    @property
    def _names(self):
        names = set()
        for p in self._pat_tree_traverse(self):
            if isinstance(p, _Dot):
                names.add(p.name)
        return names

    def _pat_tree_traverse(self, p):
        yield p
        if 'pat' in p.__dict__:
            for x in self._pat_tree_traverse(p.pat):
                yield x
        else:
            if 'pat1' in p.__dict__:
                for y in self._pat_tree_traverse(p.pat1):
                    yield y
            if 'pat2' in p.__dict__:
                for z in self._pat_tree_traverse(p.pat2):
                    yield z


################################################################################

class _ArgPattern(_Pattern):
    """Base class for patterns which take an argument, possibly
    an unevaluated expression."""

    def __init__(self, argval):
        super().__init__()
        self.argval = argval

    def arg(self, env):
        """arg(ENV) returns the value of the argument. If it is an
        unevaluated expression, it is evaluated in the local environment
        ENV."""
        argval = self.argval
        if isinstance(argval, _UnevaluatedExpression):
            return argval.eval(env)
        else:
            return argval

    def format(self, subformat):
        argval = self.argval
        if isinstance(argval, _UnevaluatedExpression):
            argstr = argval.format(subformat)
        else:
            argstr = repr(argval)
        return "%s(%s)" % (self.__class__.__name__, argstr)


################################################################################

class _Succeed(_Pattern):
    """Pattern which always succeeds."""

    def match(self, subj, pos, env, val, cont):
        return _succeed(pos, val)

    def format(self, subformat):
        return "SUCCEED"


SUCCEED = _Succeed()

################################################################################

class _Fail(_Pattern):
    """Pattern which always fails."""

    def match(self, subj, pos, env, val, cont):
        return None

    def format(self, subformat):
        return "FAIL"


FAIL = _Fail()


def _fail(pos, val):
    """Continuation for successfully terminating a pattern match."""
    return None


################################################################################

class LIT(_ArgPattern):
    """LIT(STR) matches the literal string STR. It is not usually necessary
    to explicitly instantiate this class, since in most cases a string will 
    be coerced into a pattern automatically when needed."""

    def match(self, subj, pos, env, val, cont):
        tstr = self.arg(env)
        end = pos + len(tstr)
        if subj[pos:end] == tstr:
            return cont(end, val)


################################################################################

class _Arb(_Pattern):
    """A pattern which matches zero or more of any character.
    Matches the shortest possible string."""

    def match(self, subj, pos, env, val, cont):
        max = len(subj)
        while pos <= max:
            result = cont(pos, val)
            if result is not None:
                return result
            pos = pos + 1
        return None

    def format(self, subformat):
        return "ARB"


ARB = _Arb()

################################################################################

class BAL(_ArgPattern):
    """The pattern BAL(STR="()") matches any nonempty string which is balanced
    with respect to the parentheses characters specified by the argument
    string."""

    def __init__(self, str="()"):
        _ArgPattern.__init__(self, str)

    def match(self, subj, pos, env, val, cont):
        bra, ket = self.arg(env)
        pos2 = pos
        max = len(subj)
        depth = 0
        while pos2 < max:
            c = subj[pos2]
            pos2 = pos2 + 1
            if c == bra:
                depth = depth + 1
            elif c == ket:
                depth = depth - 1
            if depth == 0:
                result = cont(pos2, val)
                if result is not None:
                    return result
        return None


################################################################################

class _Rem(_Pattern):
    """A pattern which matches the remainder of the string."""

    def match(self, subj, pos, env, val, cont):
        return cont(len(subj), val)

    def format(self, subformat):
        return "REM"


REM = _Rem()

################################################################################

class ANY(_ArgPattern):
    """ANY(STR) is a pattern which matches exactly one character from STR."""

    def match(self, subj, pos, env, val, cont):
        tstr = self.arg(env)
        if pos < len(subj) and subj[pos] in tstr:
            return cont(pos + 1, val)
        else:
            return None


################################################################################

class ARBNO(_Pattern):
    """ARBNO(PAT) is a pattern which matches zero or more repetitions
    of the pattern PAT."""

    def __init__(self, pat):
        self.pat = _to_pattern(pat)

    def match(self, subj, pos, env, val, cont):
        result = cont(pos, val)
        if result is not None:
            return result
        else:
            return self.pat.match(subj, pos, env, val,
                                  (lambda pos2, val2, self=self, subj=subj, env=env, cont=cont:
                                   self.match(subj, pos2, env, val2, cont)))

    def format(self, subformat):
        return "ARBNO(%s)" % subformat(self.pat)


################################################################################

class BREAK(_ArgPattern):
    """The pattern BREAK(STR) matches zero or more characters
    not in STR which are followed by a character in STR. The
    final character is not included in the match."""

    def match(self, subj, pos, env, val, cont):
        max = len(subj)
        tstr = self.arg(env)
        while pos < max:
            if subj[pos] in tstr:
                return cont(pos, val)
            pos = pos + 1
        return None


################################################################################

class LEN(_ArgPattern):
    """The pattern LEN(NUM) matches exactly NUM characters."""

    def match(self, subj, pos, env, val, cont):
        num = self.arg(env)
        pos = pos + num
        if pos <= len(subj):
            return cont(pos, val)
        else:
            return None


################################################################################

class NOTANY(_ArgPattern):
    """The pattern NOTANY(STR) matches exactly one character not in STR."""

    def match(self, subj, pos, env, val, cont):
        tstr = self.arg(env)
        if pos < len(subj) and subj[pos] not in tstr:
            return cont(pos + 1, val)
        else:
            return None


################################################################################

class POS(_ArgPattern):
    """The pattern POS(NUM) matches at position NUM from the beginning
    of the subject."""

    def match(self, subj, pos, env, val, cont):
        num = self.arg(env)
        if pos == num:
            return cont(pos, val)
        else:
            return None


################################################################################

class RPOS(_ArgPattern):
    """The pattern RPOS(NUM) matches at position NUM from the end
    of the subject."""

    def match(self, subj, pos, env, val, cont):
        num = self.arg(env)
        if pos == len(subj) - num:
            return cont(pos, val)
        else:
            return None


################################################################################

class RTAB(_ArgPattern):
    """The pattern RTAB(NUM) matches 0 or more characters up to position
    NUM from the end of the string."""

    def match(self, subj, pos, env, val, cont):
        num = self.arg(env)
        pos2 = len(subj) - num
        if pos <= pos2:
            return cont(pos2, val)
        else:
            return None


################################################################################

class SPAN(_ArgPattern):
    """The pattern SPAN(STR) matches one or more characters in STR."""

    def match(self, subj, pos, env, val, cont):
        tstr = self.arg(env)
        pos2 = pos
        max = len(subj)
        while pos2 < max and subj[pos2] in tstr:
            pos2 = pos2 + 1
        while pos2 > pos:
            result = cont(pos2, val)
            if result is not None:
                return result
            pos2 = pos2 - 1
        return None


################################################################################

class TAB(_ArgPattern):
    """The pattern TAB(NUM) matches 0 or more characters up to position
    NUM from the beginning of the string."""

    def match(self, subj, pos, env, val, cont):
        pos2 = self.arg(env)
        if pos <= pos2:
            return cont(pos2, val)
        else:
            return None


################################################################################

class _Seq(_Pattern):
    """A pattern which matches the concatenation of two other patterns."""

    def __init__(self, pat1, pat2):
        self.pat1 = pat1
        self.pat2 = pat2

    def match(self, subj, pos, env, val, cont):
        return self.pat1.match(subj, pos, env, val,
                               (lambda pos2, val2, self=self, subj=subj, env=env, cont=cont:
                                self.pat2.match(subj, pos2, env, val2, cont)))

    def __str__(self):
        return "%s+%s" % (self.pat1, self.pat2)

    def __repr__(self):
        return "Snobol._Seq(%s,%s)" % (repr(self.pat1), repr(self.pat2))


################################################################################

class _Alt(_Pattern):
    """A pattern which matches either of two other patterns."""

    def __init__(self, pat1, pat2):
        self.pat1 = pat1
        self.pat2 = pat2

    def match(self, subj, pos, env, val, cont):
        result = self.pat1.match(subj, pos, env, val, cont)
        if result is None:
            result = self.pat2.match(subj, pos, env, val, cont)
        return result

    def __str__(self):
        return "%s|%s" % (self.pat1, self.pat2)

    def __repr__(self):
        return "Snobol._Alt(%s,%s)" % (repr(self.pat1), repr(self.pat2))


################################################################################

class _Dot(_Pattern):
    """A pattern which performs dot-assignment. PAT.NAME matches PAT
    against the subject, and if successful, assigns the value yielded by PAT
    to NAME in the Matcher object and attempts to match the rest of the
    pattern. If backtracking occurs, the previous value of NAME is
    restored. If PAT does not yield a value, the matched string is assigned."""

    def __init__(self, pat, name):
        self.pat = _to_pattern(pat)
        self.name = name

    def match(self, subj, pos, env, val, cont):
        return self.pat.match(subj, pos, env, val,
                              (lambda pos2, val2,
                                      self=self, pos=pos, subj=subj, env=env, val=val, cont=cont:
                               self.assign(subj, pos, pos2, val2, env, val, cont)))

    def assign(self, subj, pos, pos2, val2, dict, val, cont):
        if val2:
            (value,) = val2
        else:
            value = subj[pos:pos2]
        # dict = env.__dict__
        name = self.name
        #print "_Dot.assign: dict =", repr(dict) #@@@
        old = dict.get(name, None)
        dict[name] = value
        result = cont(pos2, val)
        if result is None:
            dict[name] = old
        return result

    def __str__(self):
        return "%s.%s" % (str(self.pat), self.name)

    def __repr__(self):
        return "Snobol._Dot(%s,%s)" % (repr(self.pat), repr(self.name))


################################################################################

class _UnevaluatedExpression(_Formattable):
    """This class encapsulates an unevaluated expression together with
    the global namespace in which it should be evaluated."""

    def __init__(self, expr, globals):
        self.expr = expr
        self.globals = globals
        self.code = compile(expr, "<Snobol unevaluated expression>", "eval")

    def eval(self, env):
        """eval(ENV) evaluates the expression with the dictionary ENV as 
        the local namespace and the previously captured globals as the global 
        namespace."""
        return eval(self.code, self.globals, env)

    def format(self, subformat):
        return "VAL(%s)" % repr(self.expr)


def VAL(expr):
    """VAL(STR) is an unevaluated expression which may be used as a pattern
    element or as an argument to any of the primitive pattern-constructing 
    functions such as SPAN or LEN. Each time it is encountered during matching,
    the Python expression in STR is evaluated. The local namespace for evaluation
    is the instance dictionary of the match object, and the global namespace is
    the one that was in effect when the VAL constructor was called."""

    return _UnevaluatedExpression(expr, _caller_globals())


def _caller_globals():
    """Capture the global environment of the caller of the caller
    of this function."""
    import sys

    try:
        raise _SpanishInquisition
    except _SpanishInquisition:
        return sys.exc_info()[2].tb_frame.f_back.f_back.f_globals


class _SpanishInquisition(Exception):
    """You weren't expecting THIS, were you?"""


################################################################################

class _UnevaluatedPattern(_Pattern):
    """This class represents an unevaluated expression which evaluates to
    a pattern."""

    def __init__(self, expr):
        self.expr = expr

    def match(self, subj, pos, env, val, cont):
        return _to_pattern(self.expr.eval(env)).match(subj, pos, env, val, cont)

    def format(self, subformat):
        return self.expr.format(subformat)


def PAT(expr):
    """PAT(EXPR) is an unevaluated pattern. At matching time, EXPR is
    evaluated and must return a pattern."""
    return _UnevaluatedPattern(_UnevaluatedExpression(expr, _caller_globals()))


################################################################################

class _At(_Pattern):
    """The pattern AT matches the empty string and yields as its value
    the current position in the string."""

    def match(self, subj, pos, env, val, cont):
        return cont(pos, (pos,))

    def format(self, subformat):
        return "AT"


AT = _At()

################################################################################

class _Yield(_Pattern):
    """This class implements the YIELD(PAT, EXPR) or PAT^EXPR construct."""

    def __init__(self, pat, expr, globals):
        self.pat = pat
        self.expr = _UnevaluatedExpression(expr, globals)
        self.variables = pat._names
        pass

    def match(self, subj, pos, env, val, cont):
        env2 = dict.fromkeys(self.variables, None)
        return self.pat.match(subj, pos, env2, (),
                              lambda pos2, val2, self=self, env2=env2, cont=cont:
                              cont(pos2, (self.expr.eval(env2),)))

    def format(self, subformat):
        return "(%s^%s)" % (subformat(self.pat), subformat(self.expr))


def YIELD(pat, expr):
    """The pattern YIELD(PAT, EXPR) matches PAT against the subject and yields the
    result of evaluating the Python expression in the string EXPR as its value.
    Matching of PAT is performed inside a new scope for dot-assignments. This
    construct may also be written: PAT ^ EXPR"""

    return _Yield(pat, expr, _caller_globals())


################################################################################

# ## George Gosline extensions

class ALLOF(_Pattern):
    """ALLOF(PAT) is a pattern which eagerly matches zero or more repetitions
    of the pattern PAT."""

    def __init__(self, pat):
        self.pat = _to_pattern(pat)

    def match(self, subj, pos, env, val, cont):
        stpos = pos
        maxlen = len(subj)
        while stpos < maxlen:
            result = self.pat.match(subj, stpos, env, val, _succeed)
            if result:
                stpos = result[0]
            else:
                break
        result = cont(stpos, val)
        return result

    def format(self, subformat):
        return "ALLOF(%s)" % subformat(self.pat)


if __name__ == "__main__":
    p = (BREAK("x") + ALLOF("x").out) ^ "[out]*3"
    m = Matcher()
    r = m.match("axxxxyy", p)
    print(r, m.out)
