<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->




# Factora Frontend Agent Instructions

## Project

Factora is an invoice-financing marketplace for SMEs.

The frontend is built with Next.js, TypeScript and Tailwind CSS.

## Scope

- Work only inside the frontend unless explicitly instructed otherwise.
- Do not modify backend files.
- Do not introduce unnecessary dependencies.
- Prefer simple, reliable implementations suitable for a hackathon.

## Code

- Use TypeScript.
- Keep components modular and reusable.
- Avoid putting an entire page in one large component.
- Use English for component names, variables, interfaces and routes.
- Use Spanish for visible UI text.
- Use mock data when backend endpoints are not available.
- Preserve the existing project structure whenever possible.

## Styling

- Follow visual references stored under `references/`.
- Use a clean fintech SaaS design.
- Desktop is the main demo target, but preserve reasonable responsive behavior.
- Use white or very light neutral backgrounds.
- Use dark navy for primary text.
- Use lime as the primary Factora accent.
- Use semantic pastel colors:
  - Lime: best offer / recommended
  - Blue: lowest commission
  - Purple: highest advance
  - Orange: fastest funding
- Cards should remain primarily white.
- Use rounded cards, subtle borders and subtle shadows.
- Do not add decorative elements that are not present in the approved reference.

## Validation

Before completing a task:

- Run the project lint command.
- Run the production build.
- Fix errors caused by the implementation.
- Do not modify unrelated files.