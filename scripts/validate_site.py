#!/usr/bin/env python3
"""Validate the static portfolio before deployment using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE_PATH = "/professional-portfolio/"
SITE_URL = f"https://devineenukorah.github.io{SITE_PATH}"
REQUIRED_FILES = {
    "index.html",
    "404.html",
    "assets/css/styles.css",
    "assets/css/production.css",
    "assets/js/theme.js",
    "assets/js/main.js",
    "assets/icons/favicon.svg",
    "images/Bless-Dark.png",
    "images/Bless-White.png",
    "robots.txt",
    "sitemap.xml",
    "site.webmanifest",
    ".nojekyll",
    ".github/workflows/pages.yml",
}
TEMPORARY_FILES = {"APPLY_UPGRADE.md", "PRODUCTION_AUDIT.md"}
REQUIRED_CSP_DIRECTIVES = {
    "default-src",
    "base-uri",
    "object-src",
    "img-src",
    "font-src",
    "style-src",
    "script-src",
    "connect-src",
    "form-action",
    "upgrade-insecure-requests",
}


@dataclass(frozen=True)
class Reference:
    tag: str
    attribute: str
    value: str
    attributes: dict[str, str]


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.references: list[Reference] = []
        self.meta_names: dict[str, str] = {}
        self.meta_properties: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.lang = ""
        self.h1_count = 0
        self.main_count = 0
        self.inline_scripts = 0
        self.inline_styles = 0
        self.images: list[dict[str, str]] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}

        if tag == "html":
            self.lang = attributes.get("lang", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "img":
            self.images.append(attributes)

        if "id" in attributes:
            self.ids.append(attributes["id"])

        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.references.append(Reference(tag, attribute, value, attributes))

        if tag == "meta":
            content = attributes.get("content", "")
            if attributes.get("name"):
                self.meta_names[attributes["name"].lower()] = content
            if attributes.get("property"):
                self.meta_properties[attributes["property"].lower()] = content
            if attributes.get("http-equiv", "").lower() == "content-security-policy":
                self.meta_names["content-security-policy"] = content

        if tag == "link" and attributes.get("rel"):
            for relation in attributes["rel"].lower().split():
                self.links[relation] = attributes.get("href", "")

        if tag == "title":
            self._in_title = True
        elif tag == "script" and not attributes.get("src"):
            self.inline_scripts += 1
        elif tag == "style":
            self.inline_styles += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

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
    if not path or path == SITE_PATH:
        return None

    if path.startswith(SITE_PATH):
        path = path.removeprefix(SITE_PATH)
    elif path.startswith("/"):
        return ROOT / "__invalid_project_root_reference__"

    return ROOT / path.lstrip("./")


def validate_csp(path: Path, parser: SiteHTMLParser, errors: list[str]) -> None:
    csp = parser.meta_names.get("content-security-policy", "")
    if not csp:
        fail(errors, f"{path.name}: missing Content-Security-Policy meta tag")
        return

    directives = {part.strip().split(maxsplit=1)[0] for part in csp.split(";") if part.strip()}
    missing = sorted(REQUIRED_CSP_DIRECTIVES - directives)
    if missing:
        fail(errors, f"{path.name}: CSP missing directives: {', '.join(missing)}")
    if "'unsafe-inline'" in csp or "'unsafe-eval'" in csp:
        fail(errors, f"{path.name}: CSP must not allow unsafe-inline or unsafe-eval")


def validate_html(path: Path, errors: list[str]) -> SiteHTMLParser:
    parser = SiteHTMLParser()
    content = path.read_text(encoding="utf-8")
    parser.feed(content)

    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        fail(errors, f"{path.name}: duplicate IDs: {', '.join(duplicates)}")

    id_set = set(parser.ids)
    for reference in parser.references:
        if reference.value.startswith("#"):
            fragment = reference.value[1:]
            if fragment and fragment not in id_set:
                fail(errors, f"{path.name}: missing fragment target: {reference.value}")
            continue

        if reference.value.startswith("http://"):
            fail(errors, f"{path.name}: insecure external reference: {reference.value}")

        if reference.value.startswith("/") and not reference.value.startswith(SITE_PATH):
            fail(errors, f"{path.name}: root-relative reference escapes project path: {reference.value}")

        local_path = local_path_from_reference(reference.value)
        if local_path is not None and not local_path.exists():
            fail(errors, f"{path.name}: missing local {reference.attribute} target: {reference.value}")

        if reference.tag == "a" and reference.attributes.get("target") == "_blank":
            rel_tokens = set(reference.attributes.get("rel", "").lower().split())
            if "noopener" not in rel_tokens or "noreferrer" not in rel_tokens:
                fail(errors, f"{path.name}: target=_blank link missing noopener noreferrer: {reference.value}")

    for image in parser.images:
        if "alt" not in image:
            fail(errors, f"{path.name}: image missing alt attribute: {image.get('src', '<unknown>')}")
        if not image.get("width") or not image.get("height"):
            fail(errors, f"{path.name}: image missing width/height: {image.get('src', '<unknown>')}")

    if parser.lang != "en":
        fail(errors, f"{path.name}: html lang must be 'en'")
    if parser.h1_count != 1:
        fail(errors, f"{path.name}: expected exactly one h1, found {parser.h1_count}")
    if parser.main_count != 1:
        fail(errors, f"{path.name}: expected exactly one main element, found {parser.main_count}")
    if parser.inline_scripts:
        fail(errors, f"{path.name}: contains {parser.inline_scripts} inline script block(s)")
    if parser.inline_styles:
        fail(errors, f"{path.name}: contains {parser.inline_styles} inline style block(s)")

    validate_csp(path, parser, errors)
    return parser


def main() -> int:
    errors: list[str] = []

    for relative_path in sorted(REQUIRED_FILES):
        if not (ROOT / relative_path).exists():
            fail(errors, f"Missing required file: {relative_path}")

    for relative_path in sorted(TEMPORARY_FILES):
        if (ROOT / relative_path).exists():
            fail(errors, f"Remove temporary upgrade document from production root: {relative_path}")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    index = validate_html(ROOT / "index.html", errors)
    not_found = validate_html(ROOT / "404.html", errors)

    if not index.title:
        fail(errors, "index.html: missing title")
    elif len(index.title) > 70:
        fail(errors, f"index.html: title is too long ({len(index.title)} characters)")

    description = index.meta_names.get("description", "")
    if not 70 <= len(description) <= 170:
        fail(errors, f"index.html: meta description length should be 70-170 characters, found {len(description)}")

    required_meta_names = {
        "description", "robots", "twitter:card", "twitter:title",
        "twitter:description", "twitter:image", "twitter:image:alt",
    }
    for name in sorted(required_meta_names):
        if not index.meta_names.get(name):
            fail(errors, f"index.html: missing meta name={name!r}")

    required_properties = {
        "og:title", "og:description", "og:type", "og:url", "og:image",
        "og:image:type", "og:image:width", "og:image:height", "og:image:alt",
    }
    for property_name in sorted(required_properties):
        if not index.meta_properties.get(property_name):
            fail(errors, f"index.html: missing meta property={property_name!r}")

    if index.meta_names.get("twitter:card") != "summary":
        fail(errors, "index.html: twitter:card should be 'summary' for the portrait social image")
    if index.links.get("canonical") != SITE_URL:
        fail(errors, "index.html: canonical URL does not match the production URL")
    if index.meta_properties.get("og:url") != SITE_URL:
        fail(errors, "index.html: og:url does not match the production URL")
    if "noindex" not in not_found.meta_names.get("robots", "").lower():
        fail(errors, "404.html: robots directive must include noindex")

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
        lastmod = sitemap_root.findtext("sm:url/sm:lastmod", namespaces=namespace)
        if not lastmod or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
            fail(errors, "sitemap.xml: lastmod must use YYYY-MM-DD")
    except ET.ParseError as exc:
        fail(errors, f"sitemap.xml: invalid XML: {exc}")

    try:
        manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
        if manifest.get("start_url") != SITE_PATH:
            fail(errors, "site.webmanifest: incorrect start_url")
        if manifest.get("scope") != SITE_PATH:
            fail(errors, "site.webmanifest: incorrect scope")
        if manifest.get("display") != "standalone":
            fail(errors, "site.webmanifest: display must be standalone")
        if not manifest.get("icons"):
            fail(errors, "site.webmanifest: at least one icon is required")
    except json.JSONDecodeError as exc:
        fail(errors, f"site.webmanifest: invalid JSON: {exc}")

    css = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in ("assets/css/styles.css", "assets/css/production.css")
    )
    for required_css_feature in ("prefers-reduced-motion", "forced-colors", "reveal-ready"):
        if required_css_feature not in css:
            fail(errors, f"CSS: missing required production feature: {required_css_feature}")

    for script_name in ("theme.js", "main.js"):
        script = (ROOT / "assets/js" / script_name).read_text(encoding="utf-8")
        if "eval(" in script or "new Function" in script:
            fail(errors, f"{script_name}: dynamic code execution is not allowed")

    workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    for required_workflow_text in (
        "pull_request:",
        "persist-credentials: false",
        "python3 scripts/validate_site.py",
        "node --check assets/js/main.js",
        "actions/upload-pages-artifact",
        "actions/deploy-pages",
    ):
        if required_workflow_text not in workflow:
            fail(errors, f"pages.yml: missing required control: {required_workflow_text}")

    if errors:
        print("Site validation failed:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Site validation passed.")
    print(
        f"Checked {len(REQUIRED_FILES)} required files, HTML semantics, references, CSP, metadata, "
        "sitemap, manifest, CSS, JavaScript, and deployment controls."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
