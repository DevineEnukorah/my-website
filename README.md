# Devine Enukorah Portfolio

Production-oriented professional portfolio for Devine Enukorah, an AI Automation Engineer and Workflow Consultant based in Abuja, Nigeria.

The site presents reliable AI automation systems that connect AI models, APIs, business applications, deterministic rules, structured data, and human-review processes.

## Live site

<https://devineenukorah.github.io/professional-portfolio/>

## Featured projects

### AI Lead Qualification and Reply Assistant

An n8n-based lead-processing system that validates inbound data, uses Gemini for constrained analysis, calculates scores deterministically, identifies stated pain points, and produces a review-ready follow-up response.

Repository: <https://github.com/DevineEnukorah/n8n-gemini-lead-qualifier>

### Nigerian Legal Information Project

An early-stage legal-technology project exploring reliable retrieval of Nigerian legislation, amendments, and authoritative legal sources.

The project is designed as an information and research assistant, not as a replacement for qualified legal professionals.

### AI Workflow Security Toolkit

A focused toolkit for safer automation workflows, covering input limits, structured-output validation, prompt-injection detection, controlled failures, confidence scoring, and human-review flags.

## Production architecture

The portfolio intentionally uses a zero-runtime-dependency static architecture:

- Semantic HTML5
- Modern CSS with responsive layouts and light/dark themes
- Small, dependency-free JavaScript modules
- Content Security Policy restricting assets to the same origin
- Progressive enhancement, so core content remains visible without JavaScript
- Reduced-motion support
- Keyboard-accessible navigation and controls
- Open Graph and Twitter metadata
- Web app manifest, favicon, robots file, sitemap, and custom 404 page
- Automated validation and GitHub Pages deployment through GitHub Actions

This architecture removes browser-side Babel compilation, runtime Tailwind generation, and third-party JavaScript CDN dependencies.

## Repository structure

```text
.
├── .github/
│   ├── dependabot.yml
│   └── workflows/pages.yml
├── assets/
│   ├── css/styles.css
│   ├── icons/favicon.svg
│   └── js/
│       ├── main.js
│       └── theme.js
├── images/
│   ├── Bless-Dark.png
│   └── Bless-White.png
├── scripts/validate_site.py
├── .nojekyll
├── 404.html
├── index.html
├── robots.txt
├── SECURITY.md
├── sitemap.xml
└── site.webmanifest
```

## Local development

Run a local static server from the repository root:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000
```

Opening `index.html` directly may limit clipboard functionality because some browser APIs require a secure origin or localhost.

## Validation

Run the built-in site checks:

```bash
python scripts/validate_site.py
node --check assets/js/theme.js
node --check assets/js/main.js
```

## Deployment

The `.github/workflows/pages.yml` workflow validates the source, creates a controlled deployment artifact, and publishes it through GitHub Pages.

In the repository settings, set:

```text
Settings > Pages > Build and deployment > Source > GitHub Actions
```

## Security and privacy

The site has no analytics, authentication, database, contact form backend, cookies, or third-party JavaScript. Contact actions use email links and the browser clipboard API.

See [SECURITY.md](SECURITY.md) for vulnerability reporting guidance.

## Author

Devine Enukorah

- GitHub: <https://github.com/DevineEnukorah>
- LinkedIn: <https://www.linkedin.com/in/DevineEnukorah>
