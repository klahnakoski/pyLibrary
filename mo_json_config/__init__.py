# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import os
import re

from mo_dots import (
    is_data,
    is_list,
    set_default,
    from_data,
    to_data,
    is_sequence,
    coalesce,
    get_attr,
    listwrap,
    unwraplist,
    dict_to_data,
    Data,
    join_field,
)
from mo_files import File
from mo_files.url import URL
from mo_future import is_text
from mo_future import text
from mo_json import json2value
from mo_logs import Except, logger

from mo_json_config.configuration import Configuration
from mo_json_config.convert import ini2value

DEBUG = False


def get_file(file):
    file = File(file)
    return get("file://" + file.abs_path)


def get(url):
    """
    USE json.net CONVENTIONS TO LINK TO INLINE OTHER JSON
    """
    url = text(url)
    if "://" not in url:
        logger.error("{{url}} must have a prototcol (eg http://) declared", url=url)

    base = URL("")
    if url.startswith("file://") and url[7] != "/":
        if os.sep == "\\":
            base = URL("file:///" + os.getcwd().replace(os.sep, "/").rstrip("/") + "/.")
        else:
            base = URL("file://" + os.getcwd().rstrip("/") + "/.")

    phase1 = _replace_ref(dict_to_data({"$ref": url}), base)  # BLANK URL ONLY WORKS IF url IS ABSOLUTE
    try:
        phase2 = _replace_locals(phase1, [phase1])
        return to_data(phase2)
    except Exception as cause:
        logger.error("problem replacing locals in\n{{phase1}}", phase1=phase1, cause=cause)


def expand(doc, doc_url="param://", params=None):
    """
    ASSUMING YOU ALREADY PULED THE doc FROM doc_url, YOU CAN STILL USE THE
    EXPANDING FEATURE

    USE mo_json_config.expand({}) TO ASSUME CURRENT WORKING DIRECTORY

    :param doc: THE DATA STRUCTURE FROM JSON SOURCE
    :param doc_url: THE URL THIS doc CAME FROM (DEFAULT USES params AS A DOCUMENT SOURCE)
    :param params: EXTRA PARAMETERS NOT FOUND IN THE doc_url PARAMETERS (WILL SUPERSEDE PARAMETERS FROM doc_url)
    :return: EXPANDED JSON-SERIALIZABLE STRUCTURE
    """
    if "://" not in doc_url:
        logger.error("{{url}} must have a prototcol (eg http://) declared", url=doc_url)

    url = URL(doc_url)
    url.query = set_default(url.query, params)
    phase1 = _replace_ref(doc, url)  # BLANK URL ONLY WORKS IF url IS ABSOLUTE
    phase2 = _replace_locals(phase1, [phase1])
    return to_data(phase2)


def _replace_ref(node, url):
    if url.path.endswith("/"):
        url.path = url.path[:-1]

    if is_data(node):
        refs = None
        output = {}
        for k, v in node.items():
            if k == "$ref":
                refs = URL(v)
            else:
                output[k] = _replace_ref(v, url)

        if not refs:
            return output

        ref_found = False
        ref_error = None
        ref_remain = []
        for ref in listwrap(refs):
            if not ref.scheme and not ref.path:
                # DO NOT TOUCH LOCAL REF YET
                ref_remain.append(ref)
                ref_found = True
                continue

            if not ref.scheme:
                # SCHEME RELATIVE IMPLIES SAME PROTOCOL AS LAST TIME, WHICH
                # REQUIRES THE CURRENT DOCUMENT'S SCHEME
                ref.scheme = url.scheme

            # FIND THE SCHEME AND LOAD IT
            if ref.scheme not in scheme_loaders:
                raise logger.error("unknown protocol {{scheme}}", scheme=ref.scheme)
            try:
                new_value = scheme_loaders[ref.scheme](ref, url)
                ref_found = True
            except Exception as e:
                e = Except.wrap(e)
                ref_error = e
                continue

            if ref.fragment:
                new_value = get_attr(new_value, ref.fragment)

            DEBUG and logger.note("Replace {{ref}} with {{new_value}}", ref=ref, new_value=new_value)

            if not output:
                output = new_value
            elif is_text(output):
                pass  # WE HAVE A VALUE
            else:
                set_default(output, new_value)

        if not ref_found:
            raise ref_error
        if ref_remain:
            output["$ref"] = unwraplist(ref_remain)
        DEBUG and logger.note("Return {{output}}", output=output)
        return output
    elif is_list(node):
        output = [_replace_ref(n, url) for n in node]
        # if all(p[0] is p[1] for p in zip(output, node)):
        #     return node
        return output

    return node


def _replace_locals(node, doc_path):
    if is_data(node):
        # RECURS, DEEP COPY
        ref = None
        output = {}
        for k, v in node.items():
            if k == "$ref":
                ref = v
            elif k == "$concat":
                if not is_sequence(v):
                    logger.error("$concat expects an array of strings")
                return coalesce(node.get("separator"), "").join(v)
            elif v == None:
                continue
            else:
                output[k] = _replace_locals(v, [v] + doc_path)

        if not ref:
            return output

        # REFER TO SELF
        frag = ref.fragment
        if frag[0] == ".":
            # RELATIVE
            for i, p in enumerate(frag):
                if p != ".":
                    if i > len(doc_path):
                        logger.error(
                            "{{frag|quote}} reaches up past the root document", frag=frag,
                        )
                    new_value = get_attr(doc_path[i - 1], frag[i::])
                    break
            else:
                new_value = doc_path[len(frag) - 1]
        else:
            # ABSOLUTE
            new_value = get_attr(doc_path[-1], frag)

        new_value = _replace_locals(new_value, [new_value] + doc_path)

        if not output:
            return new_value  # OPTIMIZATION FOR CASE WHEN node IS {}
        else:
            return from_data(set_default(output, new_value))

    elif is_list(node):
        candidate = [_replace_locals(n, [n] + doc_path) for n in node]
        # if all(p[0] is p[1] for p in zip(candidate, node)):
        #     return node
        return candidate

    return node


###############################################################################
## SCHEME LOADERS ARE BELOW THIS LINE
###############################################################################


def _get_file(ref, url):

    if ref.path.startswith("~"):
        home_path = os.path.expanduser("~")
        if os.sep == "\\":
            home_path = "/" + home_path.replace(os.sep, "/")
        if home_path.endswith("/"):
            home_path = home_path[:-1]

        ref.path = home_path + ref.path[1::]
    elif not ref.path.startswith("/"):
        # CONVERT RELATIVE TO ABSOLUTE
        if ref.path[0] == ".":
            num_dot = 1
            while ref.path[num_dot] == ".":
                num_dot += 1

            parent = url.path.rstrip("/").split("/")[:-num_dot]
            ref.path = "/".join(parent) + ref.path[num_dot:]
        else:
            parent = url.path.rstrip("/").split("/")[:-1]
            ref.path = "/".join(parent) + "/" + ref.path

    path = ref.path if os.sep != "\\" else ref.path[1::].replace("/", "\\")

    try:
        DEBUG and logger.note("reading file {{path}}", path=path)
        content = File(path).read()
    except Exception as e:
        content = None
        logger.error("Could not read file {{filename}}", filename=path, cause=e)

    try:
        new_value = json2value(content, params=ref.query, flexible=True, leaves=True)
    except Exception as e:
        e = Except.wrap(e)
        try:
            new_value = ini2value(content)
        except Exception:
            raise logger.error("Can not read {{file}}", file=path, cause=e)
    new_value = _replace_ref(new_value, ref)
    return new_value


def get_http(ref, url):
    import requests

    params = url.query
    new_value = json2value(requests.get(str(ref)).json(), params=params, flexible=True, leaves=True)
    return new_value


def _get_env(ref, url):
    # GET ENVIRONMENT VARIABLES
    ref = ref.host
    raw_value = os.environ.get(ref)
    if not raw_value:
        logger.error("expecting environment variable with name {{env_var}}", env_var=ref)

    try:
        new_value = json2value(raw_value)
    except Exception as e:
        new_value = raw_value
    return new_value


def _get_keyring(ref, url):
    try:
        import keyring
    except Exception:
        logger.error("Missing keyring: `pip install keyring` to use this feature")

    # GET PASSWORD FROM KEYRING
    service_name = ref.host
    if "@" in service_name:
        username, service_name = service_name.split("@")
    else:
        username = ref.query.username

    raw_value = keyring.get_password(service_name, username)
    if not raw_value:
        logger.error(
            "expecting password in the keyring for service_name={{service_name}} and username={{username}}",
            service_name=service_name,
            username=username,
        )

    try:
        new_value = json2value(raw_value)
    except Exception as e:
        new_value = raw_value
    return new_value


ssm_has_failed = False


def _get_ssm(ref, url):
    global ssm_has_failed

    output = Data()

    if ssm_has_failed:
        return output
    try:
        import boto3
    except Exception:
        logger.error("Missing boto3: `pip install boto3` to use ssm://")
    try:
        ssm = boto3.client("ssm")
        result = ssm.describe_parameters(MaxResults=10)
        prefix = re.compile("^" + re.escape(ref.path.rstrip("/")) + "/|$")
        while True:
            for param in result["Parameters"]:
                name = param["Name"]
                found = prefix.match(name)
                if not found:
                    continue
                tail = join_field(name[found.regs[0][1] :].split("/"))
                detail = ssm.get_parameter(Name=name, WithDecryption=True)
                output[tail] = detail["Parameter"]["Value"]

            next_token = result.get("NextToken")
            if not next_token:
                break
            result = ssm.describe_parameters(NextToken=next_token, MaxResults=10)
    except Exception as cause:
        ssm_has_failed = True
        logger.warning("Could not get ssm parameters", cause=cause)
        return output

    if len(output) == 0:
        logger.error("No ssm parameters found at {{path}}", path=ref.path)
    return output


def _get_param(ref, url):
    # GET PARAMETERS FROM url
    param = url.query
    new_value = param[ref.host]
    return new_value


scheme_loaders = {
    "http": get_http,
    "https": get_http,
    "file": _get_file,
    "env": _get_env,
    "param": _get_param,
    "keyring": _get_keyring,
    "ssm": _get_ssm,
}


configuration = Configuration({})
