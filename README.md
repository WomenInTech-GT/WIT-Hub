# WIT Student Technology Hub

A student-built web platform where Georgia Tech students discover Women in Tech (WIT) events and programs, technical opportunities, student projects, and career resources.

**Live site:** [URL]
**Status:** MVP in development

## Why this exists

WIT events and technical opportunities (research, internships, hackathons, competitions, scholarships) are scattered across social media, emails, and department pages. This hub is the single source of truth. Instagram and other channels drive students here.

## What it does

- Directory of WIT events, programs, and technical opportunities
- Showcase of student technical projects
- Search and filtering (type, major relevance, year, deadline)
- "Find Something for Me" guided recommendations (rule-based in the MVP; AI and semantic recommendations planned for a later phase)
- Responsive, accessible design (target: WCAG 2.1 AA)
- Content update workflow that doesn't require coding
- Privacy-conscious usage analytics

## Team

We're a flat team with five areas of ownership. Everyone contributes across the product and joins code reviews, testing, and demos.

| Name | Starting focus |
|---|---|
| Haoran Duan | AI & Data: backend, database, API, deployment |
| Grace Wang | AI & Data / Full Stack: search, filtering, recommendations |
| Livia Kouts | Website Development: UI/UX, frontend |
| Qiao Yi Tan | Website / Product: frontend, analytics |
| Jiyeong Hong | Technical Content & Projects, QA: content library, schema, testing |

Areas: Website Development, AI & Data, Product & User Research, Technical Content & Projects, Digital Outreach.

## Tech stack

- **Frontend:** [e.g., React]
- **Backend/API:** [e.g., Node/Express or Python/FastAPI]
- **Database:** [e.g., PostgreSQL]
- **Hosting/CI/CD:** GitHub Actions + [Vercel / Netlify / Render]

## Repository structure

```
/frontend    Website UI
/backend     API and database
/search      Search logic, recommendation scoring config, test queries
/content     Seed data and content schema
/docs        Architecture, research, test plans, decision records
/.github     Workflows, issue and PR templates, CODEOWNERS
```

## Getting started

```bash
git clone [repo URL]
cd [repo name]

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd ../backend
[install and run commands]
```

Copy `.env.example` to `.env` and fill in the values. Never commit secrets.

## How we work

**Workflow:** Discover → Design → Build → Test → Launch → Improve

1. Pick or create an issue on the project board, labeled by area and attached to a milestone.
2. Create a branch: `yourname/short-description`.
3. Open a pull request using the PR template. Include how to test it and screenshots for UI changes.
4. At least one teammate reviews, and CI must pass before merging to `main`.
5. Merges to `main` deploy automatically.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Adding or updating content

Content lives in `/content` as structured files validated against the schema in CI.

1. Submit an opportunity or project using the **Content submission** issue form.
2. A content reviewer checks it against the quality checklist: working link, verified deadline, named source.
3. Once approved and merged, the site redeploys with the new entry.

## Reporting bugs

Open an issue with the **Bug** template. Include steps to reproduce, expected vs. actual behavior, and severity (blocker, major, minor).

## MVP timeline (6 weeks)

| Weeks | Focus |
|---|---|
| 1-2 | Discover and plan: student interviews, resource audit, requirements, user flows, architecture |
| 3-4 | Design and build: wireframes, database, responsive site, directory, search/filter, admin workflow, initial content, analytics |
| 5-6 | Test and launch: usability testing, accessibility review, bug fixes, documentation, launch campaign, demo |

## Success criteria

- Deployed MVP that students use to find opportunities
- Content that can be maintained after this cohort
- Basic usage data to guide improvements
- Meaningful technical ownership for each ambassador

## Roadmap (after MVP)

- Semantic search and AI-based recommendations
- Richer admin interface
- Expanded content from more student orgs and departments

## Privacy

Analytics are anonymous. We do not collect names or emails through search or recommendations.

## Contact

[WIT ambassador team email or Instagram handle]