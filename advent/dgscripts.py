import typing
from enum import IntEnum
from advent.db.legacy.models import DgScript
from .exceptions import DgScriptError
from evennia.utils.ansi import strip_ansi
import operator as o


class DgState(IntEnum):
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
    try:
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
            current += 1

    except IndexError:
        return -1


def matching_paren(src: str, start: int) -> int:
    try:
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
            current += 1

    except IndexError:
        return -1


class DgScriptInstance:

    def __init__(self, handler, proto: DgScript):
        self.handler = handler
        self.proto = proto
        self.state = DgState.DORMANT
        self.wait_time = 0.0
        self.curr_line = 0
        self.depth: list[tuple[Nest, int]] = list()
        self.loops = 0
        self.total_loops = 0
        self.vars: dict[str, str] = dict()

    def script_log(self, msg: str):
        pass

    def execute(self) -> int:
        try:
            match self.state:
                case DgState.RUNNING | DgState.ERROR | DgState.DONE | DgState.PURGED:
                    raise DgScriptError(f"script called in invalid state {self.state.name}")
            if not len(self.proto.lines):
                raise DgScriptError("script has no lines to execute")
            self.state = DgState.RUNNING
            return self.execute_block(self.curr_line, len(self.proto.lines))
        except DgScriptError as err:
            self.state = DgState.ERROR
            self.script_log(f"{err} - {self.proto.id} - Line {self.curr_line+1}")
            return 0

    def execute_block(self, start: int, end: int) -> int:

        self.curr_line = start

        while self.curr_line < end:

            if self.loops == 50:
                # this has run long enough, let's pause it.
                self.state = DgState.WAITING
                self.wait_time = 1.0
                self.loops = 0
                return 0

            self.loops += 1
            self.total_loops += 1

            if self.total_loops > 2000:
                raise DgScriptError("Runaway Script Halted")

            line = self.get_line(self.curr_line)
            if not line or line.startswith("*"):
                self.curr_line += 1
                continue

            # cover if
            elif line.startswith("if "):
                self.depth.append((Nest.IF, self.curr_line))
                if not self.process_if(line[3:]):
                    self.curr_line = self.find_else_end()
                    continue
            elif line.startswith("elseif "):
                if not self.depth or self.depth[-1][0] != Nest.IF:
                    raise DgScriptError("'elseif' outside of an if block")
                if not self.process_if(line[7:]):
                    self.curr_line = self.find_else_end()
                    continue
            elif line == "else" or line.startswith("else "):
                if not self.depth or self.depth[-1][0] != Nest.IF:
                    raise DgScriptError("'else' outside of an if block")
                continue
            elif line == "end" or line.startswith("end "):
                if not self.depth or self.depth[-1][0] != Nest.IF:
                    raise DgScriptError("'end' outside of an if block")
                self.depth.pop()
                continue

            # cover while
            elif line.startswith("while "):
                self.depth.append((Nest.WHILE, self.curr_line))
                if not self.process_if(line[6:]):
                    self.curr_line = self.find_done()
                    continue

            # cover switch
            elif line.startswith("switch "):
                self.depth.append((Nest.SWITCH, self.curr_line))
                self.curr_line = self.find_case(line[7:])
                continue

            elif line == "break" or line.startswith("break "):
                if not self.depth or self.depth[-1][0] != Nest.SWITCH:
                    raise DgScriptError("'break' outside of a switch-case block")
                self.curr_line = self.find_done()
                continue

            elif line.startswith("case "):
                if not self.depth or self.depth[-1][0] != Nest.SWITCH:
                    raise DgScriptError("'break' outside of a switch-case block")
                # Fall through behavior mimicking C switch
                continue

            elif line == "done" or line.startswith("done "):
                if not self.depth:
                    raise DgScriptError("'done' outside of a switch-case or while block")
                match self.depth[-1][0]:
                    case Nest.SWITCH:
                        # Rewind back to the while clause.
                        self.curr_line = self.depth[-1][1]
                        continue
                    case Nest.WHILE:
                        pass
                    case _:
                        raise DgScriptError("'done' outside of a switch-case or while block")

            else:

                sub_cmd = self.var_subst(line)
                cmd_split = sub_cmd.split(" ", 1)
                cmd = cmd_split[0]

                match cmd:
                    case "nop":
                        # Do nothing.
                        pass
                    case "return":
                        pass
                    case "wait":
                        pass
                    case _:
                        if (func := getattr(self, f"cmd_{cmd}", None)):
                            func(*cmd_split)
                        else:
                            self.handler.owner.execute_cmd(sub_cmd)

            self.curr_line += 1


    def truthy(self, value: str) -> bool:
        if not value:
            return False
        return value != "0"

    def process_if(self, cond: str) -> bool:
        return self.truthy(self.eval_expr(cond).strip())

    def eval_expr(self, line: str) -> str:
        trimmed = strip_ansi(line.strip())

        if (result := self.eval_lhs_op_rhs(trimmed)):
            return result
        elif trimmed.startswith("("):
            m = matching_paren(trimmed, 0)
            if m != 1:
                return self.eval_expr(trimmed[1:m-1])
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
        "!": o.not_
    }

    def eval_lhs_op_rhs(self, expr: str) -> typing.Optional[str]:

        for op in self.ops_map.keys():
            try:
                lhs, rhs = expr.split(op, 1)
                lhr = self.eval_expr(lhs)
                rhr = self.eval_expr(rhs)
                return self.eval_op(op, lhr, rhr)
            except ValueError:
                continue

    def eval_op(self, op: str, lhs: str, rhs: str) -> str:
        op_found = self.ops_map[op]
        if lhs.isnumeric() and rhs.isnumeric():
            a = int(lhs)
            b = int(rhs)
            return str(op_found(a, b))
        else:
            match op:
                case "&&":
                    return str(int(self.truthy(lhs) and self.truthy(rhs)))
                case "==" | "!=":
                    return str(int(op_found(lhs, rhs)))
                case "||":
                    return str(int(self.truthy(lhs) or self.truthy(rhs)))
                case _:
                    return "0"



    def find_replacement(self, v: str) -> str:
        pass

    def add_local_var(self, name: str, value: str):
        pass

    def get_line(self, i: int) -> str:
        return self.proto.lines[i].lower().trim()

    def find_else_end(self, match_elseif: bool = True, match_else: bool = True) -> int:
        if not self.depth or self.depth[-1][0] != Nest.IF:
            raise DgScriptError("find_end called outside of if! alert a codewiz!")

        i = self.depth[-1][1]
        total = len(self.proto.lines)
        while i < total:
            line = self.get_line(i)
            if not line or line.startswith("*"):
                pass

            elif match_elseif and line.startswith("elseif "):
                return i

            elif match_else and (line.startswith("else ") or line.startswith("else")):
                return i

            elif line.startswith("end"):
                return i

            elif line.startswith("if "):
                self.depth.append((Nest.IF, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("switch "):
                self.depth.append((Nest.SWITCH, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("while "):
                self.depth.append((Nest.WHILE, i))
                i = self.find_done()
                self.depth.pop()

            elif line == "default" or line.startswith("default "):
                raise DgScriptError("'default' outside of a switch-case block")

            elif line == "done" or line.startswith("done "):
                raise DgScriptError("'done' outside of a switch-case or while block")

            elif line == "case" or line.startswith("case "):
                raise DgScriptError("'case' outside of a switch-case block")

            i += 1

        raise DgScriptError("'if' without corresponding end")


    def find_end(self) -> int:
        return self.find_else_end(match_elseif=False, match_else=False)

    def find_done(self) -> int:
        if not self.depth or self.depth[-1][0] not in (Nest.SWITCH, Nest.WHILE):
            raise DgScriptError("find_done called outside of a switch-case or while block! alert a codewiz!")

        inside = self.depth[-1][0].name.capitalize()

        i = self.depth[-1][1]
        total = len(self.proto.lines)
        while i < total:
            line = self.get_line(i)
            if not line or line.startswith("*"):
                pass

            elif line.startswith("if "):
                self.depth.append((Nest.IF, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("switch "):
                self.depth.append((Nest.SWITCH, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("while "):
                self.depth.append((Nest.WHILE, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("elseif "):
                raise DgScriptError("'elseif' outside of an if block")

            elif line.startswith("else ") or line == "else":
                raise DgScriptError("'else' outside of an if block")

            elif line == "end" or line.startswith("end "):
                raise DgScriptError("'end' outside of an if block")

            elif line == "default" or line.startswith("default "):
                raise DgScriptError("'default' outside of a switch-case block")

            elif line == "done" or line.startswith("done "):
                return i

            i += 1
        raise DgScriptError(f"'{inside}' without corresponding done")

    def find_case(self, cond: str) -> int:
        if not self.depth or self.depth[-1][0] != Nest.SWITCH:
            raise DgScriptError("find_case called outside of if! alert a codewiz!")

        res = self.eval_expr(cond)

        i = self.depth[-1][1]
        total = len(self.proto.lines)
        while i < total:
            line = self.get_line(i)
            if not line or line.startswith("*"):
                pass

            if line.startswith("case ") and self.truthy(self.eval_op("==", res, line[5:])):
                return i

            elif line == "default" or line.startswith("default "):
                return i

            elif line.startswith("end"):
                return i

            elif line.startswith("if "):
                self.depth.append((Nest.IF, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("switch "):
                self.depth.append((Nest.SWITCH, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("while "):
                self.depth.append((Nest.WHILE, i))
                i = self.find_done()
                self.depth.pop()

            elif line.startswith("elseif "):
                raise DgScriptError("'elseif' outside of an if block")

            elif line.startswith("else ") or line == "else":
                raise DgScriptError("'else' outside of an if block")

            i += 1

        raise DgScriptError("'if' without corresponding end")

    def eval_var(self, varname: str, field: str, call: str, arg: str) -> str:
        pass

    def get_var(self, varname: str, context: int = -1) -> typing.Optional[str]:
        pass

    def var_subst(self, line: str) -> str:
        pass

    def process_eval(self, cmd: str):
        args = cmd.split(" ", 2)

        if len(args) != 3:
            self.script_log(f"eval w/o an arg: {cmd}")
            return

        self.vars[args[1]] = self.eval_expr(args[2])

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

    def process_global(self, cmd: str):
        pass

    def process_context(self, cmd: str):
        pass

    def process_rdelete(self, cmd: str):
        pass

    def process_return(self, cmd: str) -> int:
        pass

    def process_set(self, cmd: str):
        args = cmd.split(" ")
        if len(args) != 3:
            self.script_log(f"set with improper arg: {cmd}")
            return
        self.vars[args[1]] = args[2]

    def process_unset(self, cmd: str):
        args = cmd.split(" ")
        if len(args) != 2:
            self.script_log(f"unset with improper arg: {cmd}")
            return
        self.vars.pop(args[1], None)

    def process_wait(self, cmd: str):
        pass

    def process_detach(self, cmd: str):
        pass

    def process_attach(self, cmd: str):
        pass