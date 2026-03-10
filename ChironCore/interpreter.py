
from ChironAST import ChironAST
from ChironHooks import Chironhooks
from lazyValue import (LazyValue, LazyEnvironment, EvalTrace,
                        snapshot_value, snapshot_self_ref, _eval_expr)
import turtle

Release="Chiron v5.3"

def addContext(s):
    return str(s).strip().replace(":", "self.prg.")

class Interpreter:
    # Turtle program should not contain variable with names "ir", "pc", "t_screen"
    ir = None
    pc = None
    t_screen = None
    trtl = None

    def __init__(self, irHandler, params):
        self.ir = irHandler.ir
        self.cfg = irHandler.cfg
        self.pc = 0
        self.t_screen = turtle.getscreen()
        self.trtl = turtle.Turtle()
        self.trtl.shape("turtle")
        self.trtl.color("blue", "yellow")
        self.trtl.fillcolor("green")
        self.trtl.begin_fill()
        self.trtl.pensize(4)
        self.trtl.speed(1) # TODO: Make it user friendly

        if params is not None:
            self.args = params
        else:
            self.args = None

        turtle.title(Release)
        turtle.bgcolor("white")
        turtle.hideturtle()

    def handleAssignment(self, stmt,tgt):
        raise NotImplementedError('Assignments are not handled!')

    def handleCondition(self, stmt, tgt):
        raise NotImplementedError('Conditions are not handled!')

    def handleMove(self, stmt, tgt):
        raise NotImplementedError('Moves are not handled!')

    def handlePen(self, stmt, tgt):
        raise NotImplementedError('Pens are not handled!')

    def handleGotoCommand(self, stmt, tgt):
        raise NotImplementedError('Gotos are not handled!')

    def handleNoOpCommand(self, stmt, tgt):
        raise NotImplementedError('No-Ops are not handled!')

    def handlePauseCommand(self, stmt, tgt):
        raise NotImplementedError('No-Ops are not handled!')

    def sanityCheck(self, irInstr):
        stmt, tgt = irInstr
        # if not a condition command, rel. jump can't be anything but 1
        if not isinstance(stmt, ChironAST.ConditionCommand):
            if tgt != 1:
                raise ValueError("Improper relative jump for non-conditional instruction", str(stmt), tgt)
    
    def interpret(self):
        pass

    def initProgramContext(self, params):
        pass

class ProgramContext:
    pass


class EagerInterpreter(Interpreter):
    """
    Original exec-based eager interpreter
    """
    # Ref: https://realpython.com/beginners-guide-python-turtle
    cond_eval = None # used as a temporary variable within the embedded program interpreter
    prg = None

    def __init__(self, irHandler, params):
        super().__init__(irHandler, params)
        self.prg = ProgramContext()
        # Hooks Object:
        if self.args is not None and self.args.hooks:
            self.chironhook = Chironhooks.ConcreteChironHooks()
        self.pc = 0
        self.verbose = True

    def interpret(self):
        if self.verbose:
            print("PC:", self.pc)
        stmt, tgt = self.ir[self.pc]
        if self.verbose:
            print(" ", stmt, stmt.__class__.__name__, tgt)
        self.sanityCheck(self.ir[self.pc])

        if isinstance(stmt, ChironAST.AssignmentCommand):
            ntgt = self.handleAssignment(stmt, tgt)
        elif isinstance(stmt, ChironAST.ConditionCommand):
            ntgt = self.handleCondition(stmt, tgt)
        elif isinstance(stmt, ChironAST.MoveCommand):
            ntgt = self.handleMove(stmt, tgt)
        elif isinstance(stmt, ChironAST.PenCommand):
            ntgt = self.handlePen(stmt, tgt)
        elif isinstance(stmt, ChironAST.GotoCommand):
            ntgt = self.handleGotoCommand(stmt, tgt)
        elif isinstance(stmt, ChironAST.NoOpCommand):
            ntgt = self.handleNoOpCommand(stmt, tgt)
        elif isinstance(stmt, ChironAST.PauseCommand):
            ntgt = self.handlePauseCommand(stmt, tgt)
        else:
            raise NotImplementedError("Unknown instruction: %s, %s."%(type(stmt), stmt))

        # TODO: handle statement
        self.pc += ntgt

        if self.pc >= len(self.ir):
            # This is the ending of the interpreter.
            self.trtl.write("End, Press ESC", font=("Arial", 15, "bold"))
            if self.args is not None and self.args.hooks:
                self.chironhook.ChironEndHook(self)
            return True
        else:
            return False

    def initProgramContext(self, params):
        # This is the starting of the interpreter at setup stage.
        if self.args is not None and self.args.hooks:
            self.chironhook.ChironStartHook(self)
        self.trtl.write("Start", font=("Arial", 15, "bold"))
        for key,val in params.items():
            var = key.replace(":","")
            exec("setattr(self.prg,\"%s\",%s)" % (var, val))

    def handleAssignment(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Assignment:", stmt)
        lhs = str(stmt.lvar).replace(":", "")
        rhs = addContext(stmt.rexpr)
        exec("setattr(self.prg,\"%s\",%s)" % (lhs, rhs))
        return 1

    def handleCondition(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Condition:", stmt.cond)
        condstr = addContext(stmt)
        exec("self.cond_eval = %s" % condstr)
        return 1 if self.cond_eval else tgt

    def handleMove(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Move:", stmt.direction)
        exec("self.trtl.%s(%s)" % (stmt.direction, addContext(stmt.expr)))
        return 1

    def handleNoOpCommand(self, stmt, tgt):
        print("  No-Op Command")
        return 1

    def handlePen(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Pen:", stmt.status)
        exec("self.trtl.%s()" % stmt.status)
        return 1

    def handleGotoCommand(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Goto")
        exec("self.trtl.goto(%s, %s)" % (addContext(stmt.xcor),
                                          addContext(stmt.ycor)))
        return 1

    def handlePauseCommand(self, stmt, tgt):
        if self.verbose:
            print("  [Eager] Pause")
        import time; time.sleep(0.5)
        return 1


ConcreteInterpreter = EagerInterpreter   # backward compatibility alias


# Lazy Interpreter 
class LazyInterpreter(Interpreter):
    def __init__(self, irHandler, params):
        super().__init__(irHandler, params)
        self.env = LazyEnvironment()
        self._cond_result = None
        self.trace = None
        self.verbose = True

        if self.args is not None and getattr(self.args, "hooks", False):
            self.chironhook = Chironhooks.ConcreteChironHooks()

        self.pc = 0

    # helpers
    def _pen_down(self):
        try:
            return self.trtl.isdown()
        except Exception:
            return True

    def _force_expr(self, expr):
        return _eval_expr(expr, self.env.as_dict(), pen_down=self._pen_down(),
            trace=self.trace, pc=self.pc)

    # interpreter loop
    def interpret(self):
        if self.verbose:
            print("PC:", self.pc)

        stmt, tgt = self.ir[self.pc]

        if self.verbose:
            print(" ", stmt, stmt.__class__.__name__, tgt)

        self.sanityCheck(self.ir[self.pc])

        if isinstance(stmt, ChironAST.AssignmentCommand):
            ntgt = self.handleAssignment(stmt, tgt)
        elif isinstance(stmt, ChironAST.ConditionCommand):
            ntgt = self.handleCondition(stmt, tgt)
        elif isinstance(stmt, ChironAST.MoveCommand):
            ntgt = self.handleMove(stmt, tgt)
        elif isinstance(stmt, ChironAST.PenCommand):
            ntgt = self.handlePen(stmt, tgt)
        elif isinstance(stmt, ChironAST.GotoCommand):
            ntgt = self.handleGotoCommand(stmt, tgt)
        elif isinstance(stmt, ChironAST.NoOpCommand):
            ntgt = self.handleNoOpCommand(stmt, tgt)
        elif isinstance(stmt, ChironAST.PauseCommand):
            ntgt = self.handlePauseCommand(stmt, tgt)

        else:
            raise NotImplementedError(f"Unknown instruction: {type(stmt)}")

        self.pc += ntgt
        if self.pc >= len(self.ir):
            self.trtl.write("End, Press ESC", font=("Arial", 15, "bold"))

            if self.trace:
                self.trace.record(self.pc, "PROGRAM-END", "---")
            if self.args is not None and getattr(self.args, "hooks", False):
                self.chironhook.ChironEndHook(self)
            return True

        return False

    # program init
    def initProgramContext(self, params):
        if self.args is not None and getattr(self.args, "hooks", False):
            self.chironhook.ChironStartHook(self)

        self.trtl.write("Start", font=("Arial", 15, "bold"))

        for key, val in params.items():
            varname = key.lstrip(":")
            try:
                num_val = int(val) if float(val).is_integer() else float(val)
            except (TypeError, ValueError):
                num_val = val

            lv = LazyValue(ChironAST.Num(num_val))
            self.env.set(varname, lv)

            if self.verbose:
                print(f"  [Lazy] init param :{varname} = {num_val}")


    # assignment
    def handleAssignment(self, stmt, tgt):
        lhs_name = str(stmt.lvar).lstrip(":")
        rhs_expr = stmt.rexpr

        if self.verbose:
            print(f"  [Lazy] Assignment: :{lhs_name} = {rhs_expr}")

        is_counter = lhs_name.startswith("__rep_counter_")
        if is_counter:
            val = self._force_expr(rhs_expr)
            lv = LazyValue(ChironAST.Num(val))
            self.env.set(lhs_name, lv)

            if self.verbose:
                print(f"    → counter immediate value: {val}")
            return 1

        if lhs_name in self.env:
            rhs_expr = snapshot_self_ref(lhs_name, rhs_expr, self.env)

        lv = snapshot_value(rhs_expr, self.env.as_dict(),
                            pen_down=self._pen_down(), lhs_name=lhs_name)

        self.env.set(lhs_name, lv)
        if self.verbose:
            print(f"    → deferred as {lv!r}")

        if self.trace:
            self.trace.record(self.pc, "ASSIGN-DEFERRED", f":{lhs_name} = {rhs_expr}")

        return 1

    # condition
    def handleCondition(self, stmt, tgt):
        cond = stmt.cond

        if self.verbose:
            if isinstance(cond, ChironAST.AND):
                print("  [Lazy] Condition (AND):", cond)
            elif isinstance(cond, ChironAST.OR):
                print("  [Lazy] Condition (OR):", cond)
            else:
                print("  [Lazy] Condition:", cond)

        if isinstance(cond, ChironAST.BoolFalse):
            return tgt

        result = _eval_expr(cond, self.env.as_dict(), pen_down=self._pen_down(),
            trace=self.trace, pc=self.pc)

        if self.verbose:
            print(f"    → condition result: {result}")

        self._cond_result = result

        return 1 if result else tgt

    # move commands
    def handleMove(self, stmt, tgt):
        if self.verbose:
            print(f"  [Lazy] Move: {stmt.direction}")
        value = self._force_expr(stmt.expr)

        if self.verbose:
            print(f"    → forced value: {value}")

        if self.trace:
            self.trace.record(self.pc, "MOVE-FORCE", f"{stmt.direction}({stmt.expr})={value}")

        getattr(self.trtl, stmt.direction)(value)
        return 1

    # pen commands
    def handlePen(self, stmt, tgt):
        if self.verbose:
            print(f"  [Lazy] Pen: {stmt.status}")

        getattr(self.trtl, stmt.status)()
        return 1

    # goto command
    def handleGotoCommand(self, stmt, tgt):
        if self.verbose:
            print("  [Lazy] Goto")

        xcor = self._force_expr(stmt.xcor)
        ycor = self._force_expr(stmt.ycor)
        if self.verbose:
            print(f"    → goto({xcor}, {ycor})")

        self.trtl.goto(xcor, ycor)
        return 1

    # misc commands
    def handleNoOpCommand(self, stmt, tgt):
        return 1

    def handlePauseCommand(self, stmt, tgt):
        if self.verbose:
            print("  [Lazy] Pause")

        import time
        time.sleep(0.5)
        return 1