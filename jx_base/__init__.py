# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

from uuid import uuid4

from jx_base.expressions import jx_expression
from jx_base.models.facts import Facts
from jx_base.models.namespace import Namespace
from jx_base.models.snowflake import Snowflake
from jx_base.models.table import Table
from jx_base.models.container import Container
from jx_base.models.relation import Relation
from jx_python.expressions import Literal
from mo_dots import coalesce, listwrap, to_data
from mo_dots.datas import register_data
from mo_dots.lists import last
from mo_future import is_text, text
from mo_imports import export
from mo_json import (
    value2json,
    true,
    false,
    null,
    EXISTS,
    OBJECT,
    ARRAY,
)
from mo_json.typed_encoder import EXISTS_KEY
from mo_logs import Log
from mo_logs.strings import expand_template, quote


ENABLE_CONSTRAINTS = True


def generateGuid():
    """
    Gets a random GUID.
    Note: python's UUID generation library is used here.
    Basically UUID is the same as GUID when represented as a string.
    :Returns:
        str, the generated random GUID.

    a=GenerateGuid()
    import uuid
    print(a)
    print(uuid.UUID(a).hex)
    """
    return text(uuid4())


def _exec(code, name):
    try:
        globs = globals()
        fake_locals = {}
        exec(code, globs, fake_locals)
        temp = fake_locals[name]
        return temp
    except Exception as cause:
        Log.error("Can not make class\n{{code}}", code=code, cause=cause)


_ = listwrap, last, true, false, null


def failure(row, rownum, rows, constraint):
    constraint = to_data(constraint)
    if constraint['and']:
        for a in constraint['and']:
            failure(row, rownum, rows, a)
        return
    expr = jx_expression(constraint)

    try:
        if not expr(row, rownum, row):
            raise Log.error("{{row}} fails to pass {{req}}", row=row, req=expr.__data__())
    except Exception as cause:
        raise Log.error("{{row}} fails to pass {{req}}", row=row, req=expr.__data__(), cause=cause)


def DataClass(name, columns, constraint=None):
    """
    Use the DataClass to define a class, but with some extra features:
    1. restrict the data type of property
    2. restrict if `required`, or if `nulls` are allowed
    3. generic constraints on object properties

    It is expected that this class become a real class (or be removed) in the
    long term because it is expensive to use and should only be good for
    verifying program correctness, not user input.

    :param name: Name of the class we are creating
    :param columns: Each columns[i] has properties {
            "name",     - (required) name of the property
            "required", - False if it must be defined (even if None)
            "nulls",    - True if property can be None, or missing
            "default",  - A default value, if none is provided
            "type"      - a Python data type
        }
    :param constraint: a JSON query Expression for extra constraints (return true if all constraints are met)
    :return: The class that has been created
    """

    columns = to_data([
        {"name": c, "required": True, "nulls": False, "type": object}
        if is_text(c)
        else c
        for c in columns
    ])
    constraint = {
        "and": [
            {"exists": c.name} for c in columns if not c.nulls and c.default == None
        ]
        + [constraint]
    }
    slots = columns.name
    required = to_data(filter(lambda c: c.required and c.default == None, columns)).name
    # nulls = to_data(filter(lambda c: c.nulls, columns)).name
    defaults = {c.name: coalesce(c.default, None) for c in columns}
    types = {c.name: coalesce(c.type, object) for c in columns}

    code = expand_template(
        """
from __future__ import unicode_literals
from mo_future import is_text, is_binary, Mapping
from mo_dots import Null
from jx_base import failure

meta = None
types_ = {{types}}
defaults_ = {{defaults}}

class {{class_name}}(Mapping):
    __slots__ = {{slots}}


    def _constraint(row, rownum, rows):
        code = {{constraint_expr|quote}}
        if {{constraint_expr}}:
            return
        failure(row, rownum, rows, {{constraint}})
        Log.error(
            "constraint\\n{" + "{code}}\\nnot satisfied {" + "{expect}}\\n{" + "{value|indent}}",
            code={{constraint_expr|quote}},
            expect={{constraint}},
            value=row
        )

    def __init__(self, **kwargs):
        if not kwargs:
            return

        for s in {{slots}}:
            object.__setattr__(self, s, kwargs.get(s, {{defaults}}.get(s, None)))

        missed = {{required}}-set(kwargs.keys())
        if missed:
            Log.error("Expecting properties {"+"{missed}}", missed=missed)

        illegal = set(kwargs.keys())-set({{slots}})
        if illegal:
            Log.error("{"+"{names}} are not a valid properties", names=illegal)

        self._constraint(0, [self])

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)
        return self

    def __setattr__(self, item, value):
        if item not in {{slots}}:
            Log.error("{"+"{item|quote}} not valid attribute", item=item)

        if value==None and item in {{required}}:
            Log.error("Expecting property {"+"{item}}", item=item)

        object.__setattr__(self, item, value)
        self._constraint(0, [self])

    def __getattr__(self, item):
        Log.error("{"+"{item|quote}} not valid attribute", item=item)

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        try:
            if isinstance(other, {{class_name}}) and dict(self)==dict(other) and self is not other:
                Log.error("expecting to be same object")
            return self is other
        except Exception:
            return False
            
    def __dict__(self):
        return {k: getattr(self, k) for k in {{slots}}}

    def items(self):
        return ((k, getattr(self, k)) for k in {{slots}})

    def __copy__(self):
        _set = object.__setattr__
        output = object.__new__({{class_name}})
        {{assign}}
        return output

    def __iter__(self):
        return {{slots}}.__iter__()

    def __len__(self):
        return {{len_slots}}

    def __str__(self):
        return str({{dict}})

""",
        {
            "class_name": name,
            "slots": "(" + ", ".join(quote(s) for s in slots) + ")",
            "required": "{" + ", ".join(quote(s) for s in required) + "}",
            "defaults": Literal(defaults).to_python(),
            "len_slots": len(slots),
            "dict": "{" + ", ".join(quote(s) + ": self." + s for s in slots) + "}",
            "assign": "; ".join(
                "_set(output, " + quote(s) + ", self." + s + ")" for s in slots
            ),
            "types": "{"
            + ",".join(quote(k) + ": " + v.__name__ for k, v in types.items())
            + "}",
            "constraint_expr": jx_expression(
                not ENABLE_CONSTRAINTS or constraint
            ).to_python(),
            "constraint": value2json(constraint),
        },
    )

    output = _exec(code, name)
    register_data(output)
    return output


TableDesc = DataClass(
    "Table",
    [
        "name",
        {"name": "url", "nulls": true},
        "query_path",
        {"name": "last_updated", "nulls": False},
        "columns",
    ],
    constraint={"and": [{"ne": [{"last": "query_path"}, {"literal": "."}]}]},
)


from jx_base.models.container import Container

Column = DataClass(
    "Column",
    [
        "name",
        "es_column",
        "es_index",
        "es_type",
        "json_type",
        "nested_path",  # AN ARRAY OF PATHS (FROM DEEPEST TO SHALLOWEST) INDICATING THE JSON SUB-ARRAYS
        {"name": "count", "nulls": True},
        {"name": "cardinality", "nulls": True},
        {"name": "multi", "nulls": False},
        {"name": "partitions", "nulls": True},
        "last_updated",
    ],
    constraint={"and": [
        {
            "when": {"ne": {"name": "."}},
            "then": {"or": [
                {"and": [{"eq": {"json_type": "object"}}, {"eq": {"multi": 1}}]},
                {"ne": ["name", {"first": "nested_path"}]},
            ]},
            "else": True,
        },
        {
            "when": {"eq": {"es_column": "."}},
            "then": {"in": {"json_type": ["nested", "object"]}},
            "else": True,
        },
        {"not": {"find": {"es_column": "null"}}},
        {"not": {"eq": {"es_column": "string"}}},
        {"not": {"eq": {"es_type": "object", "json_type": "exists"}}},
        {
            "when": {"suffix": {"es_column": "." + EXISTS_KEY}},
            "then": {"eq": {"json_type": EXISTS}},
            "else": True,
        },
        {
            "when": {"suffix": {"es_column": "." + EXISTS_KEY}},
            "then": {"exists": "cardinality"},
            "else": True,
        },
        {
            "when": {"eq": {"json_type": OBJECT}},
            "then": {"in": {"cardinality": [0, 1]}},
            "else": True,
        },
        {
            "when": {"eq": {"json_type": ARRAY}},
            "then": {"in": {"cardinality": [0, 1]}},
            "else": True,
        },
        {"not": {"prefix": [{"first": "nested_path"}, {"literal": "testdata"}]}},
        {"ne": [{"last": "nested_path"}, {"literal": "."}]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
        {
            "when": {"eq": [{"literal": ".~N~"}, {"right": {"es_column": 4}}]},
            "then": {"or": [
                {"and": [
                    {"gt": {"multi": 1}},
                    {"eq": {"json_type": "nested"}},
                    {"eq": {"es_type": "nested"}},
                ]},
                {"and": [
                    {"eq": {"multi": 1}},
                    {"eq": {"json_type": "object"}},
                    {"eq": {"es_type": "object"}},
                ]},
            ]},
            "else": True,
        },
        {
            "when": {"gte": [{"count": "nested_path"}, 2]},
            "then": {"ne": [
                {"first": {"right": {"nested_path": 2}}},
                {"literal": "."},
            ]},  # SECOND-LAST ELEMENT
            "else": True,
        },
    ]},
)

export("jx_base.expressions.query_op", Column)
