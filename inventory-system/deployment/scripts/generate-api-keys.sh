#!/bin/bash
set -euo pipefail

###############################################################################
# Generate ERPNext API Keys for the Inventory System
#
# Run this AFTER ERPNext is up and you can log in as Administrator.
#
# Usage:
#   ./generate-api-keys.sh <erpnext-url> <admin-password>
#
# Example:
#   ./generate-api-keys.sh http://localhost:8080 admin
###############################################################################

ERPNEXT_URL="${1:?Usage: $0 <erpnext-url> <admin-password>}"
ADMIN_PASSWORD="${2:?Usage: $0 <erpnext-url> <admin-password>}"

echo "Logging into ERPNext at ${ERPNEXT_URL}..."

# Login and get session cookie
COOKIES=$(mktemp)
LOGIN_RESPONSE=$(curl -s -c "$COOKIES" -X POST "${ERPNEXT_URL}/api/method/login" \
    -H "Content-Type: application/json" \
    -d "{\"usr\": \"Administrator\", \"pwd\": \"${ADMIN_PASSWORD}\"}")

if echo "$LOGIN_RESPONSE" | grep -q "Logged In"; then
    echo "Login successful."
else
    echo "Login failed: $LOGIN_RESPONSE"
    rm -f "$COOKIES"
    exit 1
fi

# Generate API keys
echo "Generating API keys..."
KEY_RESPONSE=$(curl -s -b "$COOKIES" -X POST \
    "${ERPNEXT_URL}/api/method/frappe.core.doctype.user.user.generate_keys" \
    -H "Content-Type: application/json" \
    -d '{"user": "Administrator"}')

API_SECRET=$(echo "$KEY_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['api_secret'])" 2>/dev/null)

# Get the API key from user doc
API_KEY=$(curl -s -b "$COOKIES" \
    "${ERPNEXT_URL}/api/resource/User/Administrator" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['api_key'])" 2>/dev/null)

rm -f "$COOKIES"

if [ -n "$API_KEY" ] && [ -n "$API_SECRET" ]; then
    echo ""
    echo "========================================="
    echo " API Keys Generated Successfully"
    echo "========================================="
    echo ""
    echo "ERPNEXT_API_KEY=${API_KEY}"
    echo "ERPNEXT_API_SECRET=${API_SECRET}"
    echo ""
    echo "Add these to your .env file:"
    echo "  ERPNEXT_URL=${ERPNEXT_URL}"
    echo "  ERPNEXT_API_KEY=${API_KEY}"
    echo "  ERPNEXT_API_SECRET=${API_SECRET}"
    echo ""
    echo "IMPORTANT: Save the API Secret now - it cannot be retrieved later!"
else
    echo "Failed to generate API keys."
    echo "Response: $KEY_RESPONSE"
    exit 1
fi
