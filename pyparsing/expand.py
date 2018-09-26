from __builtin__ import reduce

from pyparsing import Forward, opAssoc, FollowedBy, Group, OneOrMore, Optional, Suppress, ZeroOrMore, ParserElement


def infixNotation( baseExpr, opList, lpar=Suppress('('), rpar=Suppress(')') ):
    """
    Helper method for constructing grammars of expressions made up of
    operators working in a precedence hierarchy.  Operators may be unary or
    binary, left- or right-associative.  Parse actions can also be attached
    to operator expressions. The generated parser will also recognize the use
    of parentheses to override operator precedences (see example below).

    Note: if you define a deep operator list, you may see performance issues
    when using infixNotation. See L{ParserElement.enablePackrat} for a
    mechanism to potentially improve your parser performance.

    Parameters:
     - baseExpr - expression representing the most basic element for the nested
     - opList - list of tuples, one for each operator precedence level in the
      expression grammar; each tuple is of the form
      (opExpr, numTerms, rightLeftAssoc, parseAction), where:
       - opExpr is the pyparsing expression for the operator;
          may also be a string, which will be converted to a Literal;
          if numTerms is 3, opExpr is a tuple of two expressions, for the
          two operators separating the 3 terms
       - numTerms is the number of terms for this operator (must
          be 1, 2, or 3)
       - rightLeftAssoc is the indicator whether the operator is
          right or left associative, using the pyparsing-defined
          constants C{opAssoc.RIGHT} and C{opAssoc.LEFT}.
       - parseAction is the parse action to be associated with
          expressions matching this operator expression (the
          parse action tuple member may be omitted); if the parse action
          is passed a tuple or list of functions, this is equivalent to
          calling C{setParseAction(*fn)} (L{ParserElement.setParseAction})
     - lpar - expression for matching left-parentheses (default=C{Suppress('(')})
     - rpar - expression for matching right-parentheses (default=C{Suppress(')')})

    Example::
        # simple example of four-function arithmetic with ints and variable names
        integer = pyparsing_common.signed_integer
        varname = pyparsing_common.identifier

        arith_expr = infixNotation(integer | varname,
            [
            ('-', 1, opAssoc.RIGHT),
            (oneOf('* /'), 2, opAssoc.LEFT),
            (oneOf('+ -'), 2, opAssoc.LEFT),
            ])

        arith_expr.runTests('''
            5+3*6
            (5+3)*6
            -2--11
            ''', fullDump=False)
    prints::
        5+3*6
        [[5, '+', [3, '*', 6]]]

        (5+3)*6
        [[[5, '+', 3], '*', 6]]

        -2--11
        [[['-', 2], '-', ['-', 11]]]
    """

    # COLLECT THE OPS
    ops = [op for op, num, assoc, action in opList if num>1]

    # CONSTRUCT ALTERNATING MATCHER
    sequence = baseExpr + ZeroOrMore(reduce(ParserElement.__or__, ops) + baseExpr)



    ret = Forward()
    lastExpr = baseExpr | ( lpar + ret + rpar )
    for i,operDef in enumerate(opList):
        opExpr,arity,rightLeftAssoc,pa = (operDef + (None,))[:4]
        termName = "%s term" % opExpr if arity < 3 else "%s%s term" % opExpr
        if arity == 3:
            if opExpr is None or len(opExpr) != 2:
                raise ValueError("if numterms=3, opExpr must be a tuple or list of two expressions")
            opExpr1, opExpr2 = opExpr
        thisExpr = Forward().setName(termName)
        if rightLeftAssoc == opAssoc.LEFT:
            if arity == 1:
                matchExpr = FollowedBy(lastExpr + opExpr) + Group( lastExpr + OneOrMore( opExpr ) )
            elif arity == 2:
                if opExpr is not None:
                    matchExpr = FollowedBy(lastExpr + opExpr + lastExpr) + Group( lastExpr + OneOrMore( opExpr + lastExpr ) )
                else:
                    matchExpr = FollowedBy(lastExpr+lastExpr) + Group( lastExpr + OneOrMore(lastExpr) )
            elif arity == 3:
                matchExpr = FollowedBy(lastExpr + opExpr1 + lastExpr + opExpr2 + lastExpr) + \
                            Group( lastExpr + opExpr1 + lastExpr + opExpr2 + lastExpr )
            else:
                raise ValueError("operator must be unary (1), binary (2), or ternary (3)")
        elif rightLeftAssoc == opAssoc.RIGHT:
            if arity == 1:
                # try to avoid LR with this extra test
                if not isinstance(opExpr, Optional):
                    opExpr = Optional(opExpr)
                matchExpr = FollowedBy(opExpr.expr + thisExpr) + Group( opExpr + thisExpr )
            elif arity == 2:
                if opExpr is not None:
                    matchExpr = FollowedBy(lastExpr + opExpr + thisExpr) + Group( lastExpr + OneOrMore( opExpr + thisExpr ) )
                else:
                    matchExpr = FollowedBy(lastExpr + thisExpr) + Group( lastExpr + OneOrMore( thisExpr ) )
            elif arity == 3:
                matchExpr = FollowedBy(lastExpr + opExpr1 + thisExpr + opExpr2 + thisExpr) + \
                            Group( lastExpr + opExpr1 + thisExpr + opExpr2 + thisExpr )
            else:
                raise ValueError("operator must be unary (1), binary (2), or ternary (3)")
        else:
            raise ValueError("operator must indicate right or left associativity")
        if pa:
            if isinstance(pa, (tuple, list)):
                matchExpr.setParseAction(*pa)
            else:
                matchExpr.setParseAction(pa)
        thisExpr <<= ( matchExpr.setName(termName) | lastExpr )
        lastExpr = thisExpr
    ret <<= lastExpr
    return ret

operatorPrecedence = infixNotation
"""(Deprecated) Former name of C{L{infixNotation}}, will be dropped in a future release."""
