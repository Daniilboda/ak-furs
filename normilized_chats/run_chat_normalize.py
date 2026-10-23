"""CLI: нормализация шапок чатов → normilized_chats/chats/ (исходный zip не меняется)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chat_normalize import normalize_from_dir, normalize_from_zip

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = Path(__file__).resolve().parent
DEFAULT_ZIP = ROOT / "docs" / "04_client_chats.zip"
DEFAULT_CATALOG = ROOT / "docs" / "03_catalog_prices_reference.xlsx"
DEFAULT_OUT = PACKAGE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Привести шапки чатов к канону (клиент/заказ — числа, менеджер — справочник). "
            "Пишет копии в --out-dir/chats; docs/ и исходный zip не изменяются."
        )
    )
    parser.add_argument("--zip", type=Path, default=None, help="Архив чатов (как в docs/)")
    parser.add_argument(
        "--chats-dir",
        type=Path,
        default=None,
        help="Папка с Cxxxx.txt или с подпапкой chats/ (вместо --zip)",
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if args.zip is not None and args.chats_dir is not None:
        print("укажите либо --zip, либо --chats-dir", file=sys.stderr)
        return 2
    if args.zip is None and args.chats_dir is None:
        args.zip = DEFAULT_ZIP

    if args.zip is not None:
        result = normalize_from_zip(args.zip, args.catalog, args.out_dir)
        source = args.zip
    else:
        result = normalize_from_dir(args.chats_dir, args.catalog, args.out_dir)
        source = args.chats_dir

    sample = next(iter(result.values())).splitlines()[0]
    print(f"source={source}")
    print(f"out={args.out_dir / 'chats'}")
    print(f"chats={len(result)}")
    print(f"sample_header={sample}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
