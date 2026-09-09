import os
import json
import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

class NotificationEngine:
    def __init__(self, config=None):
        self.config = config.get("notifications", {}) if config else {}

    def dispatch(self, artist, releases, bandcamp_url=None, callback_url=None):
        """
        Dispatches notifications to all enabled channels.
        Returns a dictionary of status per channel.
        """
        if not releases:
            return {}

        results = {}

        # 1. Local Markdown Digest (always default / fallback)
        md_cfg = self.config.get("markdown_digest", {})
        if md_cfg.get("enabled", True):
            md_path = md_cfg.get("file_path", "NEW_RELEASES.md")
            results["markdown"] = self.log_markdown(artist, releases, md_path, bandcamp_url)

        # 2. Email (SMTP)
        email_cfg = self.config.get("email", {})
        if email_cfg.get("enabled", False):
            results["email"] = self.send_email(artist, releases, email_cfg, bandcamp_url)

        # 3. Discord Webhook
        discord_cfg = self.config.get("discord", {})
        if discord_cfg.get("enabled", False) and discord_cfg.get("webhook_url"):
            results["discord"] = self.send_discord(artist, releases, discord_cfg.get("webhook_url"))

        # 4. ntfy Push Notification
        ntfy_cfg = self.config.get("ntfy", {})
        if ntfy_cfg.get("enabled", False) and ntfy_cfg.get("topic"):
            server_url = ntfy_cfg.get("server_url", "https://ntfy.sh")
            topic = ntfy_cfg.get("topic")
            results["ntfy"] = self.send_ntfy(artist, releases, server_url, topic, callback_url=callback_url)

        return results

    def log_markdown(self, artist, releases, file_path="NEW_RELEASES.md", bandcamp_url=None):
        try:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            lines = []
            if not os.path.exists(file_path):
                lines.append("# 🎵 Bandcamp New Releases Log\n\n")

            artist_link = f"[{artist}]({bandcamp_url})" if bandcamp_url else artist
            lines.append(f"### {artist_link} — Discovered {now_str}\n\n")

            for r in releases:
                title = r.get("title", "Untitled")
                url = r.get("url", "#")
                date = r.get("date_published") or (str(r.get("year")) if r.get("year") else "Unknown Date")
                cover = r.get("cover_art")

                if cover:
                    lines.append(f"- [![{title}]({cover})]({url}) **[{title}]({url})** — *{date}*\n")
                else:
                    lines.append(f"- **[{title}]({url})** — *{date}*\n")

            lines.append("\n---\n\n")

            with open(file_path, "a", encoding="utf-8") as f:
                f.writelines(lines)
            return {"status": "success", "file": file_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_email(self, artist, releases, email_cfg, bandcamp_url=None):
        try:
            smtp_host = email_cfg.get("smtp_host", "smtp.gmail.com")
            smtp_port = int(email_cfg.get("smtp_port", 587))
            use_tls = email_cfg.get("use_tls", True)
            username = email_cfg.get("username")
            password = email_cfg.get("password")
            to_addr = email_cfg.get("to_address")

            if not username or not password or not to_addr:
                return {"status": "skipped", "reason": "Missing email credentials"}

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎧 New Bandcamp Releases: {artist}"
            msg["From"] = username
            msg["To"] = to_addr

            # Plaintext body
            text_lines = [f"New Bandcamp releases found for {artist}:\n"]
            for r in releases:
                text_lines.append(f"- {r.get('title')} ({r.get('date_published', r.get('year'))}): {r.get('url')}")
            text_part = MIMEText("\n".join(text_lines), "plain", "utf-8")

            # HTML body
            html_cards = []
            for r in releases:
                title = r.get("title", "Untitled")
                url = r.get("url", "#")
                date = r.get("date_published") or (str(r.get("year")) if r.get("year") else "")
                cover = r.get("cover_art", "")
                img_tag = f'<img src="{cover}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 6px; margin-right: 15px;" />' if cover else ''

                card = f"""
                <div style="display: flex; align-items: center; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                    {img_tag}
                    <div>
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 4px;">{title}</div>
                        <div style="color: #6c757d; font-size: 13px; margin-bottom: 8px;">📅 {date}</div>
                        <a href="{url}" style="display: inline-block; background: #1da1f2; color: #ffffff; padding: 6px 14px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold;">Listen on Bandcamp &rarr;</a>
                    </div>
                </div>
                """
                html_cards.append(card)

            html_content = f"""
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #212529; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="border-bottom: 2px solid #000; padding-bottom: 8px;">🎧 New Music for {artist}</h2>
                <p>Based on your Jellyfin playback today, here are newer releases available on Bandcamp:</p>
                {''.join(html_cards)}
                <div style="margin-top: 24px; font-size: 12px; color: #adb5bd; border-top: 1px solid #dee2e6; padding-top: 10px;">
                    MediaHelper Automation &bull; Jellyfin &bull; Bandcamp
                </div>
            </body>
            </html>
            """
            html_part = MIMEText(html_content, "html", "utf-8")

            msg.attach(text_part)
            msg.attach(html_part)

            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.sendmail(username, [to_addr], msg.as_string())
            server.quit()

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_discord(self, artist, releases, webhook_url):
        try:
            embeds = []
            for r in releases[:5]:  # Discord limit is 10 embeds
                title = r.get("title", "Untitled")
                url = r.get("url", "")
                date = r.get("date_published") or (str(r.get("year")) if r.get("year") else "Recently")
                cover = r.get("cover_art")
                desc = r.get("description") or f"Released: {date}"

                embed = {
                    "title": f"{artist} - {title}",
                    "url": url,
                    "description": desc[:250],
                    "color": 3447003, # Blue
                    "fields": [
                        {"name": "📅 Release Date", "value": str(date), "inline": True}
                    ]
                }
                if cover:
                    embed["thumbnail"] = {"url": cover}
                embeds.append(embed)

            payload = {
                "content": f"🚨 **New Bandcamp Release Alert for {artist}**",
                "embeds": embeds
            }

            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "MediaHelper-Notifier"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 204):
                    return {"status": "success"}
                return {"status": "error", "code": resp.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def send_ntfy(self, artist, releases, server_url="https://ntfy.sh", topic="mediahelper-releases", callback_url=None):
        try:
            count = len(releases)
            first = releases[0]
            first_title = first.get("title", "Untitled")
            title = f"New {artist} Release{'s' if count > 1 else ''} ({count})"
            body = f"Latest: {first_title} ({first.get('date_published', first.get('year'))})"
            click_url = first.get("url", "")

            actions = []
            if click_url:
                actions.append({
                    "action": "view",
                    "label": "Open Bandcamp",
                    "url": click_url
                })

            if callback_url:
                cb = callback_url.rstrip("/")
                q_art = urllib.parse.quote(artist)
                q_rel = urllib.parse.quote(first_title)
                actions.append({
                    "action": "view",
                    "label": "Ignore Release",
                    "url": f"{cb}/ignore_release?artist={q_art}&release={q_rel}"
                })
                actions.append({
                    "action": "view",
                    "label": "Mute Artist",
                    "url": f"{cb}/ignore_artist?artist={q_art}"
                })

            payload = {
                "topic": topic,
                "title": f"🎧 {title}",
                "message": body,
                "click": click_url,
                "tags": ["musical_note", "headphones"]
            }

            if actions:
                payload["actions"] = actions

            req = urllib.request.Request(
                f"{server_url.rstrip('/')}",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "MediaHelper-Notifier"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    return {"status": "success"}
                return {"status": "error", "code": resp.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}
