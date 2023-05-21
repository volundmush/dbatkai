import typing
import operator as o
import re
from django.conf import settings
from collections import defaultdict
from random import randint
from enum import IntEnum, IntFlag
from athanor.exceptions import DGScriptError
from evennia.utils.ansi import strip_ansi
from evennia.utils.utils import lazy_property, class_from_module, logger
from evennia import ObjectDB
from advent import DG_FUNCTIONS, DG_VARS
from typeclasses.scripts import Script, DgScriptPrototype
from evennia.utils.search import search_script_tag


class DGState(IntEnum):
    DORMANT = 0
    RUNNING = 1
    WAITING = 2
    ERROR = 3
    DONE = 4
    PURGED = 5


class Nest(IntEnum):
    IF = 0
    WHILE = 1
    SWITCH = 2


def matching_quote(src: str, start: int) -> int:
    """
    Given a string and a starting index, find the matching quote.
    Return a -1 if no match is found.
    """
    try:
        if src[start] != '"':  # Sanity check
            return -1
        escaped = False
        current = start + 1

        while True:
            if escaped:
                escaped = False
            else:
                match src[current]:
                    case "\\":
                        escaped = True
                    case '"':
                        return current
                    case _:
                        pass
            current += 1

    except IndexError:
        return -1


def matching_paren(src: str, start: int) -> int:
    """
    Given a string and a starting index, find the matching closing paren.
    This is sensitive to nesting depth.

    Return a -1 if no match is found.
    """
    try:
        if src[start] != "(":  # Sanity check
            return -1
        depth = 0
        current = start + 1
        while True:
            match src[current]:
                case "(":
                    depth += 1
                case '"':
                    current = matching_quote(src, current)
                    if current == -1:
                        return -1
                case ")":
                    if depth:
                        depth -= 1
                    else:
                        return current
                case _:
                    pass
            current += 1

    except IndexError:
        return -1


def matching_perc(src: str, start: int) -> int:
    """
    Given a string and a starting index, find the matching %.
    This is sensitive to nesting depth.
    Return -1 if nothing is found.
    """
    try:
        if src[start] != "%":  # Sanity check
            return -1
        current = start + 1
        while True:
            match src[current]:
                case "(":
                    current = matching_paren(src, current)
                    continue
                case "%":
                    return current
            current += 1
    except IndexError:
        return -1


class DGScriptInstance(Script):

    def at_script_creation(self):
        self.db.proto = None
        self.db.state = DGState.DORMANT
        self.db.wait_time = 0.0
        self.db.curr_line = 0
        self.db.context = 0
        self.db.lines: list[str] = list()
        self.db.depth: list[tuple[Nest, int]] = list()
        self.db.loops = 0
        self.db.total_loops = 0
        self.db.vars: dict[str, str] = dict()

    def types(self) -> set[str]:
        return self.db.proto.trigger_types()

    @property
    def handler(self):
        return self.obj.dgscripts

    @property
    def proto_key(self) -> str:
        return self.db.proto.key

    def reset(self):
        self.db.curr_line = 0
        self.db.lines = self.db.proto.db.script_body.splitlines()
        self.set_state(DGState.DORMANT)
        self.db.depth.clear()
        self.db.loops = 0
        self.db.total_loops = 0
        self.db.context = 0
        self.db.vars.clear()

    def script_log(self, msg: str):
        print(f"SCRIPT ERROR: {msg}")

    def set_state(self, state: DGState):
        self.db.state = state
        #print(f"{self} STATE: {self.db.state.name}")

    def at_repeat(self):
        match self.db.state:
            case DGState.WAITING:
                self.decrement_timer()
            case DGState.ERROR | DGState.DONE | DGState.PURGED:
                self.reset()

    def decrement_timer(self):
        self.db.wait_time -= self.interval
        if self.db.wait_time <= 0.0:
            self.db.wait_time = 0.0
            self.execute()

    def execute(self) -> int:
        #print(f"EXECUTE: {self}")
        try:
            match self.db.state:
                case DGState.RUNNING | DGState.ERROR | DGState.DONE | DGState.PURGED:
                    raise DGScriptError(f"script called in invalid state {self.db.state.name}")
            if not len(self.db.lines):
                raise DGScriptError("script has no lines to execute")
            self.set_state(DGState.RUNNING)
            results = self.execute_block(self.db.curr_line, len(self.db.lines))
            self.start()
            if self.db.state == DGState.DONE:
                self.reset()
            return results
        except DGScriptError as err:
            self.set_state(DGState.ERROR)
            self.script_log(f"{err} - {self.db.proto.key} - Line {self.db.curr_line+1}")
            return 0

    def execute_block(self, start: int, end: int) -> int:

        ret_val = 1

        self.db.curr_line = start

        while self.db.curr_line < end:
            #print(f"CURR_LINE: {self.db.curr_line} against {end}")

            if self.db.loops == 500:
                #print(f"{self} RAN TOO LONG!")
                # this has run long enough, let's pause it.
                self.set_state(DGState.WAITING)
                self.db.wait_time = 1.0
                self.db.loops = 0
                return ret_val

            self.db.loops += 1
            self.db.total_loops += 1

            if self.db.total_loops > 2000:
                raise DGScriptError("Runaway Script Halted")

            line = self.get_line(self.db.curr_line)
            if not line or line.startswith("*"):
                pass  #print(f"GOT COMMENT... skipping...")

            # cover if
            elif line.startswith("if "):
                self.db.depth.append((Nest.IF, self.db.curr_line))
                #print(f"CHECKING IF: {line}")
                if not self.process_if(line[3:]):
                    #print(f"IF {line} failed, checking for else/end...")
                    self.db.curr_line = self.find_else_end()
                    #print(f"IF Failed, proceeding at {self.db.curr_line}")
                    continue
            elif line.startswith("elseif "):
                if not self.db.depth or self.db.depth[-1][0] != Nest.IF:
                    raise DGScriptError("'elseif' outside of an if block")
                self.db.curr_line = self.find_end()
                continue
            elif line == "else" or line.startswith("else "):
                if not self.db.depth or self.db.depth[-1][0] != Nest.IF:
                    raise DGScriptError("'else' outside of an if block")
                self.db.curr_line = self.find_end()
                continue
            elif line == "end" or line.startswith("end "):
                if not self.db.depth or self.db.depth[-1][0] != Nest.IF:
                    raise DGScriptError("'end' outside of an if block")
                self.db.depth.pop()
                #print(f"END OF IF {self.db.curr_line}")

            # cover while
            elif line.startswith("while "):
                self.db.depth.append((Nest.WHILE, self.db.curr_line))
                if not self.process_if(line[6:]):
                    #print(f"WHILE {line} IS TRUE")
                    self.db.curr_line = self.find_done()
                    continue

            # cover switch
            elif line.startswith("switch "):
                self.db.depth.append((Nest.SWITCH, self.db.curr_line))
                self.db.curr_line = self.find_case(line[7:])
                continue

            elif line == "break" or line.startswith("break "):
                if not self.db.depth or self.db.depth[-1][0] != Nest.SWITCH:
                    raise DGScriptError("'break' outside of a switch-case block")
                self.db.curr_line = self.find_done()
                continue

            elif line.startswith("case "):
                if not self.db.depth or self.db.depth[-1][0] != Nest.SWITCH:
                    raise DGScriptError("'break' outside of a switch-case block")
                # Fall through behavior mimicking C switch
                continue

            elif line == "done" or line.startswith("done "):
                if not self.db.depth:
                    raise DGScriptError("'done' outside of a switch-case or while block")
                match self.db.depth[-1][0]:
                    case Nest.WHILE:
                        # Rewind back to the while clause.
                        #print(f"REACHED WHILE END {self.db.curr_line}")
                        self.db.curr_line = self.db.depth[-1][1]
                        self.db.depth.pop()
                        continue
                    case Nest.SWITCH:
                        #print(f"REACHED SWITCH END {self.db.curr_line}")
                        self.db.depth.pop()
                    case _:
                        raise DGScriptError("'done' outside of a switch-case or while block")


            else:
                #print(f"Checking Line... {line}")
                sub_cmd = self.var_subst(line)
                #print(f"post var_subst: {sub_cmd}")
                cmd_split = sub_cmd.split(" ", 1)
                cmd = cmd_split[0]

                match cmd.lower():
                    case "nop":
                        # Do nothing.
                        pass
                    case "return":
                        if len(cmd_split) > 1:
                            out = cmd_split[1]
                            self.set_state(DGState.DONE)
                            if out not in ("0", "1"):
                                return int(self.truthy(out))
                            else:
                                return int(out)
                        else:
                            return ret_val
                    case "wait":
                        if (wait_time := self.cmd_wait(sub_cmd)):
                            self.set_state(DGState.WAITING)
                            self.db.wait_time = wait_time
                            self.db.loops = 0
                            self.db.curr_line += 1
                            return ret_val
                    case _:
                        if (func := getattr(self, f"cmd_{cmd}", None)):
                            func(sub_cmd)
                        else:
                            #print(f"Unrecognized command {cmd}, passing to execute_cmd...")
                            self.handler.owner.execute_cmd(sub_cmd)

            #print(f"Incrementing line...")
            self.db.curr_line += 1

        self.set_state(DGState.DONE)

    def truthy(self, value: str) -> bool:
        if not value:
            #print(f"TRUTHY OF {value}: False")
            return False
        res = value != "0"
        #print(f"TRUTHY of {value}: {res}")
        return res

    def process_if(self, cond: str) -> bool:
        result = self.truthy(self.maybe_negate(self.eval_expr(cond).strip()))
        #print(f"IF {cond} : {result}")
        return result

    def eval_expr(self, line: str) -> str:
        #print(f"EVAL_EXPR: {line}")
        trimmed = line.strip()
        if trimmed.startswith("("):
            m = matching_paren(trimmed, 0)
            if m != -1:
                return self.eval_expr(trimmed[1:m])
        elif (result := self.eval_lhs_op_rhs(trimmed)):
            return result
        else:
            return self.var_subst(trimmed)

    ops_map = {
        "||": o.or_,
        "&&": o.and_,
        "==": o.eq,
        "!=": o.ne,
        "<=": o.le,
        ">=": o.ge,
        "<": o.lt,
        ">": o.gt,
        "/=": o.truediv,
        "-": o.sub,
        "+": o.add,
        "/": o.floordiv,
        "*": o.mul,
        #"!": o.not_
    }

    def eval_lhs_op_rhs(self, expr: str) -> typing.Optional[str]:
        #print(f"EVAL_LHS_OP_RHS: {expr}")
        for op in self.ops_map.keys():
            try:
                lhs, rhs = expr.split(op, 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                #print(f"LHS: {lhs}, RHS: {rhs}")
                lhr = self.eval_expr(lhs)
                rhr = self.eval_expr(rhs)
                #print(f"LHR: {lhr}, RHR: {rhr}")
                result = self.eval_op(op, lhr, rhr)
                #print(f"EVAL OP RESULT: {result}")
                return result
            except ValueError:
                continue

    def maybe_negate(self, data: str):
        if data.startswith("!"):
            return "0" if self.truthy(self.maybe_negate(data[1:])) else "1"
        return data

    def eval_op(self, op: str, lhs: str, rhs: str) -> str:
        op_found = self.ops_map[op]
        #print(f"EVAL OP: {op} - {op_found}")
        result = "0"

        lhs = self.maybe_negate(lhs)
        rhs = self.maybe_negate(rhs)

        if lhs.isnumeric() and rhs.isnumeric():
            a = int(lhs)
            b = int(rhs)
            if op_found(a, b):
                result = "1"
        else:
            match op:
                case "&&":
                    if self.truthy(lhs) and self.truthy(rhs):
                        result = "1"
                case "==" | "!=":
                    if op_found(lhs.lower(), rhs.lower()):
                        result = "1"
                case "||":
                    if  self.truthy(lhs) or self.truthy(rhs):
                        result = "1"
                case _:
                    result = "0"
        return result

    def find_replacement(self, v: str) -> str:
        pass

    def add_local_var(self, name: str, value: str):
        pass

    def get_line(self, i: int) -> str:
        line = self.db.lines[i].strip()
        #print(f"GET_LINE: {line}")
        return line

    def find_else_end(self, match_elseif: bool = True, match_else: bool = True) -> int:
        if not self.db.depth or self.db.depth[-1][0] != Nest.IF:
            #print(f"FIND ELSE END WHOOPS 1")
            raise DGScriptError("find_end called outside of if! alert a codewiz!")

        i = self.db.depth[-1][1] + 1
        total = len(self.db.lines)
        while i < total:
            line = self.get_line(i)
            #print(f"Scanning for Else {match_else}, Elseif {match_elseif}, line {i} : {line}")
            if not line or line.startswith("*"):
                pass

            elif match_elseif and line.startswith("elseif ") and self.process_if(line[7:]):
                #print(f"found truthy elseif {i}")
                return i + 1

            elif match_else and (line.startswith("else ") or line == "else"):
                #print(f"found else {i}")
                return i + 1

            elif line.startswith("end ") or line == "end":
                #print(f"found end {i}")
                return i

            elif line.startswith("if "):
                depth = len(self.db.depth)
                #print(f"Nested IF detected at {i}. Depth: {depth}")
                self.db.depth.append((Nest.IF, i))
                i = self.find_end() + 1
                #print(f"exited depth {depth} IF...")
                self.db.depth.pop()
                continue

            elif line.startswith("switch "):
                self.db.depth.append((Nest.SWITCH, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("while "):
                self.db.depth.append((Nest.WHILE, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line == "default" or line.startswith("default "):
                raise DGScriptError("'default' outside of a switch-case block")

            elif line == "done" or line.startswith("done "):
                raise DGScriptError("'done' outside of a switch-case or while block")

            elif line == "case" or line.startswith("case "):
                raise DGScriptError("'case' outside of a switch-case block")

            #print(f"incrementing {i}")
            i += 1

        raise DGScriptError("'if' without corresponding end")


    def find_end(self) -> int:
        return self.find_else_end(match_elseif=False, match_else=False)

    def find_done(self) -> int:
        if not self.db.depth or self.db.depth[-1][0] not in (Nest.SWITCH, Nest.WHILE):
            raise DGScriptError("find_done called outside of a switch-case or while block! alert a codewiz!")

        inside = self.db.depth[-1][0].name.capitalize()

        i = self.db.depth[-1][1] + 1
        total = len(self.db.lines)
        while i < total:
            line = self.get_line(i)
            if not line or line.startswith("*"):
                pass

            elif line.startswith("if "):
                self.db.depth.append((Nest.IF, i))
                i = self.find_end() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("switch "):
                self.db.depth.append((Nest.SWITCH, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("while "):
                self.db.depth.append((Nest.WHILE, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("elseif "):
                raise DGScriptError("'elseif' outside of an if block")

            elif line.startswith("else ") or line == "else":
                raise DGScriptError("'else' outside of an if block")

            elif line == "end" or line.startswith("end "):
                raise DGScriptError("'end' outside of an if block")

            elif line == "default" or line.startswith("default "):
                raise DGScriptError("'default' outside of a switch-case block")

            elif line == "done" or line.startswith("done "):
                return i

            i += 1
        raise DGScriptError(f"'{inside}' without corresponding done")

    def find_case(self, cond: str) -> int:
        if not self.db.depth or self.db.depth[-1][0] != Nest.SWITCH:
            raise DGScriptError("find_case called outside of if! alert a codewiz!")

        res = self.eval_expr(cond)

        i = self.db.depth[-1][1] + 1
        total = len(self.lines)
        while i < total:
            line = self.get_line(i)
            if not line or line.startswith("*"):
                pass

            if line.startswith("case ") and self.truthy(self.eval_op("==", res, line[5:])):
                return i + 1

            elif line == "default" or line.startswith("default "):
                return i + 1

            elif line == "done" or line.startswith("done "):
                return i

            elif line.startswith("if "):
                self.db.depth.append((Nest.IF, i))
                i = self.find_end() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("switch "):
                self.db.depth.append((Nest.SWITCH, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("while "):
                self.db.depth.append((Nest.WHILE, i))
                i = self.find_done() + 1
                self.db.depth.pop()
                continue

            elif line.startswith("end ") or line == "end":
                raise DGScriptError("'end' outside of an if block")

            elif line.startswith("elseif "):
                raise DGScriptError("'elseif' outside of an if block")

            elif line.startswith("else ") or line == "else":
                raise DGScriptError("'else' outside of an if block")

            i += 1

        raise DGScriptError("'switch' without corresponding done")

    _re_expr = re.compile(r"^(?P<everything>(?P<varname>\w+)(?:.(?P<field>\w+?)?)?(?P<call>\((?P<arg>[\w| ]+)?\))?)$")

    _re_dbref = re.compile(r"^#\d+$")

    def get_members(self, data: str):
        start = 0
        i = 0
        member = ""
        call = False
        arg = ""
        try:
            while True:
                match data[i]:
                    case ".":
                        yield {"member": member, "call": call, "arg": arg}
                        member = ""
                        call = False
                        arg = ""
                    case "(":
                        m = matching_paren(data, i)
                        if m != -1:
                            arg = data[i+1:m]
                            call = True
                            i = m + 1
                            continue
                    case _:
                        if call:
                            pass
                        else:
                            member += data[i]
                i += 1

        except IndexError as err:
            yield {"member": member, "call": call, "arg": arg}

    def eval_var(self, data: str) -> str:

        def _db_check(text):
            if hasattr(text, "dbref"):
                return text
            if self._re_dbref.match(text):
                if (found := ObjectDB.objects.filter(id=int(text[1:])).first()):
                    return found
            return text

        last_mem = None
        for mem in self.get_members(data):
            if hasattr(last_mem, "dbref"):
                result = last_mem.dgscripts.evaluate(self, **mem)
                last_mem = _db_check(result)
            elif callable(last_mem):
                result = last_mem(self, **mem)
                last_mem = _db_check(result)
            elif isinstance(last_mem, str):
                # strings CANNOT have members.
                return ""
            elif last_mem is not None:
                # safety check
                return ""
            else:
                # this is probably a special var. Let's check those first.
                if (found := DG_VARS.get(mem["member"].lower(), None)):
                    if callable(found):
                        last_mem = _db_check(found(self, **mem))
                    elif isinstance(found, str):
                        last_mem = _db_check(found)
                else:
                    v = self.db.vars.get(mem["member"].lower(), "")
                    last_mem = _db_check(v)

        while callable(last_mem):
            last_mem = last_mem(self)

        if not isinstance(last_mem, str):
            return ""

        #print(f"eval_var results: {last_mem}")
        return last_mem

    def get_var(self, varname: str, context: int = -1) -> typing.Optional[str]:
        pass

    def var_subst(self, line: str) -> str:
        #print(f"VAR_SUBST: {line}")
        out = ""
        i = 0
        escaped = False

        try:
            while True:
                if escaped:
                    i += 1
                    escaped = False
                    continue

                match line[i]:
                    case "\\":
                        escaped = True
                    case "%":
                        m = matching_perc(line, i)
                        if m != -1:
                            # we now have a sub-section. But there might be more %-sections!
                            # so, we recurse...
                            recursed = self.var_subst(line[i+1:m])
                            # now confident that all nested variables are evaluated...
                            out += self.eval_var(recursed)
                            i = m + 1
                            continue
                    case _:
                        out += line[i]

                i += 1

        except IndexError:
            return out

    def process_eval(self, cmd: str):
        args = cmd.split(" ", 2)

        if len(args) != 3:
            self.script_log(f"eval w/o an arg: {args}")
            return

        self.db.vars[args[1]] = self.eval_expr(args[2])

    def extract_value(self, cmd: str):
        pass

    def dg_letter_value(self, cmd: str):
        pass

    def makeuid_var(self, cmd: str):
        pass

    def do_dg_cast(self, cmd: str):
        pass

    def do_dg_affect(self, cmd: str):
        pass

    def cmd_global(self, cmd: str):
        pass

    def cmd_context(self, cmd: str):
        pass

    def cmd_rdelete(self, cmd: str):
        args = cmd.split()
        if len(args) < 2:
            self.script_log(f"rdelete with improper arg: {cmd}")
            return
        if args[1] not in self.db.vars:
            self.script_log(f"rdelete missing target var: {cmd}")
            return
        if not (target := self.handler.owner.search(args[2], use_dbref=True)):
            self.script_log(f"rdelete target not found: {cmd}")
            return
        #target.dgscripts.vars
        target.dgscripts.vars[self.context].pop(args[1])
        target.dgscripts.save()

    def cmd_remote(self, cmd: str):
        args = cmd.split()
        if len(args) < 2:
            self.script_log(f"remote with improper arg: {cmd}")
            return
        if args[1] not in self.db.vars:
            self.script_log(f"remote missing local var: {cmd}")
            return
        if not (target := self.handler.owner.search(args[2], use_dbref=True)):
            self.script_log(f"remote target not found: {cmd}")
            return
        target.dgscripts.vars[self.context][args[1]] = self.db.vars[args[1]]
        target.dgscripts.save()

    def cmd_set(self, cmd: str):
        args = cmd.split()
        if len(args) < 2:
            self.script_log(f"set with improper arg: {cmd}")
            return
        if len(args) < 3:
            args.append("")
        self.db.vars[args[1]] = args[2]

    def cmd_unset(self, cmd: str):
        args = cmd.split()
        if len(args) != 2:
            self.script_log(f"unset with improper arg: {cmd}")
            return
        self.db.vars.pop(args[1], None)

    def cmd_wait(self, cmd: str):
        args = cmd.split()
        if len(args) < 2:
            args.append("1")

        if not args[1].isnumeric():
            self.script_log(f"wait with improper arg: {args}")
            return 0

        if len(args) < 3:
            args.append("s")

        match args[2].lower():
            case "s" | "sec" | "second" | "seconds":
                return float(args[1])
            case _:
                return float(args[1])

    def cmd_detach(self, cmd: str):
        pass

    def cmd_attach(self, cmd: str):
        pass


class DGHandler:
    """
    Handler that's meant to be attached to an Athanor Object.
    """
    check_random: tuple[str] = ()

    def __init__(self, owner):
        self.owner = owner
        self.scripts: dict[str, DGScriptInstance] = dict()
        self.vars: dict[int, dict[str, str]] = defaultdict(dict)
        self.load()

    def load(self):
        for s in self.owner.scripts.all():
            if not s.tags.get(category="dgscript"):
                continue
            self.scripts[s.proto_key] = s

    def ids(self):
        return self.scripts.keys()

    def all(self):
        return self.scripts.values()

    def attach(self, script_id: typing.Union[int, str]):
        if isinstance(script_id, int):
            script_id = f"dg_script_{script_id}"
        if script_id in self.scripts:
            return

        if (dg := DgScriptPrototype.objects.filter_family(db_key=script_id).first()):
            new_dg, err = DGScriptInstance.create(key=f"Instance: {script_id} on {self.owner.dbref}", obj=self.owner,
                                                  persistent=True, interval=0.1, autostart=False)
            if err:
                return
            new_dg.tags.add(category="dgscript", key=script_id)
            new_dg.db.proto = dg
            new_dg.reset()
            self.scripts[script_id] = new_dg

    def detach(self, script_id):
        if (script := self.scripts.pop(script_id, None)):
            script.delete()

    def get_ready(self, trig_type: str):
        ready = list()
        for v in self.all():
            if v.db.state == DGState.DORMANT and trig_type in v.types():
                ready.append(v)
        return ready

    def trigger(self, trig_type, **kwargs):
        results = []
        for v in self.get_ready(trig_type):
            if trig_type in self.check_random:
                if randint(1, 100) > v.proto.narg:
                    continue
            v.db.vars.update(kwargs)
            results.append(v.execute())
        return results

    func_map = {
        "align": "alignment",
        "affects": "affected_flags",
        "affect": "affected_flags",
        "plr": "player_flags",
        "pref": "preference_flags",
    }

    def eval_func(self, script, member: str = "", call: bool = False, arg: str = "") -> tuple[bool, typing.Optional[str]]:

        member = self.func_map.get(member.lower(), member).lower()

        match member:
            case "vnum":
                return True, str(self.owner.attributes.get(key=member, default=-1))
            case "name":
                return True, self.owner.get_display_name(looker=script.obj)
            case "is_pc":
                return True, str(int(getattr(self.owner, "is_player", False)))
            case "alignment":
                if call and arg:
                    pass
                return True, str(self.owner.stats.get_effective(member))
            case "affected_flags" | "extra_flags" | "wear_flags" | "room_flags" | "player_flags":
                if call and arg:
                    return True, str(int(bool(self.owner.tags.get(category=member, key=arg))))

        return False, None

    def evaluate(self, script: DGScriptInstance, member: str = "", call: bool = False, arg: str = "") -> str:
        was_func, result = self.eval_func(script, member=member.lower(), call=call, arg=arg if call else None)
        if was_func:
            return result
        return self.vars[script.db.context].get(member.lower(), "")


class DgHandlerCharacter(DGHandler):

    func_map = {
        "class": "sensei",
        "int": "intelligence",
        "str": "strength",
        "con": "constitution",
        "agi": "agility",
        "wis": "wisdom",
        "spd": "speed",
        "cha": "speed",
        "charisma": "speed",
        "gold": "money",
        "zenni": "gold",
        "mana": "ki",
        "maxmana": "maxki",
        "gender": "sex",
        "move": "stamina"
    }

    def eval_func(self, script, member: str = "", call: bool = False, arg: str = "") -> tuple[bool, typing.Optional[str]]:
        was_func, result = super().eval_func(script, member=member, call=call, arg=arg)
        if was_func:
            return was_func, result

        member = self.func_map.get(member.lower(), member).lower()

        match member:
            case "race" | "sensei":
                return True, self.owner.aspects.get_aspect(member).get_name()
            case "strength" | "intelligence" | "constitution" | "agility" | "wisdom" | "speed":
                if call and arg:
                    pass  # Todo: coerce arg to int and call modify on stat...
                return True, str(self.owner.stats.get_effective(member))

        return False, None


def stat_get_set(obj, script, field, handler, arg: str) -> str:
    """
    Util function to make writing dgfuncs easier.
    """
    if arg:
        try:
            getattr(obj, handler).mod(int(arg))
        except (ValueError, TypeError):
            script.script_log(f"invalid arg for {field}: {arg}")
    return str(getattr(obj, handler).effective())

"""
class DGCommand(Command):

    def func(self):
        if (found := self.obj.dgscripts.scripts.get(self.script_id, None)):
            if found.state == DGState.DORMANT:
                found.vars["actor"] = self.caller
                found.vars["arg"] = self.args.strip()
                found.vars["cmd"] = self.cmdstring
                found.execute()
"""