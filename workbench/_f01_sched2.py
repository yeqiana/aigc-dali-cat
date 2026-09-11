# -*- coding: utf-8 -*-
import ast, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
src = open(r"episodes/_system/image_scheduler.py", encoding="utf-8").read()
t = ast.parse(src)
lines = src.splitlines()
for node in ast.walk(t):
    if isinstance(node, ast.FunctionDef) and node.name in ("ready_items", "run_scheduler_async", "ledger_begin", "backend_worker", "ledger_success"):
        print("#####", node.name, node.lineno, "-", node.end_lineno)
        for i in range(node.lineno - 1, min(node.end_lineno, node.lineno - 1 + 100)):
            print(lines[i])
        print()
