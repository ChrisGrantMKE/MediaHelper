# 📋 Project Roadmap & Future To-Do Items

## 🚀 Next Priority: Cloudflare REST API Dynamic DNS (Auto-IP Updater)

- [ ] **Automated Dynamic DNS (DDNS) Engine via Cloudflare REST API**
  - **Objective:** Automatically detect changes in the server's public WAN IP address and update the Cloudflare DNS `A` record(s) for `chrisgrants.net` (and configured subdomains).
  - **Core Components:**
    - **IP Detection:** Query lightweight public IP services (e.g. `https://1.1.1.1/cdn-cgi/trace`, `https://api.ipify.org`, or `https://icanhazip.com`).
    - **Local State Cache:** Store the last known public IP in `media_tracker.db` (or `.last_ip`) to avoid redundant API calls.
    - **Cloudflare REST API Client:**
      - Query Zone ID & DNS Record ID:
        `GET https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={domain}`
      - Update Record upon IP change:
        `PATCH https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}`
        Payload: `{"type": "A", "name": "{domain}", "content": "{new_ip}", "ttl": 1, "proxied": true}`
    - **Integration Options:**
      - Lightweight standalone systemd timer / cron job (e.g. checks every 5–15 minutes).
      - Integrated background thread within `jellyfin_listener.py`.
    - **Alerts:** Dispatch a push notification via `ntfy` (`SeaGee_new_releases` or `SeaGee_server_alerts`) whenever a public IP change is detected and updated.
