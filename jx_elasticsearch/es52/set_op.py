# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

from collections import OrderedDict
from copy import copy

from jx_base.domains import ALGEBRAIC
from jx_base.expressions import LeavesOp, Variable, TRUE, NULL
from jx_base.expressions.query_op import DEFAULT_LIMIT
from jx_base.language import is_op
from jx_elasticsearch.es52.expressions import (
    split_expression_by_path,
    NestedOp,
    ESSelectOp,
)
from jx_elasticsearch.es52.expressions.utils import setop_to_es_queries, pre_process, ES52
from jx_elasticsearch.es52.painless import Painless
from jx_elasticsearch.es52.set_format import set_formatters
from jx_elasticsearch.es52.util import jx_sort_to_es_sort
from jx_python.expressions import jx_expression_to_function
from mo_dots import (
    Data,
    FlatList,
    coalesce,
    concat_field,
    join_field,
    listwrap,
    literal_field,
    relative_field,
    split_field,
    unwrap,
    Null,
    list_to_data,
    unwraplist, )
from mo_future import text, flatten
from mo_json import NESTED, INTERNAL, OBJECT, EXISTS, PRIMITIVE
from mo_json.typed_encoder import untype_path, untyped
from mo_logs import Log
from mo_math import AND
from mo_times.timer import Timer

DEBUG = False


def is_setop(es, query):
    select = listwrap(query.select)

    if not query.edges:
        isDeep = len(split_field(query.frum.name)) > 1  # LOOKING INTO NESTED WILL REQUIRE A SCRIPT
        simpleAgg = AND([
            s.aggregate in ("count", "none") for s in select
        ])  # CONVERTING esfilter DEFINED PARTS WILL REQUIRE SCRIPT

        # NO EDGES IMPLIES SIMPLER QUERIES: EITHER A SET OPERATION, OR RETURN SINGLE AGGREGATE
        if simpleAgg or isDeep:
            return True
    else:
        isSmooth = AND(
            (e.domain.type in ALGEBRAIC and e.domain.interval == "none")
            for e in query.edges
        )
        if isSmooth:
            return True

    return False


def get_selects(query):
    schema = query.frum.schema
    query_path = schema.query_path
    query_table = query_path[0]
    query_level = len(query_path)
    # SPLIT select INTO ES_SELECT AND RESULTSET SELECT
    split_select = OrderedDict((p, ESSelectOp(p)) for p in query_path)

    def expand_split_select(c_nested_path):
        es_select = split_select.get(c_nested_path)
        if not es_select:
            temp = [(k, v) for k, v in split_select.items()]
            split_select.clear()
            split_select.update({c_nested_path: ESSelectOp(c_nested_path)})
            split_select.update(temp)
        return split_select[c_nested_path]

    new_select = FlatList()
    post_expressions = {}

    selects = list_to_data([unwrap(s.copy()) for s in listwrap(query.select)])

    # WHAT PATH IS _source USED, IF ANY?
    for select in selects:
        # IF THERE IS A *, THEN INSERT THE EXTRA COLUMNS
        if is_op(select.value, LeavesOp) and is_op(select.value.term, Variable):
            term = select.value.term
            if term.var == ".":  # TODO: REMOVE THIS CHECK
                # PLAIN * MEANS EVERYTHING
                split_select["."].source_path = "."
            else:
                split_variable = schema.split_values(term.var, exclude_type=PRIMITIVE)
                for nesting, c in split_variable.items():
                    if c.es_column == c.nested_path[0]:
                        split_select[c.es_column].source_path = c.es_column

        elif is_op(select.value, Variable):
            for leaf in set(schema.split_values(select.value.var).values()):
                if leaf.es_column in query_path:
                    expand_split_select(leaf.es_column).source_path = leaf.es_column
                    continue
                leaves = schema.split_leaves(leaf)
                for leaf in leaves:
                    if leaf.jx_type == NESTED:
                        expand_split_select(leaf.es_column).source_path = leaf.es_column

    # IF WE GET THE SOURCE FOR PARENT, WE ASSUME WE GOT SOURCE FOR CHILD
    source_path = None
    source_level = 0
    for level, es_select in enumerate(reversed(list(split_select.values()))):
        if source_path:
            es_select.source_path = source_path
        elif es_select.source_path:
            source_level = level + 1
            source_path = es_select.source_path

    def get_pull_source(c):
        nested_path = c.nested_path
        nested_level = len(nested_path)
        pos = text(nested_level)

        if nested_level <= query_level:
            if not source_level or nested_level < source_level:
                field = join_field([pos, "fields", c.es_column])
                return jx_expression_to_function(field)
            elif nested_level == source_level:
                field = relative_field(c.es_column, nested_path[0])

                def pull_source(row):
                    return untyped(row.get(pos, Null)._source[field])

                return pull_source
            else:
                pos = text(query_level)
                field = relative_field(c.es_column, nested_path[0])

                def pull_property(row):
                    return untyped(row.get(pos, Null)[field])

                return pull_property
        else:
            # SELECTING DEEPER NESTED ARRAYS MEANS SOME AGGREGATION
            pos = text(query_level)

            if not source_level or nested_level < source_level:
                # PULL FIELDS AND THEN AGGREGATE THEM
                value = jx_expression_to_function(join_field(["fields", c.es_column]))
                name = literal_field(nested_path[0])
                index = jx_expression_to_function("_nested.offset")

                def pull_nested_field(doc):
                    hits = doc.get(pos, Null).inner_hits[name].hits.hits
                    if not hits:
                        return []

                    temp = [(index(h), value(h)) for h in hits]
                    acc = [None] * len(temp)
                    for i, v in temp:
                        acc[i] = unwraplist(v)
                    return acc

                return pull_nested_field
            else:
                # PULL SOURCES
                value = jx_expression_to_function(concat_field(
                    "_source", relative_field(c.es_column, nested_path[0])
                ))
                name = literal_field(nested_path[0])
                index = jx_expression_to_function(join_field(
                    ["_nested"] * (len(c.nested_path) - 1) + ["offset"]
                ))

                def pull_nested_source(doc):
                    hits = doc.get(pos, Null).inner_hits[name].hits.hits
                    if not hits:
                        return []

                    temp = [(index(h), value(h)) for h in hits]
                    acc = [None] * len(temp)
                    for i, v in temp:
                        acc[i] = untyped(v)
                    return acc

                return pull_nested_source

    used_names = set()
    for select in selects:
        # IF THERE IS A *, THEN INSERT THE EXTRA COLUMNS
        if is_op(select.value, LeavesOp) and is_op(select.value.term, Variable):
            term = select.value.term
            if term.var == ".":
                # PLAIN * MEANS EVERYTHING
                for leaf in schema.columns:
                    if leaf.jx_type in (OBJECT, EXISTS):
                        continue
                    if leaf.name == "_id":
                        continue
                    if leaf.name == ".":
                        # THE NESTED VERSION OF "." IS IRREGULAR
                        continue
                    nested_level = len(leaf.nested_path)
                    if nested_level > query_level:
                        continue
                    if nested_level == query_level and leaf.name != ".":
                        rel_name = untype_path(relative_field(leaf.name, query_table))
                        name = concat_field(select.name, untype_path(rel_name))
                        put_name = concat_field(select.name, literal_field(untype_path(rel_name)))

                        used_names.add(put_name)
                        new_select.append({
                            "name": name,
                            "value": Variable(leaf.es_column),
                            "put": {"name": put_name, "index": len(used_names)-1, "child": "."},
                            "pull": get_pull_source(leaf),
                        })
                    elif nested_level < query_level and leaf.jx_type != NESTED:
                        rel_name = untype_path(relative_field(leaf.name, leaf.nested_path[0]))
                        name = concat_field(select.name, untype_path(rel_name))
                        put_name = concat_field(select.name, literal_field(untype_path(rel_name)))

                        used_names.add(put_name)
                        new_select.append({
                            "name": name,
                            "value": Variable(leaf.es_column),
                            "put": {"name": put_name, "index": len(used_names)-1, "child": "."},
                            "pull": get_pull_source(leaf),
                        })
                continue

            split_variable = schema.split_values(term.var, exclude_type=PRIMITIVE)
            for nesting, selected_column in split_variable.items():
                leaves = schema.split_leaves(
                    selected_column, exclude_type=(OBJECT, EXISTS)
                )
                for leaf in leaves:
                    if leaf.jx_type == NESTED and leaf.es_column in query_path:
                        continue
                    rel_name = relative_field(
                        leaf.es_column, selected_column.es_column,
                    )
                    if rel_name != '.':
                        rel_name = rel_name.lstrip(".")
                    name = concat_field(select.name, untype_path(rel_name))
                    put_name = concat_field(select.name, literal_field(untype_path(rel_name)))
                    split_select[leaf.nested_path[0]].fields.append(leaf.es_column)
                    used_names.add(put_name)
                    new_select.append({
                        "name": name,
                        "value": Variable(leaf.es_column),
                        "put": {"name": put_name, "index": len(used_names)-1, "child": "."},
                        "pull": get_pull_source(leaf),
                    })
        elif is_op(select.value, Variable):
            if select.value.var == ".":
                # PULL ALL SOURCE
                used_names.add(select.name)
                new_select.append({
                    "name": select.name,
                    "value": select.value,
                    "put": {"name": select.name, "index": len(used_names)-1, "child": "."},
                    "pull": get_pull_source(Data(
                        es_column=query_table, nested_path=query_path
                    )),
                })
                continue

            split_variable = schema.split_values(select.value.var)
            if not split_variable:
                # CAN NOT FIND
                used_names.add(select.name)
                new_select.append({
                    "name": select.name,
                    "value": NULL,
                    "put": {"name": select.name, "index": len(used_names)-1, "child": "."},
                    "pull": NULL,
                })

            for nesting, selected_column in split_variable.items():
                leaves = schema.split_leaves(selected_column)
                if not leaves:
                    used_names.add(select.name)
                    new_select.append({
                        "name": select.name,
                        "value": NULL,
                        "put": {"name": select.name, "index": len(used_names)-1, "child": "."},
                        "pull": NULL,
                    })
                    continue
                for leaf in leaves:
                    if leaf.es_column in query_path:
                        continue  # ALREADY CONSIDERED
                    if leaf.jx_type == NESTED:
                        used_names.add(select.name)
                        new_select.append({
                            "name": select.name,
                            "value": select.value,
                            "put": {
                                "name": select.name,
                                "index": len(used_names)-1,
                                "child": ".",
                            },
                            "pull": get_pull_source(Data(
                                es_column=leaf.es_column,
                                nested_path=(leaf.es_column,) + tuple(leaf.nested_path),
                            )),
                        })
                    elif leaf.es_column == "_id":
                        used_names.add(select.name)
                        new_select.append({
                            "name": select.name,
                            "value": Variable(leaf.es_column),
                            "put": {
                                "name": select.name,
                                "index": len(used_names)-1,
                                "child": ".",
                            },
                            "pull": pull_id,
                        })
                    else:
                        expand_split_select(nesting).fields.append(leaf.es_column)
                        child = untype_path(relative_field(leaf.es_column, selected_column.es_column))

                        used_names.add(select.name)
                        new_select.append({
                            "name": select.name,
                            "value": Variable(leaf.es_column),
                            "put": {
                                "name": select.name,
                                "index": len(used_names)-1,
                                "child": child,
                            },
                            "pull": get_pull_source(leaf),
                        })
        else:
            op, split_scripts = split_expression_by_path(
                select.value, schema, lang=Painless
            )
            for pos, (p, scripts) in enumerate(reversed(list(split_scripts.items()))):
                for script in scripts:
                    es_script = script.partial_eval(Painless).to_es_script(schema)
                    es_select = split_select[p]
                    es_select.scripts[select.name] = {"script": text(es_script)}

                    used_names.add(select.name)
                    new_select.append({
                        "name": select.name,
                        "pull": pull_script(text(pos + 1), select.name),
                        "put": {"name": select.name, "index": len(used_names)-1, "child": "."},
                    })

    def inners(query_path, parent_pos):
        """
        :param query_path:
        :return:  ITERATOR OVER TUPLES ROWS AS TUPLES, WHERE  row[len(nested_path)] HAS INNER HITS
                  AND row[0] HAS post_expressions
        """
        pos = text(int(parent_pos) + 1)
        if not query_path:

            def base_case(row):
                extra = {}
                for k, e in post_expressions.items():
                    extra[k] = e(row)
                row["0"] = extra
                yield row

            return base_case

        if pos == "1":
            more = inners(query_path[:-1], "1")

            def first_case(results):
                for result in results:
                    for hit in result.hits.hits:
                        seed = {"0": None, pos: hit}
                        for row in more(seed):
                            yield row

            return first_case

        else:
            more = inners(query_path[:-1], pos)
            if source_path and source_path < query_path[-1]:
                rel_path = relative_field(query_path[-1], source_path)
                lit_rel_path = literal_field(rel_path)

                def source(acc):
                    hits = acc[parent_pos]._source[rel_path]
                    inner_hits = acc[parent_pos].inner_hits[lit_rel_path].hits.hits
                    if inner_hits:
                        # inner_hits WILL GUIDE MATCHES INTO THE SOURCE
                        for meta in inner_hits:
                            nested = meta._nested
                            # ASSUME nested.field == rel_path
                            inner_row = hits[nested.offset]
                            acc[pos] = inner_row
                            for tt in more(acc):
                                yield tt
                    elif hits:
                        for inner_row in hits:
                            acc[pos] = inner_row
                            for tt in more(acc):
                                yield tt
                    else:
                        for tt in more(acc):
                            yield tt

                return source
            else:
                path = literal_field(query_path[-1])

                def recurse(acc):
                    inner_hits = acc[parent_pos].inner_hits[path].hits.hits
                    if inner_hits:
                        for inner_row in inner_hits:
                            acc[pos] = inner_row
                            for tt in more(acc):
                                yield tt
                    else:
                        for tt in more(acc):
                            yield tt

                return recurse

    return new_select, split_select, inners(query_path, "0")


def es_setop(es, query):
    schema = query.frum.schema
    all_paths, split_decoders, var_to_columns = pre_process(query)
    new_select, split_select, flatten = get_selects(query)
    # THE SELECTS MAY BE REACHING DEEPER INTO THE NESTED RECORDS
    all_paths = list(reversed(sorted(set(split_select.keys()) | set(all_paths))))
    es_query = setop_to_es_queries(query, all_paths, split_select, var_to_columns)
    if not es_query:
        # NO QUERY TO SEND
        formatter, _, mime_type = set_formatters[query.format]
        output = formatter([], new_select, query)
        output.meta.content_type = mime_type
        output.meta.es_query = es_query
        return output

    size = coalesce(query.limit, DEFAULT_LIMIT)
    sort = jx_sort_to_es_sort(query.sort, schema)
    for q in es_query:
        q["size"] = size
        q["sort"] = sort

    with Timer("call to ES", verbose=DEBUG) as call_timer:
        results = es.multisearch(es_query)

    T = [copy(row) for row in flatten(results)]
    try:
        formatter, _, mime_type = set_formatters[query.format]

        with Timer("formatter", silent=True):
            output = formatter(T, new_select, query)
        output.meta.timing.es = call_timer.duration
        output.meta.content_type = mime_type
        output.meta.es_query = es_query
        return output
    except Exception as e:
        Log.error("problem formatting", e)


def pull_id(row):
    return row["1"]._id


def get_pull(column):
    if column.nested_path[0] == ".":
        return concat_field("fields", literal_field(column.es_column))
    else:
        rel_name = relative_field(column.es_column, column.nested_path[0])
        return concat_field("_inner", rel_name)


def get_pull_function(column):
    func = jx_expression_to_function(get_pull(column))
    if column.jx_type in INTERNAL:
        return lambda doc: untyped(func(doc))
    else:
        return func


def pull_script(pos, name):
    return jx_expression_to_function(join_field([pos, "fields", name]))


def get_pull_stats():
    return jx_expression_to_function({"select": [
        {"name": "count", "value": "count"},
        {"name": "sum", "value": "sum"},
        {"name": "min", "value": "min"},
        {"name": "max", "value": "max"},
        {"name": "avg", "value": "avg"},
        {"name": "sos", "value": "sum_of_squares"},
        {"name": "std", "value": "std_deviation"},
        {"name": "var", "value": "variance"},
    ]})


def es_query_proto(selects, op, wheres, schema):
    """
    RETURN AN ES QUERY
    :param selects: MAP FROM path TO ESSelect INSTANCE
    :param wheres: MAP FROM path TO LIST OF WHERE CONDITIONS
    :return: es_query
    """
    es_query = op.zero
    for p in reversed(sorted(set(wheres.keys()) | set(selects.keys()))):
        # DEEPEST TO SHALLOW
        where = wheres.get(p, TRUE)
        select = selects.get(p, Null)

        es_where = op([es_query, where])
        es_query = NestedOp(path=Variable(p), select=select, where=es_where)
    return es_query.partial_eval(ES52).to_es(schema)
