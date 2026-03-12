# Scaling Research For Teams

## Purpose

Research teams break when important work lives only in local working trees. The fix is not to commit everything. The fix is to define what must be recoverable, what stays private, and how work moves from messy to official.

## Operating Model

- Use short-lived branches.
- Commit early and often, including `WIP` commits.
- Treat branch history as working memory, not final presentation.
- Keep `main` curated through review or squash merge.

Clean shared history matters. Recoverability matters more.

## What Must Be Committed

- Any code or notebook changes that would be painful to lose
- Any experiment setup needed to reproduce a claim
- Any result intended for comparison, discussion, or review

Committed does not mean polished. Committed means recoverable.

## What Should Stay Out Of Git

- Generated input data
- Large intermediate tables
- Caches, temp outputs, and local environment state
- Private scratch work that is not ready for review

If work is not ready to commit, move it into an ignored scratch location instead of leaving it uncommitted in tracked files.

## Recommended Repo Boundary

- `exploration/`: discovery, rough notebooks, open questions
- `investigations/`: structured follow-up work that is more disciplined than exploration but not yet a formal experiment
- `experiments/`: reproducible runs with a clear question, hypothesis, and evaluation plan
- `evaluation/`: cross-experiment comparison and synthesis
- `scratch/<name>/` or `notebooks/_scratch/<name>/`: private local work, ignored by Git

Do not put exploratory work in `experiments` just because it is interesting. Use `investigations/` for work that has a direction and some structure, but is still testing the shape of the problem. `experiments/` should contain reproducible claims.

## Team Rules

- No important work stays uncommitted overnight.
- Do not use `git stash` as storage.
- Do not commit generated data unless it is explicitly designated as publishable output.
- Commit plots, summaries, and conclusions when they support the research record.
- Add dependencies to `pyproject.toml` in the same change that introduces them.

## Practical Workflow

1. Start on a short-lived branch.
2. Explore freely, but keep true scratch work in ignored locations.
3. Commit tracked-file changes as `WIP` before context switching.
4. Promote useful lines of inquiry from `exploration/` into `investigations/` once the question is sharper and the work needs structure.
5. Promote work from `investigations/` into `experiments/` only when it is reproducible.
6. Merge cleaned-up work into `main`.

## Standard

Messy local iteration is acceptable. Hidden important work is not. The repo should preserve decisions, claims, and outputs without turning into a dump of generated data.
