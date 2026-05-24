#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/root/NoBrainFog"
VENV_PYTHON="$REPO_DIR/.venv/bin/python"
CLI_SCRIPT="$REPO_DIR/tools/nbf_cli.py"
DEFAULT_ENV_FILE="/root/nobrainfog-config/cli.env"
INSTALL_DIR="$HOME/.local/bin"
COMMAND_PATH="$INSTALL_DIR/nbf"

if [ ! -d "$REPO_DIR" ]; then
  echo "❌ Repository directory not found: $REPO_DIR" >&2
  exit 1
fi

if [ ! -x "$VENV_PYTHON" ]; then
  echo "❌ Python virtualenv not found or not executable: $VENV_PYTHON" >&2
  echo "Run this first:" >&2
  echo "  cd $REPO_DIR" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  source .venv/bin/activate" >&2
  echo "  pip install -r requirements.txt" >&2
  exit 1
fi

if [ ! -f "$CLI_SCRIPT" ]; then
  echo "❌ CLI script not found: $CLI_SCRIPT" >&2
  exit 1
fi

if [ ! -f "$DEFAULT_ENV_FILE" ]; then
  echo "❌ CLI env file not found: $DEFAULT_ENV_FILE" >&2
  echo "Create it from cli.env.example or copy compatible values from discord.env." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"

cat > "$COMMAND_PATH" <<EOF
#!/usr/bin/env bash
exec "$VENV_PYTHON" "$CLI_SCRIPT" --env-file "$DEFAULT_ENV_FILE" "\$@"
EOF

chmod +x "$COMMAND_PATH"

echo "✅ Installed NoBrainFog CLI command: $COMMAND_PATH"

case ":$PATH:" in
  *":$INSTALL_DIR:"*)
    echo "✅ $INSTALL_DIR is already in PATH"
    ;;
  *)
    echo "⚠️  $INSTALL_DIR is not currently in PATH."
    echo "Add this to ~/.bashrc if needed:"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    ;;
esac

echo
"$COMMAND_PATH" help
