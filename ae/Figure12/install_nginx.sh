#!/bin/bash
# install_nginx.sh — Install NGINX, wrk2, and generate workload files for Figure 12
#
# This script sets up both the NGINX server (local) and the wrk2 client (remote).
#
# Usage:
#   bash install_nginx.sh [server|client|all]
#
# Default: all (installs both server and client components)
#
# Server (192.168.6.1):
#   - Installs NGINX, generates heavy-tailed workload files
# Client (192.168.6.2):
#   - Installs wrk2, copies Lua script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT="${1:-all}"

SERVER_IP="192.168.6.1"
CLIENT_IP="192.168.6.2"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()    { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok() { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
die()    { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Server: Install NGINX and generate workload ─────────────────────
install_server() {
    log "Installing NGINX ..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq nginx bc iproute2

    # Configure NGINX for benchmarking
    log "Configuring NGINX ..."
    sudo tee /etc/nginx/sites-available/bench > /dev/null <<'NGINX_CONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html;

    server_name _;

    location /bench/ {
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        access_log off;
    }
}
NGINX_CONF

    sudo ln -sf /etc/nginx/sites-available/bench /etc/nginx/sites-enabled/bench
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    log_ok "NGINX installed and configured"

    # Generate heavy-tailed workload files
    generate_workload
}

# ── Generate heavy-tailed file distribution ──────────────────────────
generate_workload() {
    local target_dir="/var/www/html/bench"
    sudo mkdir -p "$target_dir"
    sudo rm -rf "${target_dir:?}"/*

    log "Generating 100 files with heavy-tailed web content distribution ..."

    for i in $(seq 1 100); do
        rand=$((RANDOM % 100 + 1))

        if [ "$rand" -le 40 ]; then
            # Class A: 1–5KB (40%) — tiny resources: icons, thumbnails
            size_kb=$(( (RANDOM % 5) + 1 ))
        elif [ "$rand" -le 70 ]; then
            # Class B: 5–20KB (30%) — small images, scripts
            size_kb=$(( (RANDOM % 16) + 5 ))
        elif [ "$rand" -le 85 ]; then
            # Class C: 20–50KB (15%) — medium images
            size_kb=$(( (RANDOM % 31) + 20 ))
        elif [ "$rand" -le 95 ]; then
            # Class D: 50–200KB (10%) — photos
            size_kb=$(( (RANDOM % 151) + 50 ))
        else
            # Class E: 200–500KB (5%) — larger photos/documents
            size_kb=$(( (RANDOM % 301) + 200 ))
        fi

        size_bytes=$(( size_kb * 1024 ))

        echo -ne "[File $i/100] ${size_kb}KB\r"
        sudo dd if=/dev/urandom of="${target_dir}/file_${i}.bin" \
            bs=1K count=${size_kb} status=none
    done

    echo ""
    log_ok "Workload generated: $(du -sh "$target_dir" | cut -f1) total"
    log "Largest 5 files:"
    ls -lhS "${target_dir}"/file_*.bin | head -5
}

# ── Client: Install wrk2 ────────────────────────────────────────────
install_client() {
    log "Installing wrk2 dependencies ..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq build-essential libssl-dev git bc iproute2

    local wrk2_dir="/tmp/wrk2"
    if [[ ! -x "/usr/local/bin/wrk2" ]]; then
        log "Building wrk2 from source ..."
        rm -rf "$wrk2_dir"
        git clone https://github.com/giltene/wrk2.git "$wrk2_dir"
        make -C "$wrk2_dir" -j"$(nproc)"
        sudo cp "$wrk2_dir/wrk" /usr/local/bin/wrk2
        rm -rf "$wrk2_dir"
        log_ok "wrk2 installed at /usr/local/bin/wrk2"
    else
        log_ok "wrk2 already installed"
    fi

    # Create Lua script for Zipf access pattern
    mkdir -p "$SCRIPT_DIR/lua"
    cat > "$SCRIPT_DIR/lua/zipf.lua" <<'LUA_SCRIPT'
-- zipf.lua — Deterministic Zipf(1.2) access pattern for wrk2

local total_files = 100
local zipf_alpha = 1.2
local base_seed = 42

local counter = 1
function setup(thread)
   thread:set("id", counter)
   counter = counter + 1
end

function init(args)
   math.randomseed(base_seed + id)
   math.random(); math.random(); math.random()
end

local function get_zipf_index(n, alpha)
    local r = math.random()
    local index = math.floor(math.pow(r, -1/alpha))
    if index > n then
        return math.random(1, n)
    else
        return index
    end
end

request = function()
   local index = get_zipf_index(total_files, zipf_alpha)
   local path = "/bench/file_" .. index .. ".bin"
   return wrk.format("GET", path)
end
LUA_SCRIPT
    log_ok "Lua script created: $SCRIPT_DIR/lua/zipf.lua"
}

# ── Main ─────────────────────────────────────────────────────────────
case "$COMPONENT" in
    server)
        install_server
        ;;
    client)
        install_client
        ;;
    all)
        install_server
        install_client
        ;;
    *)
        die "Unknown component: $COMPONENT (use: server, client, or all)"
        ;;
esac

log_ok "Installation complete ($COMPONENT)"
echo ""
echo "Next steps:"
echo "  On server ($SERVER_IP):  bash install_nginx.sh server"
echo "  On client ($CLIENT_IP):  bash install_nginx.sh client"
echo "  Then:                    sudo bash run.sh"
