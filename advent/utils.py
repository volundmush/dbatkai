import uuid
import typing
import random
import string
import yaml
import json

from pathlib import Path


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
    for candidate in candidate_list:
        if match_text.lower() == key(candidate).lower():
            return candidate
        if not exact:
            if key(candidate).lower().startswith(match_text.lower()):
                return candidate


def generate_name(prefix: str, existing, gen_length: int = 20) -> str:
    def gen():
        return f"{prefix}_{''.join(random.choices(string.ascii_letters + string.digits, k=gen_length))}"

    while (u := gen()) not in existing:
        return u
