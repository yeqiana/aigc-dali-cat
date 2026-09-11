# -*- coding: utf-8 -*-
import ast, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for fn in ["episodes/_system/image_scheduler.py", "episodes/_system/scheduler_core.py"]:
    src = open(fn, encoding="utf-8").read()
    t = ast.parse(src)
    lines = src.splitlines()
    for node in ast.walk(t):
        if isinstance(node, ast.FunctionDef) and node.name in ("cmd_add", "cmd_run", "add_item", "run_ready_items", "_ready_items", "pending_items", "claim_budget"):
            print("#####", fn, node.name, node.lineno, "-", node.end_lineno)
            for i in range(node.lineno - 1, min(node.end_lineno, node.lineno - 1 + 90)):
                print(lines[i])
            print()
