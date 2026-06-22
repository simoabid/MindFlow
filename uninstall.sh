#!/bin/bash
# uninstall.sh — Remove MindFlow IBus engine

set -e

echo "🗑️  Uninstalling MindFlow..."

# Remove IBus component
rm -f "$HOME/.local/share/ibus/component/mindflow.xml"

# Remove install directory
rm -rf "$HOME/.local/share/mindflow"

# Keep config (ask user)
read -p "Remove config directory ~/.config/mindflow? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.config/mindflow"
    echo "📝 Config removed."
fi

# Restart IBus
ibus restart 2>/dev/null || ibus-daemon -drx 2>/dev/null || true

echo "✅ MindFlow uninstalled."
