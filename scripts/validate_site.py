#!/usr/bin/env python3
"""Validate the static portfolio before deployment using only the Python standard library."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://devineenukorah.github.io/professional-portfolio/"
REQUIRED_FILES = {
    "index.html",
    "404.html",
    "assets/css/styles.css",
    "assets/js/theme.js",
    "assets/js/main.js",
    "assets/icons/favicon.svg",
    "images/Bless-Dark.png",
    "images/Bless-White.png",
    "robots.txt",
    "sitemap.xml",
    "site.webmanifest",
    ".nojekyll",
}


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.references: list[tuple[str, str]] = []
        self.meta_names: dict[str, str] = {}
        self.meta_properties: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.title_parts: list[str] = []
        self._in_title = False
        self.inline_scripts = 0
        self.inline_styles = 0
        self._script_has_src = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}

        if "id" in attributes:
            self.ids.append(attributes["id"])

        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.references.append((attribute, value))

        if tag == "meta":
            content = attributes.get("content", "")
            if attributes.get("name"):
                self.meta_names[attributes["name"].lower()] = content
            if attributes.get("property"):
                self.meta_properties[attributes["property"].lower()] = content

        if tag == "link" and attributes.get("rel"):
            self.links[attributes["rel"].lower()] = attributes.get("href", "")

        if tag == "title":
            self._in_title = True

        if tag == "script":
            self._script_has_src = bool(attributes.get("src"))
            if not self._script_has_src:
                self.inline_scripts += 1

        if tag == "style":
            self.inline_styles += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script":
            self._script_has_src = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def local_path_from_reference(reference: str) -> Path | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("#", "mailto:", "tel:")):
        return None

    path = parsed.path
    if not path or path == "/professional-portfolio/":
        return None

    if path.startswith("/professional-portfolio/"):
        path = path.removeprefix("/professional-portfolio/")
    elif path.startswith("/"):
        return None

    return ROOT / path.lstrip("./")


def validate_html(path: Path, errors: list[str]) -> SiteHTMLParser:
    parser = SiteHTMLParser()
    content = path.read_text(encoding="utf-8")
    parser.feed(content)

    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        fail(errors, f"{path.name}: duplicate IDs: {', '.join(duplicates)}")

    for attribute, reference in parser.references:
        local_path = local_path_from_reference(reference)
        if local_path is not None and not local_path.exists():
            fail(errors, f"{path.name}: missing local {attribute} target: {reference}")

    if parser.inline_scripts:
        fail(errors, f"{path.name}: contains {parser.inline_scripts} inline script block(s)")
    if parser.inline_styles:
        fail(errors, f"{path.name}: contains {parser.inline_styles} inline style block(s)")

    return parser


def main() -> int:
    errors: list[str] = []

    for relative_path in sorted(REQUIRED_FILES):
        if not (ROOT / relative_path).exists():
            fail(errors, f"Missing required file: {relative_path}")

    index = validate_html(ROOT / "index.html", errors)
    validate_html(ROOT / "404.html", errors)

    if not index.title:
        fail(errors, "index.html: missing title")
    elif len(index.title) > 70:
        fail(errors, f"index.html: title is too long ({len(index.title)} characters)")

    description = index.meta_names.get("description", "")
    if not 70 <= len(description) <= 170:
        fail(errors, f"index.html: meta description length should be 70-170 characters, found {len(description)}")

    required_meta_names = {"description", "robots", "twitter:card", "twitter:title", "twitter:description", "twitter:image"}
    for name in sorted(required_meta_names):
        if not index.meta_names.get(name):
            fail(errors, f"index.html: missing meta name={name!r}")

    required_properties = {"og:title", "og:description", "og:type", "og:url", "og:image", "og:image:alt"}
    for property_name in sorted(required_properties):
        if not index.meta_properties.get(property_name):
            fail(errors, f"index.html: missing meta property={property_name!r}")

    if index.links.get("canonical") != SITE_URL:
        fail(errors, "index.html: canonical URL does not match the production URL")
    if index.meta_properties.get("og:url") != SITE_URL:
        fail(errors, "index.html: og:url does not match the production URL")

    if index.inline_scripts or index.inline_styles:
        fail(errors, "index.html: strict CSP requires external scripts and styles")

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    expected_sitemap = f"Sitemap: {SITE_URL}sitemap.xml"
    if expected_sitemap not in robots:
        fail(errors, "robots.txt: sitemap URL is missing or incorrect")

    try:
        sitemap_root = ET.parse(ROOT / "sitemap.xml").getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [element.text for element in sitemap_root.findall("sm:url/sm:loc", namespace)]
        if locations != [SITE_URL]:
            fail(errors, f"sitemap.xml: expected only {SITE_URL!r}, found {locations!r}")
    except ET.ParseError as exc:
        fail(errors, f"sitemap.xml: invalid XML: {exc}")

    try:
        manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
        if manifest.get("start_url") != "/professional-portfolio/":
            fail(errors, "site.webmanifest: incorrect start_url")
        if manifest.get("scope") != "/professional-portfolio/":
            fail(errors, "site.webmanifest: incorrect scope")
    except json.JSONDecodeError as exc:
        fail(errors, f"site.webmanifest: invalid JSON: {exc}")

    css = (ROOT / "assets/css/styles.css").read_text(encoding="utf-8")
    if "prefers-reduced-motion" not in css:
        fail(errors, "styles.css: missing reduced-motion support")

    for script_name in ("theme.js", "main.js"):
        script = (ROOT / "assets/js" / script_name).read_text(encoding="utf-8")
        if "eval(" in script or "new Function" in script:
            fail(errors, f"{script_name}: dynamic code execution is not allowed")

    if errors:
        print("Site validation failed:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Site validation passed.")
    print(f"Checked {len(REQUIRED_FILES)} required files, HTML references, metadata, sitemap, manifest, CSS, and JavaScript safety rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
