# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from datetime import date, datetime, timedelta
from decimal import Decimal

from mo_dots import (
    CLASS,
    Data,
    DataObject,
    FlatList,
    NullType,
    SLOT,
    _get,
    is_data,
    join_field,
    split_field,
    concat_field,
)
from mo_logs import Log
from mo_logs.strings import quote
from mo_times import Date, Duration

from mo_future import (
    binary_type,
    generator_types,
    integer_types,
    is_binary,
    is_text,
    sort_using_key,
    text,
)
from mo_json import (
    BOOLEAN,
    ESCAPE_DCT,
    EXISTS,
    INTEGER,
    ARRAY,
    NUMBER,
    STRING,
    float2json,
    datetime2unix,
    python_type_to_jx_type,
    quote,
    python_type_to_jx_type_key,
)
from mo_json.encoder import (
    COLON,
    COMMA,
    UnicodeBuilder,
    json_encoder,
    problem_serializing,
)
from mo_json.typed_object import TypedObject
from mo_json.types import BOOLEAN_KEY, NUMBER_KEY, INTEGER_KEY, STRING_KEY, ARRAY_KEY, EXISTS_KEY, IS_TYPE_KEY


def encode_property(name):
    return name.replace(",", "\\,").replace(".", ",")


def decode_property(encoded):
    return encoded.replace("\\,", "\a").replace(",", ".").replace("\a", ",")


def untype_path(encoded):
    if encoded.startswith(".."):
        remainder = encoded.lstrip(".")
        back = len(encoded) - len(remainder) - 1
        return ("." * back) + join_field(
            decode_property(c) for c in split_field(remainder) if not IS_TYPE_KEY.match(c)
        )
    else:
        return join_field(decode_property(c) for c in split_field(encoded) if not IS_TYPE_KEY.match(c))


def unnest_path(encoded):
    if encoded.startswith(".."):
        remainder = encoded.lstrip(".")
        back = len(encoded) - len(remainder)
        return ("." * back) + unnest_path(remainder)

    path = split_field(encoded)
    if not path:
        return "."
    if path[-1] == ARRAY_KEY:
        path = path[:-1]
        if not path:
            return "."

    return join_field(
        [decode_property(c) for c in path[:-1] if not IS_TYPE_KEY.match(c)] + [decode_property(path[-1])]
    )


def get_nested_path(typed_path):
    # CONSTRUCT THE nested_path FROM THE typed_path
    path = split_field(typed_path)
    parent = "."
    nested_path = (parent,)
    for i, p in enumerate(path[:-1]):
        if p == ARRAY_KEY:
            step = concat_field(parent, join_field(path[0: i + 1]))
            nested_path = (step,) + nested_path
    return nested_path


def detype(value):
    return _detype_value(value)


def _detype_list(value):
    if any(is_data(v) for v in value):
        # MAY BE MORE TYPED OBJECTS IN THIS LIST
        return [_detype_value(v) for v in value]
    else:
        # LIST OF PRIMITIVE VALUES
        return value


def _detype_dict(value):
    output = {}

    for k, v in value.items():
        if IS_TYPE_KEY.match(k):
            if k == EXISTS_KEY:
                continue
            elif k == ARRAY_KEY:
                return _detype_list(v)
            else:
                return v
        else:
            new_v = _detype_value(v)
            if new_v is not None:
                output[decode_property(k)] = new_v
    return output


def _detype_value(value):
    _type = _get(value, CLASS)
    if _type is TypedObject:
        return value._boxed_value
    elif _type is Data:
        return _detype_dict(_get(value, SLOT))
    elif _type is dict:
        return _detype_dict(value)
    elif _type is FlatList:
        return _detype_list(value.list)
    elif _type is list:
        return _detype_list(value)
    elif _type is NullType:
        return None
    elif _type is DataObject:
        return _detype_value(_get(value, SLOT))
    elif _type in generator_types:
        return _detype_list(value)
    else:
        return value


def encode(value):
    buffer = UnicodeBuilder(1024)
    typed_encode(value, sub_schema={}, path=[], net_new_properties=[], buffer=buffer)
    return buffer.build()


def typed_encode(value, sub_schema, path, net_new_properties, buffer):
    """
    :param value: THE DATA STRUCTURE TO ENCODE
    :param sub_schema: dict FROM PATH TO Column DESCRIBING THE TYPE
    :param path: list OF CURRENT PATH
    :param net_new_properties: list FOR ADDING NEW PROPERTIES NOT FOUND IN sub_schema
    :param buffer: UnicodeBuilder OBJECT
    :return:
    """
    try:
        # from jx_base import Column
        if sub_schema.__class__.__name__ == "Column":
            value_json_type = python_type_to_jx_type[value.__class__]
            column_json_type = es_type_to_json_type[sub_schema.es_type]

            if value_json_type == column_json_type:
                pass  # ok
            elif value_json_type == ARRAY and all(
                    python_type_to_jx_type[v.__class__] == column_json_type for v in value if v != None
            ):
                pass  # empty arrays can be anything
            else:
                from mo_logs import Log

                Log.error(
                    "Can not store {{value}} in {{column|quote}}", value=value, column=sub_schema.name,
                )

            sub_schema = {json_type_to_inserter_type[value_json_type]: sub_schema}

        if value == None and path:
            from mo_logs import Log

            Log.error("can not encode null (missing) values")
        elif value is True:
            if BOOLEAN_KEY not in sub_schema:
                sub_schema[BOOLEAN_KEY] = {}
                net_new_properties.append(path + [BOOLEAN_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_BOOLEAN_KEY)
            append(buffer, "true}")
            return
        elif value is False:
            if BOOLEAN_KEY not in sub_schema:
                sub_schema[BOOLEAN_KEY] = {}
                net_new_properties.append(path + [BOOLEAN_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_BOOLEAN_KEY)
            append(buffer, "false}")
            return

        _type = value.__class__
        if _type in (dict, Data):
            if sub_schema.__class__.__name__ == "Column":
                from mo_logs import Log

                Log.error("Can not handle {{column|json}}", column=sub_schema)

            if ARRAY_KEY in sub_schema:
                # PREFER NESTED, WHEN SEEN BEFORE
                if value:
                    append(buffer, "{")
                    append(buffer, QUOTED_ARRAY_KEY)
                    append(buffer, "[")
                    _dict2json(
                        value, sub_schema[ARRAY_KEY], path + [ARRAY_KEY], net_new_properties, buffer,
                    )
                    append(buffer, "]" + COMMA)
                    append(buffer, QUOTED_EXISTS_KEY)
                    append(buffer, text(len(value)))
                    append(buffer, "}")
                else:
                    # SINGLETON LIST
                    append(buffer, "{")
                    append(buffer, QUOTED_ARRAY_KEY)
                    append(buffer, "[{")
                    append(buffer, QUOTED_EXISTS_KEY)
                    append(buffer, "1}]")
                    append(buffer, COMMA)
                    append(buffer, QUOTED_EXISTS_KEY)
                    append(buffer, "1}")
            else:
                if EXISTS_KEY not in sub_schema:
                    sub_schema[EXISTS_KEY] = {}
                    net_new_properties.append(path + [EXISTS_KEY])

                if value:
                    _dict2json(value, sub_schema, path, net_new_properties, buffer)
                else:
                    append(buffer, "{")
                    append(buffer, QUOTED_EXISTS_KEY)
                    append(buffer, "1}")
        elif _type is binary_type:
            if STRING_KEY not in sub_schema:
                sub_schema[STRING_KEY] = True
                net_new_properties.append(path + [STRING_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_STRING_KEY)
            append(buffer, '"')
            try:
                v = value.decode("utf8")
            except Exception as e:
                raise problem_serializing(value, e)

            for c in v:
                append(buffer, ESCAPE_DCT.get(c, c))
            append(buffer, '"}')
        elif _type is text:
            if STRING_KEY not in sub_schema:
                sub_schema[STRING_KEY] = True
                net_new_properties.append(path + [STRING_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_STRING_KEY)
            append(buffer, '"')
            for c in value:
                append(buffer, ESCAPE_DCT.get(c, c))
            append(buffer, '"}')
        elif _type in integer_types:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])

            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, text(value))
            append(buffer, "}")
        elif _type in (float, Decimal):
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(value))
            append(buffer, "}")
        elif _type in (set, list, tuple, FlatList):
            if len(value) == 0:
                append(buffer, "{")
                append(buffer, QUOTED_EXISTS_KEY)
                append(buffer, "0}")
            elif any(v.__class__ in (Data, dict, set, list, tuple, FlatList) for v in value):
                if len(value) == 1:
                    if ARRAY_KEY in sub_schema:
                        append(buffer, "{")
                        append(buffer, QUOTED_ARRAY_KEY)
                        _list2json(
                            value, sub_schema[ARRAY_KEY], path + [ARRAY_KEY], net_new_properties, buffer,
                        )
                        append(buffer, "}")
                    else:
                        # NO NEED TO NEST, SO DO NOT DO IT
                        typed_encode(value[0], sub_schema, path, net_new_properties, buffer)
                else:
                    if ARRAY_KEY not in sub_schema:
                        sub_schema[ARRAY_KEY] = {}
                        net_new_properties.append(path + [ARRAY_KEY])
                    append(buffer, "{")
                    append(buffer, QUOTED_ARRAY_KEY)
                    _list2json(
                        value, sub_schema[ARRAY_KEY], path + [ARRAY_KEY], net_new_properties, buffer,
                    )
                    append(buffer, "}")
            else:
                # ALLOW PRIMITIVE MULTIVALUES
                value = [v for v in value if v != None]
                types = list(set(python_type_to_jx_type_key[v.__class__] for v in value))
                if len(types) == 0:  # HANDLE LISTS WITH Nones IN THEM
                    append(buffer, "{")
                    append(buffer, QUOTED_ARRAY_KEY)
                    append(buffer, "[]}")
                elif len(types) > 1:
                    _list2json(
                        value, sub_schema, path + [ARRAY_KEY], net_new_properties, buffer,
                    )
                else:
                    element_type = types[0]
                    if element_type not in sub_schema:
                        sub_schema[element_type] = True
                        net_new_properties.append(path + [element_type])
                    append(buffer, "{")
                    append(buffer, quote(element_type))
                    append(buffer, COLON)
                    _multivalue2json(
                        value, sub_schema[element_type], path + [element_type], net_new_properties, buffer,
                    )
                    append(buffer, "}")
        elif _type is date:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(datetime2unix(value)))
            append(buffer, "}")
        elif _type is datetime:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(datetime2unix(value)))
            append(buffer, "}")
        elif _type is Date:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(value.unix))
            append(buffer, "}")
        elif _type is timedelta:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(value.total_seconds()))
            append(buffer, "}")
        elif _type is Duration:
            if NUMBER_KEY not in sub_schema:
                sub_schema[NUMBER_KEY] = True
                net_new_properties.append(path + [NUMBER_KEY])
            append(buffer, "{")
            append(buffer, QUOTED_NUMBER_KEY)
            append(buffer, float2json(value.seconds))
            append(buffer, "}")
        elif _type is NullType:
            append(buffer, "null")
        elif hasattr(value, "__data__"):
            typed_encode(value.__data__(), sub_schema, path, net_new_properties, buffer)
        elif hasattr(value, "__iter__"):
            if ARRAY_KEY not in sub_schema:
                sub_schema[ARRAY_KEY] = {}
                net_new_properties.append(path + [ARRAY_KEY])

            append(buffer, "{")
            append(buffer, QUOTED_ARRAY_KEY)
            _iter2json(
                value, sub_schema[ARRAY_KEY], path + [ARRAY_KEY], net_new_properties, buffer,
            )
            append(buffer, "}")
        else:
            from mo_logs import Log

            Log.error(text(repr(value)) + " is not JSON serializable")
    except Exception as e:
        from mo_logs import Log

        Log.error(text(repr(value)) + " is not JSON serializable", cause=e)


def _list2json(value, sub_schema, path, net_new_properties, buffer):
    if not value:
        append(buffer, "[]")
    else:
        sep = "["
        for v in value:
            append(buffer, sep)
            sep = COMMA
            typed_encode(v, sub_schema, path, net_new_properties, buffer)
        append(buffer, "]")
        # append(buffer, COMMA)
        # append(buffer, QUOTED_EXISTS_KEY)
        # append(buffer, text(len(value)))


def _multivalue2json(value, sub_schema, path, net_new_properties, buffer):
    if not value:
        append(buffer, "[]")
    elif len(value) == 1:
        append(buffer, json_encoder(value[0]))
    else:
        sep = "["
        for v in value:
            append(buffer, sep)
            sep = COMMA
            append(buffer, json_encoder(v))
        append(buffer, "]")


def _iter2json(value, sub_schema, path, net_new_properties, buffer):
    append(buffer, "[")
    sep = ""
    count = 0
    for v in value:
        append(buffer, sep)
        sep = COMMA
        typed_encode(v, sub_schema, path, net_new_properties, buffer)
        count += 1
    append(buffer, "]")
    append(buffer, COMMA)
    append(buffer, QUOTED_EXISTS_KEY)
    append(buffer, text(count))


def _dict2json(value, sub_schema, path, net_new_properties, buffer):
    prefix = "{"
    for k, v in sort_using_key(value.items(), lambda r: r[0]):
        if v == None or v == "":
            continue
        append(buffer, prefix)
        prefix = COMMA
        if is_binary(k):
            k = k.decode("utf8")
        if not is_text(k):
            Log.error("Expecting property name to be a string")
        if k not in sub_schema:
            sub_schema[k] = {}
            net_new_properties.append(path + [k])
        append(buffer, quote(encode_property(k)))
        append(buffer, COLON)
        typed_encode(v, sub_schema[k], path + [k], net_new_properties, buffer)
    if prefix is COMMA:
        append(buffer, COMMA)
        append(buffer, QUOTED_EXISTS_KEY)
        append(buffer, "1}")
    else:
        append(buffer, "{")
        append(buffer, QUOTED_EXISTS_KEY)
        append(buffer, "1}")


append = UnicodeBuilder.append

QUOTED_BOOLEAN_KEY = quote(BOOLEAN_KEY) + COLON
QUOTED_NUMBER_KEY = quote(NUMBER_KEY) + COLON
QUOTED_INTEGER_KEY = quote(INTEGER_KEY) + COLON
QUOTED_STRING_KEY = quote(STRING_KEY) + COLON
QUOTED_ARRAY_KEY = quote(ARRAY_KEY) + COLON
QUOTED_EXISTS_KEY = quote(EXISTS_KEY) + COLON

inserter_type_to_json_type = {
    BOOLEAN_KEY: BOOLEAN,
    NUMBER_KEY: NUMBER,
    INTEGER_KEY: INTEGER,
    STRING_KEY: STRING,
}

json_type_to_inserter_type = {
    BOOLEAN: BOOLEAN_KEY,
    INTEGER: NUMBER_KEY,
    NUMBER: NUMBER_KEY,
    STRING: STRING_KEY,
    ARRAY: ARRAY_KEY,
    EXISTS: EXISTS_KEY,
}

es_type_to_json_type = {
    "text": "string",
    "string": "string",
    "keyword": "string",
    "float": "number",
    "double": "number",
    "integer": "number",
    "object": "object",
    "nested": "nested",
    "source": "json",
    "boolean": "boolean",
    "exists": "exists",
}
