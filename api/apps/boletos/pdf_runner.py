"""Isolated PDF parser entrypoint. Never print diagnostics or input."""

import json
import resource
import sys
from dataclasses import asdict
from datetime import date


def main():
    limit = int(sys.argv[1])
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024, 128 * 1024))
    from apps.boletos.pdf import extrair_pdf

    result = asdict(extrair_pdf(sys.stdin.buffer.read(5 * 1024 * 1024 + 1)))
    print(
        json.dumps(
            result,
            default=lambda value: value.isoformat() if isinstance(value, date) else None,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
