import uuid
import typing
import random
import string
import yaml
import json
import inflect

from pathlib import Path
from evennia.utils.ansi import parse_ansi, ANSIString
from rich.ansi import AnsiDecoder
from rich.console import group

from collections import defaultdict

from django.utils.translation import gettext as _
from evennia.utils.utils import _MULTIMATCH_TEMPLATE

INFLECT = inflect.engine()


def read_json_file(p: Path):
    return json.loads(open(p, mode='rb').read())


def read_yaml_file(p: Path):
    return yaml.safe_load(open(p, mode="r"))


def read_data_file(p: Path):
    if p.name.lower().endswith(".json"):
        return read_json_file(p)
    elif p.name.lower().endswith(".yaml"):
        return read_yaml_file(p)
    return None


def fresh_uuid4(existing) -> uuid:
    """
    Given a list of UUID4s, generate a new one that's not already used.
    Yes, I know this is silly. UUIDs are meant to be unique by sheer statistic unlikelihood of a conflict.
    I'm just that afraid of collisions.
    """
    existing = set(existing)
    fresh_uuid = uuid.uuid4()
    while fresh_uuid in existing:
        fresh_uuid = uuid.uuid4()
    return fresh_uuid


def partial_match(
    match_text: str, candidates: typing.Iterable[typing.Any], key: callable = str, exact: bool = False) -> typing.Optional[typing.Any]:
    """
    Given a list of candidates and a string to search for, does a case-insensitive partial name search against all
    candidates, preferring exact matches.

    Args:
        match_text (str): The string being searched for.
        candidates (list of obj): A list of any kind of object that key can turn into a string to search.
        key (callable): A callable that must return a string, used to do the search. this 'converts' the objects in the
            candidate list to strings.

    Returns:
        Any or None.
    """
    candidate_list = sorted(candidates, key=lambda item: len(key(item)))
    mlow = match_text.lower()
    for candidate in candidate_list:
        can_lower = key(candidate).lower()
        if mlow == can_lower:
            return candidate
        if not exact:
            if can_lower.startswith(mlow):
                return candidate


def generate_name(prefix: str, existing, gen_length: int = 20) -> str:
    def gen():
        return f"{prefix}_{''.join(random.choices(string.ascii_letters + string.digits, k=gen_length))}"

    while (u := gen()) not in existing:
        return u


@group()
def ev_to_rich(s: str):
    if isinstance(s, ANSIString):
        for line in AnsiDecoder().decode(str(s)):
            yield line
    else:
        ev = parse_ansi(s, xterm256=True, mxp=True)
        for line in AnsiDecoder().decode(ev):
            yield line


def echo_action(template: str, actors: dict[str, "DefaultObject"], viewers: typing.Iterable["DefaultObject"], **kwargs):

    for viewer in viewers:
        var_dict = defaultdict(lambda: "!ERR!")
        var_dict.update(kwargs)
        for k, v in actors.items():
            v.get_template_vars(var_dict, k, looker=viewer)

        viewer.msg(text=ev_to_rich(template.format_map(var_dict)))


def iequals(first: str, second: str):
    return str(first).lower() == str(second).lower()


def at_search_result(matches, caller, query="", quiet=False, allow_multiple=False, **kwargs):
    """
    This is a generic hook for handling all processing of a search
    result, including error reporting. This is also called by the cmdhandler
    to manage errors in command lookup.

    Args:
        matches (list): This is a list of 0, 1 or more typeclass
            instances or Command instances, the matched result of the
            search. If 0, a nomatch error should be echoed, and if >1,
            multimatch errors should be given. Only if a single match
            should the result pass through.
        caller (Object): The object performing the search and/or which should
        receive error messages.
        query (str, optional): The search query used to produce `matches`.
        quiet (bool, optional): If `True`, no messages will be echoed to caller
            on errors.
    Keyword Args:
        nofound_string (str): Replacement string to echo on a notfound error.
        multimatch_string (str): Replacement string to echo on a multimatch error.

    Returns:
        processed_result (Object or None): This is always a single result
        or `None`. If `None`, any error reporting/handling should
        already have happened. The returned object is of the type we are
        checking multimatches for (e.g. Objects or Commands)

    """

    error = ""
    if not matches:
        # no results.
        error = kwargs.get("nofound_string") or _("Could not find '{query}'.").format(query=query)
        matches = None
    elif len(matches) > 1:
        if allow_multiple:
            return matches
        multimatch_string = kwargs.get("multimatch_string")
        if multimatch_string:
            error = "%s\n" % multimatch_string
        else:
            error = _("More than one match for '{query}' (please narrow target):\n").format(
                query=query
            )

        for num, result in enumerate(matches):
            # we need to consider Commands, where .aliases is a list
            aliases = result.aliases.all() if hasattr(result.aliases, "all") else result.aliases
            # remove any pluralization aliases
            aliases = [
                alias
                for alias in aliases
                if hasattr(alias, "category") and alias.category not in ("plural_key",)
            ]
            error += _MULTIMATCH_TEMPLATE.format(
                number=num + 1,
                name=result.get_display_name(caller)
                if hasattr(result, "get_display_name")
                else query,
                aliases=" [{alias}]".format(alias=";".join(aliases) if aliases else ""),
                info=result.get_extra_info(caller),
            )
        matches = None
    else:
        # exactly one match
        matches = matches[0]

    if error and not quiet:
        caller.msg(error.strip())
    return matches
