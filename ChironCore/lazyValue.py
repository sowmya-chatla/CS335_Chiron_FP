from ChironAST import ChironAST

# evaluation trace
class EvalTrace:
    def __init__(self):
        self._events = []

    def record(self, pc, label, expr_str):
        self._events.append((pc, label, str(expr_str)))

    def report(self):
        print(f"\n=== EvalTrace ({len(self._events)} events) ===")
        for pc, label, expr in self._events:
            pc_str = str(pc) if pc is not None else "?"
            print(f"  PC{pc_str:<3}  {label:<20}  {expr}")
        print()

    def count(self):
        return len(self._events)

    def events(self):
        return list(self._events)

    def clear(self):
        self._events.clear()


# lazy wrapper
class LazyValue:
    def __init__(self, expr):
        if not isinstance(expr, ChironAST.AST):
            raise TypeError(f"LazyValue requires AST node, got {type(expr)}")
        self._expr = expr
        self._evaluated = False
        self._cache = None

    # force evaluation
    def force(self, env, pen_down=True, trace=None, pc=None):
        if not self._evaluated:
            if trace:
                trace.record(pc, "FORCE", self._expr)

            print(f"    [Memo] COMPUTING  {self._expr}  (first use)")
            self._cache = _eval_expr(self._expr, env, pen_down=pen_down, trace=trace,
            pc=pc)

            print(f"    [Memo] STORED     {self._expr}  =  {self._cache}")

            self._evaluated = True

        else:
            print(f"    [Memo] CACHE HIT  {self._expr}  =  {self._cache}  (reused)")

        return self._cache

    def is_evaluated(self):
        return self._evaluated

    def invalidate(self):
        self._evaluated = False
        self._cache = None

    def __repr__(self):
        if self._evaluated:
            return f"LazyValue(cached={self._cache!r})"
        return f"LazyValue(expr={self._expr})"


# recursive evaluator
def _eval_expr(expr, env, pen_down=True, trace=None, pc=None):

    if isinstance(expr, ChironAST.Num):
        return expr.val

    if isinstance(expr, ChironAST.Var):
        varname = expr.varname.lstrip(":")
        if varname not in env:
            raise NameError(f"Undefined variable '{expr.varname}'")

        val = env[varname]
        if isinstance(val, LazyValue):
            return val.force(env, pen_down=pen_down, trace=trace, pc=pc)

        return val

    # unary minus
    if isinstance(expr, ChironAST.UMinus):
        return -_eval_expr(expr.expr, env, pen_down, trace, pc)

    # arithmetic ops
    if isinstance(expr, ChironAST.Sum):
        return ( _eval_expr(expr.lexpr, env, pen_down, trace, pc)
            + _eval_expr(expr.rexpr, env, pen_down, trace, pc)
        )

    if isinstance(expr, ChironAST.Diff):
        return ( _eval_expr(expr.lexpr, env, pen_down, trace, pc)
            - _eval_expr(expr.rexpr, env, pen_down, trace, pc)
        )

    if isinstance(expr, ChironAST.Mult):
        return ( _eval_expr(expr.lexpr, env, pen_down, trace, pc)
            * _eval_expr(expr.rexpr, env, pen_down, trace, pc)
        )

    if isinstance(expr, ChironAST.Div):
        divisor = _eval_expr(expr.rexpr, env, pen_down, trace, pc)

        if divisor == 0:
            raise ZeroDivisionError(f"Division by zero in {expr}")

        return ( _eval_expr(expr.lexpr, env, pen_down, trace, pc)
            / divisor
        )

    # boolean constants
    if isinstance(expr, ChironAST.BoolTrue):
        return True

    if isinstance(expr, ChironAST.BoolFalse):
        return False

    # turtle pen state
    if isinstance(expr, ChironAST.PenStatus):
        return pen_down

    # comparisons
    if isinstance(expr, ChironAST.GT):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) > \
            _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    if isinstance(expr, ChironAST.LT):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) < \
            _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    if isinstance(expr, ChironAST.GTE):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) >= \
            _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    if isinstance(expr, ChironAST.LTE):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) <= \
             _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    if isinstance(expr, ChironAST.EQ):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) == \
            _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    if isinstance(expr, ChironAST.NEQ):
        return _eval_expr(expr.lexpr, env, pen_down, trace, pc) != \
            _eval_expr(expr.rexpr, env, pen_down, trace, pc)

    # short-circuit AND
    if isinstance(expr, ChironAST.AND):
        print(f"    [Short-circuit] AND LEFT → {expr.lexpr}")

        if trace:
            trace.record(pc, "EVAL-AND-left", expr.lexpr)
        left = _eval_expr(expr.lexpr, env, pen_down, trace, pc)

        print(f"    [Short-circuit] AND LEFT result = {left}")

        if not left:
            print(f"    [Short-circuit] AND RIGHT SKIPPED → {expr.rexpr}")
            if trace:
                trace.record(pc, "SHORT-CIRCUIT-AND", "right skipped")
            return False

        if trace:
            trace.record(pc, "EVAL-AND-right", expr.rexpr)

        right = bool(_eval_expr(expr.rexpr, env, pen_down, trace, pc))
        print(f"    [Short-circuit] AND RIGHT result = {right}")
        return right

    # short-circuit OR
    if isinstance(expr, ChironAST.OR):
        print(f"    [Short-circuit] OR LEFT → {expr.lexpr}")

        if trace:
            trace.record(pc, "EVAL-OR-left", expr.lexpr)
        left = _eval_expr(expr.lexpr, env, pen_down, trace, pc)

        print(f"    [Short-circuit] OR LEFT result = {left}")

        if left:
            print(f"    [Short-circuit] OR RIGHT SKIPPED → {expr.rexpr}")
            if trace:
                trace.record(pc, "SHORT-CIRCUIT-OR", "right skipped")
            return True

        if trace:
            trace.record(pc, "EVAL-OR-right", expr.rexpr)

        right = bool(_eval_expr(expr.rexpr, env, pen_down, trace, pc))
        print(f"    [Short-circuit] OR RIGHT result = {right}")
        return right

    if isinstance(expr, ChironAST.NOT):
        return not _eval_expr(expr.expr, env, pen_down, trace, pc)

    raise NotImplementedError(
        f"Unsupported expression type {type(expr)}"
    )


# snapshot semantics
def snapshot_value(rhs_expr, env, pen_down=True, lhs_name=None):

    if isinstance(rhs_expr, ChironAST.Var):
        varname = rhs_expr.varname.lstrip(":")

        if varname in env:
            val = env[varname]

            evaluated = (
                val.force(env, pen_down=pen_down)
                if isinstance(val, LazyValue)
                else val
            )

            frozen = int(evaluated) if (
                isinstance(evaluated, float)
                and float(evaluated).is_integer()
            ) else evaluated

            lhs_label = f":{lhs_name}" if lhs_name else "var"

            print(f"    [Snapshot] {lhs_label} = :{varname} → current value {frozen}")
            print(f"    [Snapshot] Freezing {lhs_label} as {frozen}")

            return LazyValue(ChironAST.Num(frozen))

    return LazyValue(rhs_expr)


# self reference fix
def snapshot_self_ref(lhs_name, expr, env):

    if isinstance(expr, ChironAST.Num):
        return expr

    if isinstance(expr, ChironAST.Var):
        if expr.varname.lstrip(":") == lhs_name:
            return ChironAST.Num(env.force(lhs_name))
        return expr

    if isinstance(expr, ChironAST.UMinus):
        return ChironAST.UMinus(
            snapshot_self_ref(lhs_name, expr.expr, env)
        )

    for cls in (ChironAST.Sum, ChironAST.Diff, ChironAST.Mult, ChironAST.Div,
                ChironAST.AND, ChironAST.OR, ChironAST.GT, ChironAST.LT,
                ChironAST.GTE, ChironAST.LTE, ChironAST.EQ, ChironAST.NEQ):

        if isinstance(expr, cls):
            return cls(snapshot_self_ref(lhs_name, expr.lexpr, env),
                snapshot_self_ref(lhs_name, expr.rexpr, env)
            )

    if isinstance(expr, ChironAST.NOT):
        return ChironAST.NOT(snapshot_self_ref(lhs_name, expr.expr, env))

    return expr


# lazy environment
class LazyEnvironment:

    def __init__(self):
        self._store = {}

    def set(self, varname, lazy_val):
        assert isinstance(lazy_val, LazyValue), \
            f"Expected LazyValue, got {type(lazy_val)}"

        self._store[varname] = lazy_val

    def force(self, varname, pen_down=True, trace=None, pc=None):

        if varname not in self._store:
            raise NameError(f"Undefined variable :{varname}")

        return self._store[varname].force(self._store, pen_down=pen_down,
                                         trace=trace, pc=pc)

    def as_dict(self):
        return self._store

    def __contains__(self, varname):
        return varname in self._store

    def __repr__(self):
        entries = ", ".join(
            f":{k}={v!r}" for k, v in self._store.items()
        )
        return f"LazyEnv{{{entries}}}"