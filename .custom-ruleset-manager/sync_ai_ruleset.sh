#!/bin/bash
set -euo pipefail

# -----------------------------
# sync_ai_ruleset.sh
# Syncs AI rules from private template repo
# Requires SSH access to private template
# Safe to run multiple times
# Never touches: AI_RULES.md, PROJECT_SPECIFIC.md
# -----------------------------

TEMPLATE_REPO="git@github.com:csh-1997-eng/ai-base-repo-template.git"  # ⚠️ UPDATE THIS
TEMP_DIR=$(mktemp -d)

# Cleanup on exit
trap 'rm -rf "$TEMP_DIR"' EXIT

echo ""
echo "📥 Syncing AI Rules from Private Template"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Clone private template (requires SSH key)
echo "🔐 Cloning template repo (requires SSH access)..."
if ! git clone --depth 1 "$TEMPLATE_REPO" "$TEMP_DIR" 2>/dev/null; then
  echo ""
  echo "❌ ERROR: Could not clone template repo."
  echo ""
  echo "Possible reasons:"
  echo "  1. You don't have SSH access to the private template repo"
  echo "  2. SSH key not configured (run: ssh -T git@github.com)"
  echo "  3. Wrong repository URL (check TEMPLATE_REPO in this script)"
  echo ""
  exit 1
fi

echo "✅ Template cloned"
echo ""

# Create directories if they don't exist
mkdir -p rules/skills .cursor/rules .custom-ruleset-manager

# Sync files from template
echo "🔄 Syncing files..."

# 1. Sync BASE_RULES.md (always overwrite)
if [[ -f "$TEMP_DIR/rules/BASE_RULES.md" ]]; then
  cp "$TEMP_DIR/rules/BASE_RULES.md" "./rules/"
  echo "   ✓ rules/BASE_RULES.md"
fi

# 2. Sync skills (always overwrite)
if [[ -d "$TEMP_DIR/rules/skills" ]]; then
  rsync -a --delete "$TEMP_DIR/rules/skills/" "./rules/skills/"
  echo "   ✓ rules/skills/"
fi

# 3. Sync Cursor rules (always overwrite)
if [[ -d "$TEMP_DIR/.cursor/rules" ]]; then
  rsync -a --delete "$TEMP_DIR/.cursor/rules/" "./.cursor/rules/"
  echo "   ✓ .cursor/rules/"
fi

# 4. Sync entrypoint files (always overwrite)
if [[ -f "$TEMP_DIR/CLAUDE.md" ]]; then
  cp "$TEMP_DIR/CLAUDE.md" "./"
  echo "   ✓ CLAUDE.md"
fi

if [[ -f "$TEMP_DIR/AGENTS.md" ]]; then
  cp "$TEMP_DIR/AGENTS.md" "./"
  echo "   ✓ AGENTS.md"
fi

# 5. Sync this script itself (so it can be updated)
if [[ -f "$TEMP_DIR/.custom-ruleset-manager/sync_ai_ruleset.sh" ]]; then
  cp "$TEMP_DIR/.custom-ruleset-manager/sync_ai_ruleset.sh" "./.custom-ruleset-manager/"
  chmod +x ./.custom-ruleset-manager/sync_ai_ruleset.sh
  echo "   ✓ .custom-ruleset-manager/sync_ai_ruleset.sh"
fi

# 6. Sync README (always overwrite)
if [[ -f "$TEMP_DIR/.custom-ruleset-manager/README.md" ]]; then
  cp "$TEMP_DIR/.custom-ruleset-manager/README.md" "./.custom-ruleset-manager/"
  echo "   ✓ .custom-ruleset-manager/README.md"
fi

# NOTE: init_project.sh is NOT synced - it only exists in template and deletes itself after first run
# NOTE: PROJECT_SPECIFIC.md is NOT created here - init_project.sh creates it
# NOTE: AI_RULES.md is NOT touched - it's already filled in by init_project.sh

echo ""
echo "✅ Sync complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Summary:"
echo ""
echo "🔄 Synced (will be overwritten on next sync):"
echo "   • rules/BASE_RULES.md"
echo "   • rules/skills/"
echo "   • .cursor/rules/"
echo "   • CLAUDE.md"
echo "   • AGENTS.md"
echo "   • .custom-ruleset-manager/sync_ai_ruleset.sh"
echo "   • .custom-ruleset-manager/README.md"
echo ""
echo "🔒 Protected (never overwritten):"
echo "   • rules/PROJECT_SPECIFIC.md"
echo "   • AI_RULES.md"
echo ""
echo "💡 Tip: Run this script anytime to get latest rules from template"
echo ""