#!/usr/bin/env python3
"""One-way, guarded MySQL Linux name-case compatibility copy, preserving source."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import platform
if not hasattr(platform, '__path__'):
    raise RuntimeError('PROJECT_PLATFORM_PACKAGE_REQUIRED')
import pymysql
MAIN = ROOT.parent.parent
SOURCE, TARGET = "story_os_runtime", "STORY_OS_RUNTIME"
ENV = MAIN / ".storyos/runtime-launcher/runtime.env"
BACKUP = MAIN / ".storyos/runtime-launcher/backups/story_os_runtime-precutover-20261009.sql.gz"
for module_root in (ROOT / "episodes" / "_system", ROOT / "scripts"):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))



def quote(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
        raise ValueError("UNSAFE_IDENTIFIER")
    return chr(96) + name + chr(96)


def definitions(steps):
    result = []
    for _, ddl in steps:
        if not ddl.startswith("CREATE TABLE"):
            continue
        name = re.search(r"CREATE TABLE IF NOT EXISTS\s+([A-Z][A-Z0-9_]+)", ddl).group(1)
        cols = []
        for line in ddl.split("(\n", 1)[1].split("\n)", 1)[0].splitlines():
            value = line.strip().rstrip(",")
            if not value or re.match(r"^(PRIMARY KEY|INDEX|UNIQUE|CONSTRAINT|FOREIGN KEY|KEY)\b", value, re.I):
                continue
            found = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s+", value)
            if found:
                cols.append(found.group(1))
        result.append((name, cols, ddl))
    return result


def rows(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def names(conn, schema):
    return {r["TABLE_NAME"] for r in rows(conn,
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'",
        (schema,))}


def columns(conn, schema, table):
    return [r["COLUMN_NAME"] for r in rows(conn,
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
        (schema, table))]


def validate_source(conn, defs):
    databases = {next(iter(r.values())) for r in rows(conn, "SHOW DATABASES")}
    if TARGET in databases or SOURCE not in databases:
        raise RuntimeError("TARGET_PRESENT_OR_SOURCE_MISSING")
    if rows(conn, "SELECT @@lower_case_table_names AS n")[0]["n"] != 0:
        raise RuntimeError("WRONG_CASE_MODE")
    expected = {n.lower() for n, _, _ in defs}
    existing = names(conn, SOURCE)
    if expected - existing or existing - expected != {"platform_latest_record"}:
        raise RuntimeError("TABLE_SET_MISMATCH")
    changed_order = []
    for table, wanted, _ in defs:
        found = columns(conn, SOURCE, table.lower())
        if {v.lower() for v in wanted} != {v.lower() for v in found}:
            raise RuntimeError("COLUMN_SET_MISMATCH:" + table)
        if [v.lower() for v in wanted] != [v.lower() for v in found]:
            changed_order.append(table)
    return changed_order


def fingerprint(conn, schema, table, fields):
    key = [r["COLUMN_NAME"] for r in rows(conn,
        "SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY' ORDER BY ORDINAL_POSITION",
        (schema, table))]
    if not key:
        raise RuntimeError("MISSING_PK:" + table)
    cols = ",".join(map(quote, fields))
    sort = ",".join(map(quote, key))
    result = rows(conn, "SELECT " + cols + " FROM " + quote(schema) + "." + quote(table) + " ORDER BY " + sort)
    digest = hashlib.sha256()
    for row in result:
        digest.update(json.dumps(row, default=str, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return len(result), digest.hexdigest()




def verify_review_shadow_advancement(conn):
    """Accept only the previously audited, narrow MySQL review supersession.

    Every other V2 table stays byte-for-byte equivalent by normalized columns.
    """
    key_sql = ("SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE "
               "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s "
               "AND CONSTRAINT_NAME='PRIMARY' ORDER BY ORDINAL_POSITION")
    keys = [row["COLUMN_NAME"] for row in rows(
        conn, key_sql, (TARGET, "TB_RUNTIME_REVIEW_REQUEST"))]
    if not keys:
        raise RuntimeError("SHADOW_PRIMARY_KEY_MISSING")
    source_rows = rows(conn, "SELECT * FROM " + quote(SOURCE) + "." + quote("tb_runtime_review_request"))
    target_rows = rows(conn, "SELECT * FROM " + quote(TARGET) + "." + quote("TB_RUNTIME_REVIEW_REQUEST"))
    source = {tuple(row[key] for key in keys): row for row in source_rows}
    target = {tuple(row[key] for key in keys): row for row in target_rows}
    if len(source) != len(source_rows) or len(target) != len(target_rows) or source.keys() != target.keys():
        raise RuntimeError("SHADOW_REVIEW_ROW_SET_DRIFT")
    accepted = 0
    for key, old in source.items():
        new = target[key]
        if old == new:
            continue
        changes = {field for field in old if old[field] != new.get(field)}
        if (changes != {"STATUS", "PAYLOAD", "UPDATE_TIME"}
                or old.get("REVIEW_KIND") != "story-semantic-critic-shadow"
                or new.get("REVIEW_KIND") != old["REVIEW_KIND"]
                or old.get("STATUS") != "AWAITING_PRODUCT_REVIEW"
                or new.get("STATUS") != "SUPERSEDED"):
            raise RuntimeError("UNEXPECTED_REVIEW_AUTHORITY_DRIFT")
        old_payload = json.loads(old["PAYLOAD"]) if isinstance(old["PAYLOAD"], (str, bytes)) else old["PAYLOAD"]
        new_payload = json.loads(new["PAYLOAD"]) if isinstance(new["PAYLOAD"], (str, bytes)) else new["PAYLOAD"]
        if (not isinstance(old_payload, dict) or not isinstance(new_payload, dict)
                or old_payload.get("status") != "AWAITING_PRODUCT_REVIEW"
                or new_payload.get("status") != "SUPERSEDED"
                or old_payload.get("request_id") != new_payload.get("request_id")
                or old_payload.get("projection_type") != "RUNTIME_REVIEW_REQUEST_REF"
                or new_payload.get("projection_type") != old_payload["projection_type"]
                or not re.fullmatch(r"[0-9a-f]{64}", str(new_payload.get("source_sha256") or ""))
                or not isinstance(new_payload.get("source_bytes"), int)
                or int(new_payload["source_bytes"]) <= 0
                or {k: v for k, v in old_payload.items()
                    if k not in {"status", "document", "source_sha256", "source_bytes"}}
                   != {k: v for k, v in new_payload.items()
                       if k not in {"status", "document", "source_sha256", "source_bytes"}}):
            raise RuntimeError("UNVERIFIED_SHADOW_PROJECTION_DRIFT")
        accepted += 1
    if accepted != 2:
        raise RuntimeError("SHADOW_SUPERSESSION_COUNT_MISMATCH")
    return accepted


def verify_casecopy(conn, defs, *, allow_shadow_advance=False):
    """Read-only, per-table primary-key-ordered content verification.

    Must be repeated after the old Runtime task stops, before cutover: a
    snapshot copy is not an ongoing replication channel.
    """
    databases = {next(iter(row.values())) for row in rows(conn, "SHOW DATABASES")}
    if {SOURCE, TARGET} - databases:
        raise RuntimeError("SOURCE_OR_TARGET_SCHEMA_MISSING")
    if int(rows(conn, "SELECT @@lower_case_table_names AS n")[0]["n"]) != 0:
        raise RuntimeError("WRONG_CASE_MODE")
    expected = {name for name, _, _ in defs}
    target_names = names(conn, TARGET)
    if target_names != expected:
        raise RuntimeError("V2_TARGET_TABLE_SET_MISMATCH")
    source_names = names(conn, SOURCE)
    if source_names != {name.lower() for name in expected} | {"platform_latest_record"}:
        raise RuntimeError("SOURCE_TABLE_SET_MISMATCH")
    results = []
    reconciled_reviews = 0
    for name, columns_expected, _ in defs:
        source_columns = columns(conn, SOURCE, name.lower())
        target_columns = columns(conn, TARGET, name)
        if ({col.lower() for col in source_columns} !=
                {col.lower() for col in columns_expected} or
                target_columns != columns_expected):
            raise RuntimeError("COLUMN_CONTRACT_DRIFT:" + name)
        source = fingerprint(conn, SOURCE, name.lower(), columns_expected)
        target = fingerprint(conn, TARGET, name, columns_expected)
        if source != target:
            if allow_shadow_advance and name == "TB_RUNTIME_REVIEW_REQUEST":
                reconciled_reviews = verify_review_shadow_advancement(conn)
                if source[0] != target[0]:
                    raise RuntimeError("REVIEW_ROW_COUNT_DRIFT")
            else:
                raise RuntimeError("SOURCE_TARGET_DIGEST_MISMATCH:" + name)
        results.append({"table": name, "rows": source[0]})
    return {
        "status": ("SOURCE_TARGET_VERIFIED_WITH_AUTHORIZED_SHADOW_ADVANCES"
                   if reconciled_reviews else "SOURCE_TARGET_VERIFIED"),
        "tables_verified": len(results),
        "total_rows": sum(item["rows"] for item in results),
        "source_target_sha256_match": reconciled_reviews == 0,
        "authorized_shadow_supersessions": reconciled_reviews,
        "read_only": True,
        "runtime_env_unchanged": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply", "verify"))
    parser.add_argument("--allow-shadow-advance", action="store_true",
                        help="Read-only allowlist: exactly two verified Shadow SUPERSEDED transitions")
    args = parser.parse_args()
    from phase9_runtime_launcher import load_runtime_env_file
    loaded, _ = load_runtime_env_file(ENV, dict(os.environ))
    os.environ.update(loaded)
    import storage_config
    from platform.repository.mysql.schema_v2 import DDL_STEPS, CREATE_DATABASE_SQL
    kwargs = storage_config.mysql_connection_kwargs({"database": "information_schema"})
    if str(kwargs["host"]) not in ("127.0.0.1", "localhost") or int(kwargs["port"]) != 3307:
        raise RuntimeError("REFUSE_NON_LOCAL_MYSQL")
    if not BACKUP.is_file():
        raise RuntimeError("MIGRATION_BACKUP_MISSING")
    raw_hash = hashlib.sha256()
    with BACKUP.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            raw_hash.update(block)
    uncompressed_bytes = 0
    with gzip.open(BACKUP, "rb") as compressed:
        for block in iter(lambda: compressed.read(1024 * 1024), b""):
            uncompressed_bytes += len(block)
    if uncompressed_bytes < 1024:
        raise RuntimeError("INVALID_BACKUP")
    if args.action == "apply":
        mapping = subprocess.run(["docker", "port", "mysql8.0", "3306"],
            check=True, capture_output=True, text=True, timeout=12)
        if "127.0.0.1:3307" not in mapping.stdout:
            raise RuntimeError("WRONG_DOCKER_CONTAINER")
    conn = pymysql.connect(**kwargs, autocommit=True, cursorclass=pymysql.cursors.DictCursor,
                           read_timeout=60, write_timeout=60)
    defs = definitions(DDL_STEPS)
    try:
        if args.action == "verify":
            print(json.dumps(verify_casecopy(conn, defs,
                allow_shadow_advance=args.allow_shadow_advance), ensure_ascii=False))
            return
        changed = validate_source(conn, defs)
        report = {"status": "PLAN_SAFE", "source_schema": SOURCE, "target_schema": TARGET,
                  "tables": len(defs), "column_reorder": changed,
                  "backup_verified": bool(raw_hash.hexdigest()), "source_unchanged": True}
        if args.action == "plan":
            print(json.dumps(report, ensure_ascii=False))
            return
        if rows(conn, "SELECT GET_LOCK(%s,0) AS acquired",
                ("storyos-v2-case-copy-local-3307",))[0]["acquired"] != 1:
            raise RuntimeError("CASECOPY_LOCK_HELD")
        try:
            validate_source(conn, defs)
            before = {n: fingerprint(conn, SOURCE, n.lower(), cols) for n, cols, _ in defs}
            with conn.cursor() as cursor:
                cursor.execute(CREATE_DATABASE_SQL)
            dest = pymysql.connect(**{**kwargs, "database": TARGET},
                 autocommit=True, cursorclass=pymysql.cursors.DictCursor,
                 read_timeout=60, write_timeout=60)
            try:
                for name, _, ddl in defs:
                    with dest.cursor() as cursor:
                        cursor.execute(ddl)
                for name, cols, _ in defs:
                    select_cols = ",".join(map(quote, cols))
                    sql = ("INSERT INTO " + quote(TARGET) + "." + quote(name)
                           + " (" + select_cols + ") SELECT " + select_cols
                           + " FROM " + quote(SOURCE) + "." + quote(name.lower()))
                    with dest.cursor() as cursor:
                        cursor.execute(sql)
                verified = 0
                total_rows = 0
                for name, cols, _ in defs:
                    old_now = fingerprint(conn, SOURCE, name.lower(), cols)
                    new_now = fingerprint(dest, TARGET, name, cols)
                    if before[name] != old_now or old_now != new_now:
                        raise RuntimeError("ROW_DIGEST_MISMATCH:" + name)
                    verified += 1
                    total_rows += new_now[0]
                report.update({"status": "COPY_VERIFIED", "tables_verified": verified,
                    "total_rows": total_rows, "source_and_target_sha256_match": True,
                    "source_unchanged": True, "runtime_env_unchanged": True})
                print(json.dumps(report, ensure_ascii=False))
            finally:
                dest.close()
        finally:
            rows(conn, "SELECT RELEASE_LOCK(%s)", ("storyos-v2-case-copy-local-3307",))
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "COPY_ABORTED", "reason_code": str(exc).split(":")[0],
                          "source_schema_preserved": True, "runtime_env_unchanged": True}))
        raise SystemExit(22)
