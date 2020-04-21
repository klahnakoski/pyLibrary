# encoding: utf-8
import warnings

from mo_dots import Null
from mo_future import text
from mo_logs import Log, Except

from mo_parsing.engine import noop
from mo_parsing.exceptions import (
    ParseBaseException,
    ParseException,
    RecursiveGrammarException,
)
from mo_parsing.core import ParserElement
from mo_parsing.results import ParseResults, Annotation
from mo_parsing.utils import _MAX_INT

# import later
Token, Literal, Keyword, Word, CharsNotIn, _PositionToken, StringEnd = [None] * 7

_get = object.__getattribute__


class _NullToken(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __str__(self):
        return ""


class ParseElementEnhance(ParserElement):
    """Abstract subclass of :class:`ParserElement`, for combining and
    post-processing parsed tokens.
    """

    def __init__(self, expr):
        ParserElement.__init__(self)
        self.expr = expr = engine.CURRENT.normalize(expr)
        if expr != None:
            self.parser_config.mayIndexError = expr.parser_config.mayIndexError
            self.parser_config.mayReturnEmpty = expr.parser_config.mayReturnEmpty
            self.parser_config.skipWhitespace = expr.parser_config.skipWhitespace

    def copy(self):
        output = ParserElement.copy(self)
        if self.engine is engine.CURRENT:
            output.expr = self.expr
        else:
            output.expr = self.expr.copy()
        return output

    def parseImpl(self, instring, loc, doActions=True):
        if self.expr != None:
            loc, output = self.expr._parse(instring, loc, doActions)
            if output.type_for_result == self:
                Log.error("not expected")
            return loc, ParseResults(self, [output])
        else:
            raise ParseException("", loc, self)

    def leaveWhitespace(self):
        output = self.copy()
        output.parser_config.skipWhitespace = False
        output.expr = self.expr.leaveWhitespace()
        return output

    def streamline(self):
        if self.streamlined:
            return self
        self.streamlined = True
        self.expr.streamline()
        return self

    def checkRecursion(self, parseElementList):
        if self in parseElementList:
            raise RecursiveGrammarException(parseElementList + [self])
        subRecCheckList = parseElementList[:] + [self]
        if self.expr != None:
            self.expr.checkRecursion(subRecCheckList)

    def validate(self, validateTrace=None):
        if validateTrace is None:
            validateTrace = []
        tmp = validateTrace[:] + [self]
        if self.expr != None:
            self.expr.validate(tmp)
        self.checkRecursion([])

    def __str__(self):
        try:
            return super(ParseElementEnhance, self).__str__()
        except Exception as e:
            e = Except.wrap(e)
            pass
        return "%s:(%s)" % (self.__class__.__name__, text(self.expr))


class FollowedBy(ParseElementEnhance):
    """Lookahead matching of the given parse expression.
    ``FollowedBy`` does *not* advance the parsing position within
    the input string, it only verifies that the specified parse
    expression matches at the current position.  ``FollowedBy``
    always returns a null token list. If any results names are defined
    in the lookahead expression, those *will* be returned for access by
    name.

    Example::

        # use FollowedBy to match a label only if it is followed by a ':'
        data_word = Word(alphas)
        label = data_word + FollowedBy(':')
        attr_expr = Group(label + Suppress(':') + OneOrMore(data_word, stopOn=label).setParseAction(' '.join))

        OneOrMore(attr_expr).parseString("shape: SQUARE color: BLACK posn: upper left")

    prints::

        [['shape', 'SQUARE'], ['color', 'BLACK'], ['posn', 'upper left']]
    """

    def __init__(self, expr):
        super(FollowedBy, self).__init__(expr)
        self.parser_config.mayReturnEmpty = True

    def parseImpl(self, instring, loc, doActions=True):
        # by using self._expr.parse and deleting the contents of the returned ParseResults list
        # we keep any named results that were defined in the FollowedBy expression
        loc, result = self.expr._parse(instring, loc, doActions=doActions)
        result.__class__ = Annotation

        return loc, ParseResults(self, [result])


class NotAny(ParseElementEnhance):
    """Lookahead to disallow matching with the given parse expression.
    ``NotAny`` does *not* advance the parsing position within the
    input string, it only verifies that the specified parse expression
    does *not* match at the current position.  Also, ``NotAny`` does
    *not* skip over leading whitespace. ``NotAny`` always returns
    a null token list.  May be constructed using the '~' operator.

    Example::

        AND, OR, NOT = map(CaselessKeyword, "AND OR NOT".split())

        # take care not to mistake keywords for identifiers
        ident = ~(AND | OR | NOT) + Word(alphas)
        boolean_term = Optional(NOT) + ident

        # very crude boolean expression - to support parenthesis groups and
        # operation hierarchy, use infixNotation
        boolean_expr = boolean_term + ZeroOrMore((AND | OR) + boolean_term)

        # integers that are followed by "." are actually floats
        integer = Word(nums) + ~Char(".")
    """

    def __init__(self, expr):
        super(NotAny, self).__init__(expr)
        # do NOT use self.leaveWhitespace(), don't want to propagate to exprs
        self.parser_config.skipWhitespace = False
        self.parser_config.mayReturnEmpty = True

    def parseImpl(self, instring, loc, doActions=True):
        if self.expr.canParseNext(instring, loc):
            raise ParseException(instring, loc, self)
        return loc, ParseResults(self, [])

    def __str__(self):
        if self.parser_name:
            return self.parser_name
        return "~{" + text(self.expr) + "}"


class _MultipleMatch(ParseElementEnhance):
    def __init__(self, expr, stopOn=None):
        super(_MultipleMatch, self).__init__(expr)
        self.stopOn(stopOn)

    def copy(self):
        output = ParseElementEnhance.copy(self)
        output.not_ender = self.not_ender
        return output

    def stopOn(self, ender):
        self.not_ender = ~self.engine.normalize(ender) if ender else None
        return self

    def parseImpl(self, instring, loc, doActions=True):
        self_expr_parse = self.expr._parse
        if self.not_ender is None:
            try_not_ender = noop
        else:
            try_not_ender = self.not_ender.tryParse

        acc = []
        try:
            while True:
                try_not_ender(instring, loc)
                preloc = loc
                loc, tmptokens = self_expr_parse(instring, preloc, doActions)
                if tmptokens:
                    acc.append(tmptokens)
        except (ParseException, IndexError) as e:
            if not acc:
                # MUST HAVE AT LEAST ONE
                raise e

        return loc, ParseResults(self, acc)

    def __call__(self, name):
        if not name:
            return self

        for e in [self.expr]:
            if isinstance(e, ParserElement) and e.token_name:
                Log.error("can not set token name, already set in one of the other expressions")

        return ParseElementEnhance.__call__(self, name)


class OneOrMore(_MultipleMatch):
    """Repetition of one or more of the given expression.

    Parameters:
     - expr - expression that must match one or more times
     - stopOn - (default= ``None``) - expression for a terminating sentinel
          (only required if the sentinel would ordinarily match the repetition
          expression)

    Example::

        data_word = Word(alphas)
        label = data_word + FollowedBy(':')
        attr_expr = Group(label + Suppress(':') + OneOrMore(data_word).setParseAction(' '.join))

        text = "shape: SQUARE posn: upper left color: BLACK"
        OneOrMore(attr_expr).parseString(text)  # Fail! read 'color' as data instead of next label -> [['shape', 'SQUARE color']]

        # use stopOn attribute for OneOrMore to avoid reading label string as part of the data
        attr_expr = Group(label + Suppress(':') + OneOrMore(data_word, stopOn=label).setParseAction(' '.join))
        OneOrMore(attr_expr).parseString(text) # Better -> [['shape', 'SQUARE'], ['posn', 'upper left'], ['color', 'BLACK']]

        # could also be written as
        (attr_expr * (1,)).parseString(text)
    """

    def __str__(self):
        if self.parser_name:
            return self.parser_name

        return "{" + text(self.expr) + "}..."


class ZeroOrMore(_MultipleMatch):
    """Optional repetition of zero or more of the given expression.

    Parameters:
     - expr - expression that must match zero or more times
     - stopOn - (default= ``None``) - expression for a terminating sentinel
          (only required if the sentinel would ordinarily match the repetition
          expression)

    Example: similar to :class:`OneOrMore`
    """

    def __init__(self, expr, stopOn=None):
        super(ZeroOrMore, self).__init__(expr, stopOn=stopOn)
        self.parser_config.mayReturnEmpty = True

    def parseImpl(self, instring, loc, doActions=True):
        try:
            return super(ZeroOrMore, self).parseImpl(instring, loc, doActions)
        except (ParseException, IndexError):
            return loc, ParseResults(self, [])

    def __str__(self):
        if self.parser_name:
            return self.parser_name

        return "[" + text(self.expr) + "]..."


class Optional(ParseElementEnhance):
    """Optional matching of the given expression.

    Parameters:
     - expr - expression that must match zero or more times
     - default (optional) - value to be returned if the optional expression is not found.

    Example::

        # US postal code can be a 5-digit zip, plus optional 4-digit qualifier
        zip = Combine(Word(nums, exact=5) + Optional('-' + Word(nums, exact=4)))
        test.runTests(zip, '''
            # traditional ZIP code
            12345

            # ZIP+4 form
            12101-0001

            # invalid ZIP
            98765-
            ''')

    prints::

        # traditional ZIP code
        12345
        ['12345']

        # ZIP+4 form
        12101-0001
        ['12101-0001']

        # invalid ZIP
        98765-
             ^
        FAIL: Expected end of text (at char 5), (line:1, col:6)
    """

    def __init__(self, expr, default=None):
        super(Optional, self).__init__(expr)
        self.defaultValue = default
        self.parser_config.mayReturnEmpty = True

    def copy(self):
        output = ParseElementEnhance.copy(self)
        output.defaultValue = self.defaultValue
        return output

    def parseImpl(self, instring, loc, doActions=True):
        try:
            loc, tokens = self.expr._parse(instring, loc, doActions)
        except (ParseException, IndexError):
            if self.defaultValue is None:
                return loc, ParseResults(self, [])
            else:
                tokens = self.defaultValue

        return loc, ParseResults(self, [tokens])

    def __str__(self):
        if self.parser_name:
            return self.parser_name

        return "[" + text(self.expr) + "]"


class SkipTo(ParseElementEnhance):
    """Token for skipping over all undefined text until the matched
    expression is found.

    Parameters:
     - expr - target expression marking the end of the data to be skipped
     - include - (default= ``False``) if True, the target expression is also parsed
          (the skipped text and target expression are returned as a 2-element list).
     - ignore - (default= ``None``) used to define grammars (typically quoted strings and
          comments) that might contain false matches to the target expression
     - failOn - (default= ``None``) define expressions that are not allowed to be
          included in the skipped test; if found before the target expression is found,
          the SkipTo is not a match

    Example::

        report = '''
            Outstanding Issues Report - 1 Jan 2000

               # | Severity | Description                               |  Days Open
            -----+----------+-------------------------------------------+-----------
             101 | Critical | Intermittent system crash                 |          6
              94 | Cosmetic | Spelling error on Login ('log|n')         |         14
              79 | Minor    | System slow when running too many reports |         47
            '''
        integer = Word(nums)
        SEP = Suppress('|')
        # use SkipTo to simply match everything up until the next SEP
        # - ignore quoted strings, so that a '|' character inside a quoted string does not match
        # - parse action will call token.strip() for each matched token, i.e., the description body
        string_data = SkipTo(SEP, ignore=quotedString)
        string_data.setParseAction(tokenMap(str.strip))
        ticket_expr = (integer("issue_num") + SEP
                      + string_data("sev") + SEP
                      + string_data("desc") + SEP
                      + integer("days_open"))

        for tkt in ticket_expr.searchString(report):
            print tkt

    prints::

        ['101', 'Critical', 'Intermittent system crash', '6']
        - days_open: 6
        - desc: Intermittent system crash
        - issue_num: 101
        - sev: Critical
        ['94', 'Cosmetic', "Spelling error on Login ('log|n')", '14']
        - days_open: 14
        - desc: Spelling error on Login ('log|n')
        - issue_num: 94
        - sev: Cosmetic
        ['79', 'Minor', 'System slow when running too many reports', '47']
        - days_open: 47
        - desc: System slow when running too many reports
        - issue_num: 79
        - sev: Minor
    """

    def __init__(self, other, include=False, ignore=None, failOn=None):
        super(SkipTo, self).__init__(other)
        self.ignoreExpr = ignore
        self.parser_config.mayReturnEmpty = True
        self.parser_config.mayIndexError = False
        self.includeMatch = include
        self.failOn = engine.CURRENT.normalize(failOn)

    def parseImpl(self, instring, end, doActions=True):
        start = end
        instrlen = len(instring)
        end_parse = self.expr._parse
        self_failOn_canParseNext = (
            self.failOn.canParseNext if self.failOn is not None else None
        )
        self_ignoreExpr_tryParse = (
            self.ignoreExpr.tryParse if self.ignoreExpr is not None else None
        )

        tmploc = end
        while tmploc <= instrlen:
            if self_failOn_canParseNext is not None:
                # break if failOn expression matches
                if self_failOn_canParseNext(instring, tmploc):
                    break

            if self_ignoreExpr_tryParse is not None:
                # advance past ignore expressions
                while 1:
                    try:
                        tmploc = self_ignoreExpr_tryParse(instring, tmploc)
                    except ParseBaseException:
                        break

            try:
                tmploc, _ = end_parse(instring, tmploc, doActions=False)
            except (ParseException, IndexError):
                # no match, advance loc in string
                tmploc += 1
            else:
                # matched skipto expr, done
                break

        else:
            # ran off the end of the input string without matching skipto expr, fail
            raise ParseException(instring, end, self)

        # build up return values
        end = tmploc
        skiptext = instring[start:end]
        skip_result = []
        if skiptext:
            skip_result.append(skiptext)

        if self.includeMatch:
            end, end_result = end_parse(instring, end, doActions)
            skip_result.append(end_result)

        return end, ParseResults(self, skip_result)


class Forward(ParseElementEnhance):
    """Forward declaration of an expression to be defined later -
    used for recursive grammars, such as algebraic infix notation.
    When the expression is known, it is assigned to the ``Forward``
    variable using the '<<' operator.

    Note: take care when assigning to ``Forward`` not to overlook
    precedence of operators.

    Specifically, '|' has a lower precedence than '<<', so that::

        fwdExpr << a | b | c

    will actually be evaluated as::

        (fwdExpr << a) | b | c

    thereby leaving b and c out as parseable alternatives.  It is recommended that you
    explicitly group the values inserted into the ``Forward``::

        fwdExpr << (a | b | c)

    Converting to use the '<<=' operator instead will avoid this problem.

    See :class:`ParseResults.pprint` for an example of a recursive
    parser created using ``Forward``.
    """

    def __init__(self, expr=Null):
        self.expr = Null
        self.strRepr = None  # avoid recursion
        ParseElementEnhance.__init__(self, expr)
        if expr:
            self << expr

    def copy(self):
        return self

    def __lshift__(self, other):
        while isinstance(other, Forward):
            other = other.expr

        expr = self.expr = engine.CURRENT.normalize(other)
        self.expr = expr(self.token_name)
        return self

    def addParseAction(self, action):
        Log.error("not allowed")

    def leaveWhitespace(self):
        output = self.copy()
        output.parser_config.skipWhitespace = False
        return output

    def streamline(self):
        if self.streamlined:
            return self

        self.streamlined = True
        self.expr.streamline()
        return self

    def validate(self, validateTrace=None):
        if validateTrace is None:
            validateTrace = []

        if self not in validateTrace:
            tmp = validateTrace[:] + [self]
            if self.expr != None:
                self.expr.validate(tmp)
        self.checkRecursion([])

    def parseImpl(self, instring, loc, doActions=True):
        if self.expr != None:
            loc, output = self.expr._parse(instring, loc, doActions)
            if output.type_for_result is self:
                Log.error("not expected")
            return loc, output
        else:
            raise ParseException("", loc, self)

    def __str__(self):
        if self.parser_name:
            return self.parser_name

        if self.strRepr:
            return self.strRepr

        self_name = self.__class__.__name__

        # Avoid infinite recursion by setting a temporary strRepr
        self.strRepr = self_name + ": ..."

        # Use the string representation of main expression.
        retString = "..."
        try:
            retString = text(self.expr)[:1000]
        finally:
            self.strRepr = None
        return self_name + ": " + retString

    def __call__(self, name):
        output = self.copy()
        output.token_name = name
        output.expr = output.expr(name)
        return output


class TokenConverter(ParseElementEnhance):
    """
    Abstract subclass of :class:`ParseExpression`, for converting parsed results.
    """
    pass


class Combine(TokenConverter):
    """Converter to concatenate all matching tokens to a single string.
    By default, the matching patterns must also be contiguous in the
    input string; this can be disabled by specifying
    ``'adjacent=False'`` in the constructor.

    Example::

        real = Word(nums) + '.' + Word(nums)
        print(real.parseString('3.1416')) # -> ['3', '.', '1416']
        # will also erroneously match the following
        print(real.parseString('3. 1416')) # -> ['3', '.', '1416']

        real = Combine(Word(nums) + '.' + Word(nums))
        print(real.parseString('3.1416')) # -> ['3.1416']
        # no match when there are internal spaces
        print(real.parseString('3. 1416')) # -> Exception: Expected W:(0123...)
    """

    def __init__(self, expr, joinString="", adjacent=True):
        super(Combine, self).__init__(expr)
        self.adjacent = adjacent
        self.parser_config.skipWhitespace = True
        self.joinString = joinString

    def copy(self):
        output = TokenConverter.copy(self)
        output.adjacent = self.adjacent
        output.joinString = self.joinString
        return output

    def postParse(self, instring, loc, tokenlist):
        retToks = ParseResults(self, [tokenlist.asString(sep=self.joinString)])

        return retToks


class Group(TokenConverter):
    """Converter to return the matched tokens as a list - useful for
    returning tokens of :class:`ZeroOrMore` and :class:`OneOrMore` expressions.

    Example::

        ident = Word(alphas)
        num = Word(nums)
        term = ident | num
        func = ident + Optional(delimitedList(term))
        print(func.parseString("fn a, b, 100"))  # -> ['fn', 'a', 'b', '100']

        func = ident + Group(Optional(delimitedList(term)))
        print(func.parseString("fn a, b, 100"))  # -> ['fn', ['a', 'b', '100']]
    """

    def __init__(self, expr):
        super(Group, self).__init__(expr)

    def postParse(self, instring, loc, tokenlist):
        if tokenlist.type_for_result is not self:
            Log.error("please wrap")

        return tokenlist


class Dict(Group):
    """Converter to return a repetitive expression as a list, but also
    as a dictionary. Each element can also be referenced using the first
    token in the expression as its key. Useful for tabular report
    scraping when the first column can be used as a item key.

    Example::

        data_word = Word(alphas)
        label = data_word + FollowedBy(':')
        attr_expr = Group(label + Suppress(':') + OneOrMore(data_word).setParseAction(' '.join))

        text = "shape: SQUARE posn: upper left color: light blue texture: burlap"
        attr_expr = (label + Suppress(':') + OneOrMore(data_word, stopOn=label).setParseAction(' '.join))

        # print attributes as plain groups
        print(OneOrMore(attr_expr).parseString(text))

        # instead of OneOrMore(expr), parse using Dict(OneOrMore(Group(expr))) - Dict will auto-assign names
        result = Dict(OneOrMore(Group(attr_expr))).parseString(text)
        print(result)

        # access named fields as dict entries, or output as dict
        print(result['shape'])
        print(result)

    prints::

        ['shape', 'SQUARE', 'posn', 'upper left', 'color', 'light blue', 'texture', 'burlap']
        [['shape', 'SQUARE'], ['posn', 'upper left'], ['color', 'light blue'], ['texture', 'burlap']]
        - color: light blue
        - posn: upper left
        - shape: SQUARE
        - texture: burlap
        SQUARE
        {'color': 'light blue', 'posn': 'upper left', 'texture': 'burlap', 'shape': 'SQUARE'}

    See more examples at :class:`ParseResults` of accessing fields by results name.
    """

    def __init__(self, expr):
        super(Dict, self).__init__(expr)

    def postParse(self, instring, loc, tokenlist):
        acc = tokenlist.tokens_for_result
        for a in list(acc):
            for tok in list(a):
                if len(tok) == 0:
                    continue
                ikey = tok[0]
                rest = list(tok[1:])
                new_tok = Annotation(text(ikey), rest)
                acc.append(new_tok)

        return tokenlist


class Suppress(TokenConverter):
    """Converter for ignoring the results of a parsed expression.

    Example::

        source = "a, b, c,d"
        wd = Word(alphas)
        wd_list1 = wd + ZeroOrMore(',' + wd)
        print(wd_list1.parseString(source))

        # often, delimiters that are useful during parsing are just in the
        # way afterward - use Suppress to keep them out of the parsed output
        wd_list2 = wd + ZeroOrMore(Suppress(',') + wd)
        print(wd_list2.parseString(source))

    prints::

        ['a', ',', 'b', ',', 'c', ',', 'd']
        ['a', 'b', 'c', 'd']

    (See also :class:`delimitedList`.)
    """

    def postParse(self, instring, loc, tokenlist):
        return ParseResults(self, [])

    def suppress(self):
        return self

    def __str__(self):
        return text(self.expr)


class PrecededBy(ParseElementEnhance):
    """Lookbehind matching of the given parse expression.
    ``PrecededBy`` does not advance the parsing position within the
    input string, it only verifies that the specified parse expression
    matches prior to the current position.  ``PrecededBy`` always
    returns a null token list, but if a results name is defined on the
    given expression, it is returned.

    Parameters:

     - expr - expression that must match prior to the current parse
       location
     - retreat - (default= ``None``) - (int) maximum number of characters
       to lookbehind prior to the current parse location

    If the lookbehind expression is a string, Literal, Keyword, or
    a Word or CharsNotIn with a specified exact or maximum length, then
    the retreat parameter is not required. Otherwise, retreat must be
    specified to give a maximum number of characters to look back from
    the current parse position for a lookbehind match.

    Example::

        # VB-style variable names with type prefixes
        int_var = PrecededBy("#") + identifier
        str_var = PrecededBy("$") + identifier

    """

    def __init__(self, expr, retreat=None):
        super(PrecededBy, self).__init__(expr)
        self.expr = self.expr().leaveWhitespace()
        self.parser_config.mayReturnEmpty = True
        self.parser_config.mayIndexError = False
        self.exact = False
        if isinstance(expr, str):
            retreat = len(expr)
            self.exact = True
        elif isinstance(expr, (Literal, Keyword)):
            retreat = expr.matchLen
            self.exact = True
        elif isinstance(expr, (Word, CharsNotIn)) and expr.maxLen != _MAX_INT:
            retreat = expr.maxLen
            self.exact = True
        elif isinstance(expr, _PositionToken):
            retreat = 0
            self.exact = True
        self.retreat = retreat
        self.parser_config.skipWhitespace = False

    def parseImpl(self, instring, loc=0, doActions=True):
        if self.exact:
            if loc < self.retreat:
                raise ParseException(instring, loc, self)
            start = loc - self.retreat
            _, ret = self.expr._parse(instring, start)
        else:
            # retreat specified a maximum lookbehind window, iterate
            test_expr = self.expr + StringEnd()
            instring_slice = instring[:loc]
            last_expr = ParseException(instring, loc, self)
            for offset in range(1, min(loc, self.retreat + 1)):
                try:
                    _, ret = test_expr._parse(instring_slice, loc - offset)
                except ParseBaseException as pbe:
                    last_expr = pbe
                else:
                    break
            else:
                raise last_expr
        # return empty list of tokens, but preserve any defined results names

        ret.__class__ = Annotation
        return loc, ParseResults(self, [ret])


# export
from mo_parsing import core, engine

core.SkipTo = SkipTo
core.ZeroOrMore = ZeroOrMore
core.OneOrMore = OneOrMore
core.Optional = Optional
core.NotAny = NotAny
core.Suppress = Suppress
core.Group = Group

from mo_parsing import results

results.Forward = Forward
results.Group = Group
results.Dict = Dict
results.Suppress = Suppress