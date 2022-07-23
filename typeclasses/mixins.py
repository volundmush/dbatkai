from advent.handlers import SizeHandler, StatHandler, BoundedStatHandler
from athanor.modifiers import FlagsHandler, FlagHandler
from evennia.utils.utils import lazy_property
from evennia.utils.ansi import ANSIString

from evennia.utils.utils import to_str, logger, make_iter, class_from_module
from advent.utils import ev_to_rich
from advent.typing import Sex
from advent.sdesc import NPCSdescHandler, NPCRecogHandler
from evennia.contrib.rpg.rpsystem.rpsystem import parse_sdescs_and_recogs, _PREFIX
from evennia import ObjectDB


from evennia.objects.manager import _GA, _MULTIMATCH_REGEX

_SEARCH = None


def search_game_object(
        searchdata,
        attribute_name=None,
        typeclass=None,
        candidates=None,
        exact=True,
        use_dbref=True,
):
    def _searcher(searchdata, candidates, typeclass, exact=False):
        """
        Helper method for searching objects. `typeclass` is only used
        for global searching (no candidates)
        """
        if attribute_name:
            # attribute/property search (always exact).
            matches = ObjectDB.objects.get_objs_with_db_property_value(
                attribute_name, searchdata, candidates=candidates, typeclasses=typeclass
            )
            if matches:
                return matches
            return ObjectDB.objects.get_objs_with_attr_value(
                attribute_name, searchdata, candidates=candidates, typeclasses=typeclass
            )
        else:
            # normal key/alias search
            if searchdata.startswith("*"):
                return candidates
            return ObjectDB.objects.get_objs_with_key_or_alias(
                searchdata, exact=exact, candidates=candidates, typeclasses=typeclass
            )

    if not searchdata and searchdata != 0:
        return ObjectDB.objects.none()

    if typeclass:
        # typeclass may also be a list
        typeclasses = make_iter(typeclass)
        for i, typeclass in enumerate(make_iter(typeclasses)):
            if callable(typeclass):
                typeclasses[i] = "%s.%s" % (typeclass.__module__, typeclass.__name__)
            else:
                typeclasses[i] = "%s" % typeclass
        typeclass = typeclasses

    if candidates is not None:
        if not candidates:
            # candidates is the empty list. This should mean no matches can ever be acquired.
            return []
        # Convenience check to make sure candidates are really dbobjs
        candidates = [cand for cand in make_iter(candidates) if cand]
        if typeclass:
            candidates = [
                cand for cand in candidates if _GA(cand, "db_typeclass_path") in typeclass
            ]

    dbref = not attribute_name and exact and use_dbref and ObjectDB.objects.dbref(searchdata)
    if dbref:
        # Easiest case - dbref matching (always exact)
        dbref_match = ObjectDB.objects.dbref_search(dbref)
        if dbref_match:
            dmatch = dbref_match[0]
            if not candidates or dmatch in candidates:
                return dbref_match
            else:
                return ObjectDB.objects.none()

    # Search through all possibilities.
    match_number = None
    # always run first check exact - we don't want partial matches
    # if on the form of 1-keyword etc.
    matches = _searcher(searchdata, candidates, typeclass, exact=True)

    if not matches:
        # no matches found - check if we are dealing with N-keyword
        # query - if so, strip it.
        match = _MULTIMATCH_REGEX.match(str(searchdata))
        match_number = None
        stripped_searchdata = searchdata
        if match:
            # strips the number
            match_number, stripped_searchdata = match.group("number"), match.group("name")
        if match_number is not None:
            # run search against the stripped data
            matches = _searcher(stripped_searchdata, candidates, typeclass, exact=True)
            if not matches:
                # final chance to get a looser match against the number-strippped query
                matches = _searcher(stripped_searchdata, candidates, typeclass, exact=False)
        elif not exact:
            matches = _searcher(searchdata, candidates, typeclass, exact=False)

    # deal with result
    if len(matches) == 1 and match_number is not None and match_number.isnumeric() and int(match_number) - 1 != 0:
        # this indicates trying to get a single match with a match-number
        # targeting some higher-number match (like 2-box when there is only
        # one box in the room). This leads to a no-match.
        matches = ObjectDB.objects.none()
    elif len(matches) > 1 and match_number is not None:
        if not match_number.isnumeric():
            return matches
        # multiple matches, but a number was given to separate them
        if 0 <= match_number < len(matches):
            # limit to one match (we still want a queryset back)
            # TODO: Can we do this some other way and avoid a second lookup?
            matches = ObjectDB.objects.filter(id=matches[match_number].id)
        else:
            # a number was given outside of range. This means a no-match.
            matches = ObjectDB.objects.none()

    # return a list (possibly empty)
    return matches


class GameObj:

    def is_npc(self):
        return True

    def provides_light(self) -> bool:
        return False

    def is_illuminated(self) -> bool:
        return True

    def can_see_here(self) -> bool:
        if self.location:
            return True

    def filter_visible(self, candidates):
        return [c for c in candidates if self.can_see(c)]

    def get_visible_nearby(self, obj_type=None):
        if not self.can_see_here():
            return []

        candidates = []

        match obj_type:
            case "exit":
                candidates.extend(self.location.exits)
            case "vehicle":
                candidates.extend(self.location.vehicles.all())
            case "item":
                candidates.extend(self.location.inventory.all())
            case "character":
                candidates.extend(self.location.people.all())

        candidates.remove(self)
        return self.filter_visible(candidates)

    @lazy_property
    def size(self):
        return SizeHandler(self)

    def get_vnum_display(self):
        return None

    def generate_build_string(self, looker=None, **kwargs):
        build_string = list()
        if not self.locks.check_lockstring(looker, "perm(Builder)"):
            return build_string
        if (vnum := self.get_vnum_display()):
            build_string.append(vnum)
        if (trigs := self.dgscripts.ids()):
            build_string.append(f"|g[T{','.join(str(t) for t in trigs)}]|n")
        build_string.append(f"|g[{self.dbref}]|n")
        return build_string

    def get_display_name(self, looker=None, **kwargs):
        build_string = self.generate_build_string(looker=looker, **kwargs)
        name = self.db.color_name or self.key
        build_string.append(name)
        return " ".join(build_string)

    def get_visible_sex(self, looker=None, **kwargs):
        return Sex.NEUTER

    @lazy_property
    def level(self):
        return BoundedStatHandler(self, "level", default=1, min_amt=1, max_amt=100)

    @lazy_property
    def alignment(self):
        return BoundedStatHandler(self, "alignment", default=0, min_amt=-1000, max_amt=1000)

    @lazy_property
    def affect_flags(self):
        return FlagsHandler(self, "affect_flags", "AffectFlags")

    def search(
        self,
        searchdata,
        global_search=False,
        use_nicks=True,
        typeclass=None,
        location=None,
        attribute_name=None,
        quiet=False,
        exact=False,
        candidates=None,
        nofound_string=None,
        multimatch_string=None,
        use_dbref=None,
        lazy_first=True,
        allow_multiple=False
    ):
        """
        Returns an Object matching a search string/condition, taking
        sdescs into account.

        Perform a standard object search in the database, handling
        multiple results and lack thereof gracefully. By default, only
        objects in the current `location` of `self` or its inventory are searched for.

        Args:
            searchdata (str or obj): Primary search criterion. Will be matched
                against `object.key` (with `object.aliases` second) unless
                the keyword attribute_name specifies otherwise.
                **Special strings:**
                - `#<num>`: search by unique dbref. This is always
                   a global search.
                - `me,self`: self-reference to this object
                - `<num>-<string>` - can be used to differentiate
                   between multiple same-named matches
            global_search (bool): Search all objects globally. This is overruled
                by `location` keyword.
            use_nicks (bool): Use nickname-replace (nicktype "object") on `searchdata`.
            typeclass (str or Typeclass, or list of either): Limit search only
                to `Objects` with this typeclass. May be a list of typeclasses
                for a broader search.
            location (Object or list): Specify a location or multiple locations
                to search. Note that this is used to query the *contents* of a
                location and will not match for the location itself -
                if you want that, don't set this or use `candidates` to specify
                exactly which objects should be searched.
            attribute_name (str): Define which property to search. If set, no
                key+alias search will be performed. This can be used
                to search database fields (db_ will be automatically
                appended), and if that fails, it will try to return
                objects having Attributes with this name and value
                equal to searchdata. A special use is to search for
                "key" here if you want to do a key-search without
                including aliases.
            quiet (bool): don't display default error messages - this tells the
                search method that the user wants to handle all errors
                themselves. It also changes the return value type, see
                below.
            exact (bool): if unset (default) - prefers to match to beginning of
                string rather than not matching at all. If set, requires
                exact matching of entire string.
            candidates (list of objects): this is an optional custom list of objects
                to search (filter) between. It is ignored if `global_search`
                is given. If not set, this list will automatically be defined
                to include the location, the contents of location and the
                caller's contents (inventory).
            nofound_string (str):  optional custom string for not-found error message.
            multimatch_string (str): optional custom string for multimatch error header.
            use_dbref (bool or None): If None, only turn off use_dbref if we are of a lower
                permission than Builder. Otherwise, honor the True/False value.

        Returns:
            match (Object, None or list): will return an Object/None if `quiet=False`,
                otherwise it will return a list of 0, 1 or more matches.

        Notes:
            To find Accounts, use eg. `evennia.account_search`. If
            `quiet=False`, error messages will be handled by
            `settings.SEARCH_AT_RESULT` and echoed automatically (on
            error, return will be `None`). If `quiet=True`, the error
            messaging is assumed to be handled by the caller.

        """
        is_string = isinstance(searchdata, str)

        if is_string:
            # searchdata is a string; wrap some common self-references
            if searchdata.lower() in ("here",):
                return [self.location] if quiet else self.location
            if searchdata.lower() in ("me", "self"):
                return [self] if quiet else self

        if use_nicks:
            # do nick-replacement on search
            searchdata = self.nicks.nickreplace(
                searchdata, categories=("object", "account"), include_account=True
            )

        if global_search or (
            is_string
            and searchdata.startswith("#")
            and len(searchdata) > 1
            and searchdata[1:].isdigit()
        ):
            # only allow exact matching if searching the entire database
            # or unique #dbrefs
            exact = True
        elif candidates is None:
            # no custom candidates given - get them automatically
            if location:
                # location(s) were given
                candidates = []
                for obj in make_iter(location):
                    candidates.extend(obj.contents)
            else:
                # local search. Candidates are taken from
                # self.contents, self.location and
                # self.location.contents
                location = self.location
                candidates = self.contents
                if location:
                    candidates = candidates + [location] + location.contents
                else:
                    # normally we don't need this since we are
                    # included in location.contents
                    candidates.append(self)

        # the sdesc-related substitution
        is_builder = self.locks.check_lockstring(self, "perm(Builder)")
        use_dbref = is_builder if use_dbref is None else use_dbref

        def search_obj(string):
            "helper wrapper for searching"
            return search_game_object(
                string,
                attribute_name=attribute_name,
                typeclass=typeclass,
                candidates=candidates,
                exact=exact,
                use_dbref=use_dbref,
            )

        results = []
        if attribute_name:
            # let Evennia's default search handle attribute_name searches
            results = search_obj(searchdata)
        else:
            m = _MULTIMATCH_REGEX.match(searchdata)
            sel = m.group("number")
            searchname = m.group("name")

            if candidates:
                if not searchname.startswith("*"):
                    # the * check means it matches everything.
                    candidates = parse_sdescs_and_recogs(
                        self, candidates, _PREFIX + searchname, search_mode=True
                    )

                for candidate in candidates:
                    # we search by candidate keys here; this allows full error
                    # management and use of all kwargs - we will use searchdata
                    # in eventual error reporting later (not their keys). Doing
                    # it like this e.g. allows for use of the typeclass kwarg
                    # limiter.
                    results.extend([obj for obj in search_obj(candidate.key) if obj not in results])

                if not results and is_builder:
                    # builders get a chance to search only by key+alias
                    results = search_obj(searchdata)
                else:
                    # re-implement the multimatch for sdesc matches
                    if sel is not None:
                        if sel.isnumeric():
                            idx = int(sel)
                            if idx <= len(results):
                                results = [results[idx-1]]
                            else:
                                results = []
                        else:
                            # sel is * or all. do not remove anything from results set.
                            pass
                    else:
                        if lazy_first and results:
                            results = [results[0]]

        if quiet or allow_multiple:
            return results

        global _SEARCH
        if not _SEARCH:
            from django.conf import settings
            _SEARCH = class_from_module(settings.SEARCH_AT_RESULT)
        return _SEARCH(
            results,
            self,
            query=searchdata,
            nofound_string=nofound_string,
            multimatch_string=multimatch_string,
        )
