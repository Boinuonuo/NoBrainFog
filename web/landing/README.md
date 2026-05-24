# NoBrainFog Landing Page

This directory contains a small static landing page for NoBrainFog.

It is intentionally independent from the Python bot runtime. You can host it with any static hosting service, including Cloudflare Pages, GitHub Pages, Nginx, or a simple local HTTP server.

## Files

```text
web/landing/index.html
web/landing/style.css
web/landing/app.js
```

## Local preview

From the repository root:

```bash
python3 -m http.server 8090 --directory web/landing
```

Then open:

```text
http://localhost:8090
```

## Cloudflare Pages

Recommended settings:

```text
Build command: leave empty
Build output directory: web/landing
```

## Notes

This page is only a public project introduction. It does not read or write `todo.md`, does not expose private config, and does not connect to Discord or WeChat Work.
