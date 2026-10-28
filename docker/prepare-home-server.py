#!/usr/bin/env python3
"""Create local OpenCVE configuration without printing generated secrets."""

from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path
import secrets


ROOT = Path(__file__).resolve().parents[1]
DOCKER = ROOT / "docker"


def replace_values(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        key, separator, _ = line.partition("=")
        if separator and key in values:
            result.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            result.append(line)
    for key, value in values.items():
        if key not in seen:
            result.append(f"{key}={value}")
    path.write_text("\n".join(result) + "\n", encoding="utf-8")
    path.chmod(0o600)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing home-server configuration and rotate all secrets",
    )
    args = parser.parse_args()

    env_path = DOCKER / ".env"
    if (
        env_path.exists()
        and "OPENCVE_WEBSERVER_IMAGE=" in env_path.read_text(encoding="utf-8")
        and not args.force
    ):
        raise SystemExit(
            "Home-server configuration already exists; refusing to rotate secrets. "
            "Use --force only for an intentional, database-aware credential rotation."
        )
    env_path.write_text(
        (DOCKER / "conf" / ".env.home-server.example").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    postgres_password = secrets.token_urlsafe(32)
    airflow_password = secrets.token_urlsafe(24)
    fernet_key = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
    replace_values(
        env_path,
        {
            "POSTGRES_PASSWORD": postgres_password,
            "_AIRFLOW_WWW_USER_PASSWORD": airflow_password,
            "AIRFLOW__CORE__FERNET_KEY": fernet_key,
        },
    )

    web_env = ROOT / "web" / "opencve" / "conf" / ".env"
    replace_values(
        web_env,
        {
            "OPENCVE_DATABASE_URL": f"postgresql://opencve:{postgres_password}@postgres:5432/opencve",
            "OPENCVE_SECRET_KEY": secrets.token_urlsafe(64),
            "OPENCVE_WEB_BASE_URL": "http://192.168.178.57:8092",
        },
    )
    print("Home-server configuration created (secrets stored locally with mode 0600).")


if __name__ == "__main__":
    main()
