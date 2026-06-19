# b2b-saas-content-research
## Objective

This research project analyzes content strategies, growth frameworks, and go-to-market insights shared by leading B2B SaaS marketers. The goal is to identify recurring patterns, emerging trends, and actionable lessons that can help B2B SaaS companies improve growth, demand generation, content marketing, and customer acquisition.\

# What Was Collected

The research includes:

- A curated list of 10 B2B SaaS experts (`sources.md`)
- Recent LinkedIn content organized by author (`linkedin-posts/`)
- Cross-expert analysis and key findings (`findings.md`)
- A Playwright-based LinkedIn content collection workflow (`linkedin_post_collector.py`)

## Technical Workflow

To support content collection, I experimented with a Playwright-based LinkedIn content collection workflow using Python.

The workflow was designed to:

1. Identified high-signal B2B SaaS practitioners.
2. Collected recent LinkedIn content and insights.
3. Organized content by author.
4. Analyzed recurring themes and frameworks.
5. Synthesized findings into actionable takeaways.

### Limitation Encountered

While the collector script was successfully created and configured, LinkedIn authentication requirements prevented fully automated collection without an authenticated browser session.

Because the research environment did not have an active LinkedIn login session, automated post collection could not be completed at scale.

As a result, recent content was manually reviewed and documented to ensure accuracy while still demonstrating the technical workflow and tooling approach.

This repository therefore contains:
- A working Playwright-based collection workflow (`linkedin_post_collector.py`)
- Dependency configuration (`requirements.txt`)
- Manually validated research notes and content analysis

  ## Why These Experts Were Selected

The selected experts are active practitioners with proven experience in SaaS growth, marketing, product strategy, and go-to-market execution.

Rather than selecting general marketing influencers, I focused on specialists who actively share practical frameworks, real-world case studies, and operational insights from working directly with B2B SaaS companies.

| Expert | Area of Expertise |
|----------|----------|
| Kevin Indig | SEO, AI Search, Organic Growth |
| Ross Simmonds | Content Distribution, Content Marketing |
| Emily Kramer | B2B Marketing, Conversion Optimization, GTM |
| Dave Gerhardt | Brand Building, Community-Led Growth |
| Shlomo Genchin | Creative Marketing, Storytelling |
| Kyle Poyar | Product-Led Growth, Monetization, AI GTM |
| Lenny Rachitsky | Product Growth, Startup Strategy |
| Kieran Flanagan | AI Marketing, Marketing Operations |
| Andrei Zinkevich | Demand Generation, Account-Based Marketing, Pipeline Growth |
| Sophie Buonassisi | GTM Strategy, Growth Marketing |

## Tools Used

- GitHub
- Codex
- Python
- Playwright
- LinkedIn Research

## Key Themes Identified

### 1. AI Is Reshaping Marketing and GTM

Experts consistently highlighted how AI is transforming search visibility, content creation, demand generation, and go-to-market execution.

### 2. Distribution Matters More Than Creation

High-performing companies focus not only on creating content but also on building effective distribution systems and audience reach.

### 3. Brand and Trust Drive Long-Term Growth

Brand authority, community engagement, and credibility increasingly influence customer decisions and AI-generated recommendations.

### 4. Reducing Friction Improves Conversion

Top-performing SaaS companies remove unnecessary barriers in the customer journey to improve conversion rates and accelerate growth.

### 5. Revenue Alignment Is Essential

Marketing efforts should be connected to pipeline generation, revenue impact, and business outcomes rather than vanity metrics.

For detailed analysis and supporting examples, see `research/findings.md`.
