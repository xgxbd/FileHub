import argparse
import os
from pathlib import Path

from sqlalchemy import bindparam, create_engine, text


def parse_args() -> argparse.Namespace:
    backend_dir = Path(__file__).resolve().parents[1]
    default_db_url = os.environ.get("DATABASE_URL", f"sqlite:///{(backend_dir / 'filehub.db').as_posix()}")

    parser = argparse.ArgumentParser(description="清理对象内容缺失的孤儿文件元数据")
    parser.add_argument("--database-url", default=default_db_url, help="数据库连接串")
    parser.add_argument("--dry-run", action="store_true", help="仅输出，不真正删除")
    return parser.parse_args()


def build_object_roots() -> list[Path]:
    backend_dir = Path(__file__).resolve().parents[1]
    repo_dir = backend_dir.parent
    roots = [
        backend_dir / "tmp" / "object_store",
        repo_dir / "tmp" / "object_store",
    ]

    deduped: list[Path] = []
    seen = set()
    for root in roots:
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)
    return deduped


def object_exists(*, roots: list[Path], object_key: str) -> bool:
    return any((root / object_key).exists() for root in roots)


def main() -> int:
    args = parse_args()
    roots = build_object_roots()
    engine = create_engine(args.database_url)

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, owner_id, file_name, object_key
                FROM file_objects
                WHERE is_deleted = 0
                ORDER BY id ASC
                """
            )
        ).mappings().all()

        orphan_rows = [row for row in rows if not object_exists(roots=roots, object_key=row["object_key"])]

        print(f"扫描活跃文件 {len(rows)} 条")
        print(f"发现孤儿文件 {len(orphan_rows)} 条")
        for row in orphan_rows[:50]:
            print(
                f"ORPHAN id={row['id']} owner_id={row['owner_id']} "
                f"file_name={row['file_name']} object_key={row['object_key']}"
            )

        if args.dry_run or not orphan_rows:
            return 0

        orphan_ids = [row["id"] for row in orphan_rows]
        conn.execute(
            text("DELETE FROM file_objects WHERE id IN :ids").bindparams(bindparam("ids", expanding=True)),
            {"ids": orphan_ids},
        )
        print(f"已删除孤儿文件元数据 {len(orphan_ids)} 条")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
