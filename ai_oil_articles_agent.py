#!/usr/bin/env python3
"""Daily agent: finds fresh AI-in-oil-refining articles and emails links."""

from __future__ import annotations

import os
import smtplib
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus


@dataclass
class Article:
    title: str
    link: str
    published: datetime | None
    source: str


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru"
DEFAULT_QUERY = (
    '("искусственный интеллект" OR AI) '
    '("нефтепереработка" OR "oil refining" OR НПЗ) '
    '(статья OR research OR paper OR кейс)'
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_rfc2822(date_text: str) -> datetime | None:
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(date_text, fmt)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def parse_rss_feed(url: str) -> list[Article]:
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = root.findall("./channel/item")
    articles: list[Article] = []

    for item in items:
        title = (item.findtext("title") or "Без названия").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_text = (item.findtext("pubDate") or "").strip()
        source = (item.findtext("source") or "Unknown source").strip()
        published = parse_rfc2822(pub_date_text) if pub_date_text else None

        articles.append(Article(title=title, link=link, published=published, source=source))

    return articles


def fetch_recent_articles(query: str, within_hours: int) -> list[Article]:
    url = os.environ.get("NEWS_FEED_URL", GOOGLE_NEWS_RSS.format(query=quote_plus(query)))
    feed_items = parse_rss_feed(url)

    cutoff = utc_now() - timedelta(hours=within_hours)
    result: list[Article] = []
    seen_links: set[str] = set()

    for article in feed_items:
        if not article.link or article.link in seen_links:
            continue

        if article.published and article.published < cutoff:
            continue

        seen_links.add(article.link)
        result.append(article)

    return result


def format_email_html(articles: Iterable[Article], query: str) -> str:
    articles = list(articles)
    generated_at = utc_now().strftime("%Y-%m-%d %H:%M UTC")

    if not articles:
        return f"""
        <h2>Ежедневный отчёт по AI в нефтепереработке</h2>
        <p><b>Дата:</b> {generated_at}</p>
        <p><b>Запрос:</b> {query}</p>
        <p>Новых публикаций за последние сутки не найдено.</p>
        """

    lines = [
        "<h2>Ежедневный отчёт по AI в нефтепереработке</h2>",
        f"<p><b>Дата:</b> {generated_at}</p>",
        f"<p><b>Запрос:</b> {query}</p>",
        "<ol>",
    ]

    for article in articles:
        published = (
            article.published.strftime("%Y-%m-%d %H:%M UTC") if article.published else "дата не указана"
        )
        lines.append(
            f'<li><a href="{article.link}">{article.title}</a><br>'
            f"Источник: {article.source}; Дата: {published}</li>"
        )

    lines.append("</ol>")
    return "\n".join(lines)


def write_pdf_report(path: str, articles: list[Article], query: str) -> None:
    timestamp = utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "AI Oil Articles Agent - Search Results",
        f"Generated: {timestamp}",
        f"Query: {query}",
        f"Articles found: {len(articles)}",
        "",
    ]

    if not articles:
        lines.append("No new articles for the selected interval.")
    else:
        for idx, article in enumerate(articles, start=1):
            pub = article.published.strftime("%Y-%m-%d %H:%M UTC") if article.published else "n/a"
            lines.append(f"{idx}. {article.title}")
            lines.append(f"   Source: {article.source}")
            lines.append(f"   Published: {pub}")
            lines.append(f"   Link: {article.link}")
            lines.append("")

    content = ["BT", "/F1 10 Tf", "40 800 Td"]
    for i, line in enumerate(lines):
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        if i != 0:
            content.append("0 -14 Td")
        content.append(f"({safe}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1"))

    Path(path).write_bytes(pdf)


def send_email(subject: str, html_body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    smtp_starttls = os.environ.get("SMTP_STARTTLS", "1") == "1"

    sender = os.environ.get("SENDER_EMAIL", smtp_user or "agent@localhost")
    recipient = os.environ.get("RECIPIENT_EMAIL", "rataganov78@gmail.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if smtp_starttls:
            server.starttls()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(sender, [recipient], msg.as_string())


def run() -> None:
    query = os.environ.get("NEWS_QUERY", DEFAULT_QUERY)
    within_hours = int(os.environ.get("WITHIN_HOURS", "24"))
    pdf_path = os.environ.get("RESULT_PDF_PATH", "agent_search_results.pdf")

    articles = fetch_recent_articles(query=query, within_hours=within_hours)
    html = format_email_html(articles, query=query)
    write_pdf_report(pdf_path, articles, query)
    send_email(
        subject="AI + нефтепереработка: новые статьи за сутки",
        html_body=html,
    )

    print(f"Done. Sent {len(articles)} article(s) to email. PDF: {pdf_path}")


if __name__ == "__main__":
    run()
