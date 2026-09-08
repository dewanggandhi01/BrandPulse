# ADR 001: Monorepo Structure

## Status
Accepted

## Context
BrandPulse is a complex platform involving a frontend, a backend API, and several background workers (scraping, analysis, etc.). We needed to decide on a repository structure that supports efficient development, code sharing, and deployment across these different components.

## Decision
We will use a monorepo structure containing all core components (`frontend`, `backend`, `workers`) managed at the root level.
We are integrating Python dependencies with a root `pyproject.toml` and utilizing `pnpm-workspace.yaml` and `turbo.json` for frontend package management and task orchestration.

## Consequences

### Positive
- **Unified Versioning & Deployment:** Easier to coordinate changes spanning the frontend, backend, and workers simultaneously.
- **Shared Configuration:** Root level configs for tools (e.g., linting, pre-commit) ensure consistency across the codebase.
- **Streamlined Onboarding:** A single repository and root `docker-compose.yml` makes it very easy for new developers to spin up the entire stack.
- **Simplified CI/CD:** A single pipeline can build, test, and deploy all components in an orchestrated fashion.

### Negative
- **Repository Size:** Over time, the repository might grow large, potentially slowing down git operations.
- **Tooling Complexity:** Setting up tooling that spans multiple languages (Python, TypeScript) can sometimes be tricky and requires careful configuration (e.g., Turborepo with Python).
- **Coupling:** Increased risk of unintended coupling between components if boundaries are not strictly enforced.

## Alternatives Considered

- **Polyrepo (Multiple Repositories):** Separate repositories for frontend, backend, and workers. 
  - *Rejected because:* Adds significant overhead for cross-component changes, version tracking, and local development setup.
- **NX Monorepo:** Using NX as the primary build system.
  - *Rejected because:* Turborepo is lighter and easier to configure for our specific use case, especially with a mixed Python/Node.js stack.
