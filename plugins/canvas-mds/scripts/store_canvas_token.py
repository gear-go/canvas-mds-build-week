from __future__ import annotations

import argparse
import getpass
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guardar un token Canvas en el keyring sin mostrarlo ni escribirlo en archivos."
    )
    parser.add_argument("--service", default="canvas-docencia-mds")
    parser.add_argument("--account", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        import keyring  # type: ignore
    except ImportError:
        print(
            "ERROR: falta keyring. Instalarlo o usar la variable temporal CANVAS_API_TOKEN.",
            file=sys.stderr,
        )
        return 1
    token = getpass.getpass("Token Canvas (entrada oculta): ").strip()
    if len(token) < 20:
        print("ERROR: el valor no parece un token Canvas válido.", file=sys.stderr)
        return 1
    confirmation = getpass.getpass("Repetir token: ").strip()
    if token != confirmation:
        print("ERROR: los valores no coinciden.", file=sys.stderr)
        return 1
    keyring.set_password(args.service, args.account, token)
    print(f"Token almacenado en keyring: servicio={args.service}, cuenta={args.account}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

