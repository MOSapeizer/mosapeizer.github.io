# Project: Mos's Personal Blog

## Overview
This is a personal blog built with [Hugo](https://gohugo.io/). The site shares thoughts, experiences, and technology-related discussions. It uses the `terminal` theme and is configured for Traditional Chinese (`zh-tw`).

## Technology Stack
- **Static Site Generator**: Hugo
- **Templating**: Go Templates (HTML), Markdown
- **Theme**: terminal

## Directory Structure
- `content/`: Contains the markdown content for the site.
  - `posts/`: Blog posts.
- `themes/`: Contains the site themes (`themes/terminal`).
- `static/`: Static assets (images, CSS, JS) copied directly to the build.
- `layouts/`: Custom layout overrides.
- `hugo.toml`: Main project configuration file.

## Configuration Highlights (`hugo.toml`)
- **Base URL**: `https://mossie.dev/`
- **Language**: `zh-tw`
- **Title**: Mos 的個人部落格
- **Main Menu**:
  - Home (`/`)
  - Posts (`/posts/`)
  - About (`/about`)
- **Parameters**:
  - `pagerSize`: 5
  - `unsafe` markup enabled (for raw HTML in markdown).

## Development Commands

### Start Local Development Server
Starts the server with live reload.
```bash
hugo server
```

### Build for Production
Builds the static site to the `public/` directory.
```bash
hugo
```

## Content Guidelines
- Write posts in `content/posts/`.
- Use Markdown.
- Frontmatter format: TOML/YAML (check existing files for consistency).
- Images should ideally be placed in `static/` or page bundles.
