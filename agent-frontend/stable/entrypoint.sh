#!/bin/sh
set -e

STATIC_DIR="/usr/share/nginx/html"
UPSTREAM="https://os.agno.com"
API_UPSTREAM="https://os-api.agno.com"
LOCAL_API="http://localhost:8080/api-proxy"

echo "[entrypoint] Fetching HTML to discover JS bundles..."
HTML=$(curl -sL --compressed "$UPSTREAM/")

if [ -z "$HTML" ]; then
  echo "[entrypoint] ERROR: Could not fetch $UPSTREAM — check network."
  exit 1
fi

# Extract all JS paths from <script src="..."> tags
JS_PATHS=$(echo "$HTML" | grep -oE 'src="[^"]+\.js"' | sed 's/src="//;s/"//')

if [ -z "$JS_PATHS" ]; then
  echo "[entrypoint] WARNING: No JS bundles found in HTML. Sub_filter will be the fallback."
else
  echo "$JS_PATHS" | while IFS= read -r path; do
    # Resolve to full URL
    case "$path" in
      http*) URL="$path" ;;
      *)     URL="$UPSTREAM$path" ;;
    esac

    # Mirror the path locally under STATIC_DIR
    LOCAL_PATH="$STATIC_DIR$path"
    mkdir -p "$(dirname "$LOCAL_PATH")"

    echo "[entrypoint] Patching: $path"
    # Fetch (with decompression) then sed-replace API URLs
    curl -sL --compressed "$URL" \
      | sed "s|$API_UPSTREAM|$LOCAL_API|g" \
      > "$LOCAL_PATH"

    echo "[entrypoint]   -> saved to $LOCAL_PATH ($(wc -c < "$LOCAL_PATH") bytes)"
  done
fi

echo "[entrypoint] Done. Starting nginx..."
exec nginx -g "daemon off;"
