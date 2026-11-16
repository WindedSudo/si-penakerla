"""Pengambil lowongan dari RSS/Atom feed publik yang dikonfigurasi pengelola.

Tidak menerima URL dari form pengguna. Daftar feed hanya dibaca dari konfigurasi server.
"""
import ipaddress
import socket
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET

MAX_FEED_BYTES = 2 * 1024 * 1024
MAX_ITEMS_PER_FEED = 100


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def strip_markup(value, max_length=8000):
    if not value:
        return ''
    parser = _TextExtractor()
    try:
        parser.feed(str(value))
        text = unescape(' '.join(parser.parts))
    except Exception:
        text = unescape(re.sub(r'<[^>]+>', ' ', str(value)))
    return re.sub(r'\s+', ' ', text).strip()[:max_length]


def _safe_public_url(url):
    parsed = urlparse((url or '').strip())
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('URL feed harus menggunakan HTTP atau HTTPS.')
    if parsed.username or parsed.password:
        raise ValueError('URL dengan kredensial tidak diperbolehkan.')
    host = parsed.hostname.lower().rstrip('.')
    if host in {'localhost', 'localhost.localdomain'}:
        raise ValueError('Host lokal tidak diperbolehkan.')
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80))
        except (socket.gaierror, ValueError) as dns_error:
            raise ValueError('Nama host feed tidak dapat ditemukan.') from dns_error
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0].split('%')[0])
            if not ip.is_global:
                raise ValueError('Host feed mengarah ke jaringan privat/lokal.')
    else:
        if not literal_ip.is_global:
            raise ValueError('Alamat IP privat/lokal tidak diperbolehkan.')
    return parsed


class _SameHostRedirectHandler(HTTPRedirectHandler):
    def __init__(self, initial_host):
        super().__init__()
        self.initial_host = initial_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = _safe_public_url(newurl)
        if parsed.hostname != self.initial_host:
            raise ValueError('Redirect lintas host ditolak; gunakan URL feed final.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _child_text(element, names):
    names = set(names)
    for child in list(element):
        local = child.tag.rsplit('}', 1)[-1].lower()
        if local in names:
            direct_text = (child.text or '').strip()
            if direct_text:
                return direct_text
            for nested in child.iter():
                if nested is child:
                    continue
                nested_text = (nested.text or '').strip()
                if nested_text:
                    return nested_text
    return ''


def _entry_link(entry):
    for child in list(entry):
        if child.tag.rsplit('}', 1)[-1].lower() == 'link':
            href = child.attrib.get('href')
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ''


def _parse_date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo:
        parsed = parsed.astimezone(ZoneInfo('Asia/Jakarta')).replace(tzinfo=None)
    return parsed


def parse_feed(xml_bytes, source_name, feed_url):
    if b'<!DOCTYPE' in xml_bytes.upper() or b'<!ENTITY' in xml_bytes.upper():
        raise ValueError('Deklarasi DTD/entity tidak diizinkan pada feed.')
    root = ET.fromstring(xml_bytes)
    entries = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1].lower() in ('item', 'entry')]
    parsed_feed = []
    source_host = urlparse(feed_url).hostname or source_name

    for entry in entries[:MAX_ITEMS_PER_FEED]:
        title = _child_text(entry, {'title'})
        link = _entry_link(entry)
        if not link:
            link = _child_text(entry, {'link'})
        if not title or not link:
            continue
        parsed_link = urlparse(link.strip())
        if (parsed_link.scheme not in ('http', 'https') or not parsed_link.hostname
                or parsed_link.username or parsed_link.password or len(link) > 1000):
            continue

        guid = _child_text(entry, {'guid', 'id'}) or link
        description = _child_text(entry, {'description', 'summary', 'content', 'encoded'})
        company = _child_text(entry, {'company', 'author', 'creator'})
        location = _child_text(entry, {'location', 'joblocation', 'region'})
        published = _parse_date(_child_text(entry, {'pubdate', 'published', 'updated', 'date'}))
        parsed_feed.append({
            'sumber': strip_markup(source_name or source_host, 200),
            'source_key': guid[:255],
            'posisi': strip_markup(title, 200) or 'Lowongan tanpa judul',
            'perusahaan': strip_markup(company, 200) or strip_markup(source_name or source_host, 200),
            'deskripsi': strip_markup(description, 8000),
            'lokasi': strip_markup(location, 200) or 'Lihat sumber lowongan',
            'url_lamaran': link[:1000],
            'tanggal_publikasi': published,
        })
    return parsed_feed


def fetch_and_parse_feed(feed_url, timeout=12):
    parsed = _safe_public_url(feed_url)
    request = Request(
        feed_url,
        headers={
            'User-Agent': 'SI-PENAKERLA-JobFeed/1.0 (+public RSS/Atom reader)',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9,*/*;q=0.1'
        }
    )
    try:
        opener = build_opener(_SameHostRedirectHandler(parsed.hostname))
        with opener.open(request, timeout=timeout) as response:
            payload = response.read(MAX_FEED_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError(f'Feed tidak dapat diakses: {exc}') from exc
    if len(payload) > MAX_FEED_BYTES:
        raise ValueError('Ukuran feed melebihi batas 2 MB.')

    host = parsed.hostname or 'Sumber eksternal'
    source_name = host
    try:
        root = ET.fromstring(payload)
        source_container = next((node for node in root.iter()
                                 if node.tag.rsplit('}', 1)[-1].lower() in ('channel', 'feed')), root)
        source_name = _child_text(source_container, {'title'}) or host
    except ET.ParseError:
        # parse_feed akan mengeluarkan pesan parse yang jelas di bawah.
        pass
    return parse_feed(payload, source_name, feed_url)


def sync_configured_feeds(feed_urls):
    """Fetch semua feed yang dikonfigurasi. Hasil per feed dikembalikan terpisah."""
    from app.models.lowongan_eksternal import LowonganEksternal

    summary = []
    total_items = 0
    for feed_url in feed_urls or []:
        feed_url = (feed_url or '').strip()
        if not feed_url:
            continue
        try:
            items = fetch_and_parse_feed(feed_url)
            LowonganEksternal.upsert_many(items)
            total_items += len(items)
            summary.append({'url': feed_url, 'jumlah': len(items), 'error': None})
        except Exception as exc:
            summary.append({'url': feed_url, 'jumlah': 0, 'error': str(exc)[:300]})
    return {'total': total_items, 'feeds': summary}
