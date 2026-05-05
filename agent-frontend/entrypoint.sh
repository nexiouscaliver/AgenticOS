#!/bin/sh
set -e

STATIC_DIR="/usr/share/nginx/html"
UPSTREAM="https://os.agno.com"
API_UPSTREAM="https://os-api.agno.com"
LOCAL_API="http://localhost:8080/api-proxy"
LOCAL_BACKEND_ORIG="http://localhost:7777"
LOCAL_BACKEND_PROXY="http://localhost:8080/local-backend"

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
    case "$path" in
      http*) URL="$path" ;;
      *)     URL="$UPSTREAM$path" ;;
    esac

    LOCAL_PATH="$STATIC_DIR$path"
    mkdir -p "$(dirname "$LOCAL_PATH")"

    echo "[entrypoint] Patching: $path"

    # Patch 1: Rewrite remote API base URL → our /api-proxy/ location
    # Patch 2: Rewrite local backend URL → our /local-backend/ location
    #          (browser blocks cross-port requests; nginx forwards to host:7777)
    curl -sL --compressed "$URL" \
      | sed "s|$API_UPSTREAM|$LOCAL_API|g" \
      | sed "s|$LOCAL_BACKEND_ORIG|$LOCAL_BACKEND_PROXY|g" \
      > "$LOCAL_PATH"

    echo "[entrypoint]   -> saved to $LOCAL_PATH ($(wc -c < "$LOCAL_PATH") bytes)"
  done
fi

echo "[entrypoint] Done. Starting nginx..."
exec nginx -g "daemon off;"
