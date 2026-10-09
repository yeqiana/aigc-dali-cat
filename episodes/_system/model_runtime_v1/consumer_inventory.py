"""Read-only AST inventory of StoryOS callers that bypass the new model adapter.

Use this before changing legacy defaults or deleting provider routes.
"""
from __future__ import annotations
import ast
from pathlib import Path

METHODS={"run_codex", "execute_codex", "execute_task", "execute_model_task"}

def scan(root: str | Path) -> list[dict]:
    root=Path(root)
    system=root / "episodes" / "_system"
    found=[]
    for file in sorted(system.rglob("*.py")):
        if file.name=="codex_user_runner.py" or "model_runtime_v1" in file.parts:
            continue
        try:
            tree=ast.parse(file.read_text(encoding="utf-8-sig"),filename=str(file))
        except (SyntaxError,UnicodeError):
            continue
        aliases=set()
        direct={}
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for item in node.names:
                    if item.name=="codex_user_runner":
                        aliases.add(item.asname or item.name)
            elif isinstance(node,ast.ImportFrom) and node.module=="codex_user_runner":
                for item in node.names:
                    if item.name in METHODS:
                        direct[item.asname or item.name]=item.name
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call):
                continue
            method=None
            if (isinstance(node.func,ast.Attribute)
                and isinstance(node.func.value,ast.Name)
                and node.func.value.id in aliases and node.func.attr in METHODS):
                method=node.func.attr
            elif isinstance(node.func,ast.Name) and node.func.id in direct:
                method=direct[node.func.id]
            if method is not None:
                rel=file.relative_to(root).as_posix()
                found.append({"file":rel,"line":node.lineno,"entrypoint":method,
                              "migration_priority":("DIRECT_TASK_BYPASS" if method in {"execute_codex","execute_task"}
                              else "MIGRATED_ENTRYPOINT" if method=="execute_model_task"
                              else "FACADE_CALLER")})
    return sorted(found,key=lambda x:(x["file"],x["line"],x["entrypoint"]))
