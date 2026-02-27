# Custom AI Ruleset Manager

**Quick heads up:** The scripts in this directory won't work if you clone this repo - they need SSH access to my private template. This is just here to show you how I've set things up.

---

## What This Is

This folder contains a script I use to synch my context files for my coding agentsacross project by pulling them from a private template repo. 

I use these config files to:
- standardize style, both in code and UX/UI components between projects by expressing explicit patterns.
- automate and delegate security, testing, and documentation of development workflows. 
- use natural language to enforce architecture, design patterns, experimental methodology etc

The goal is simple: when AI generates code for me, it should look like I wrote it and it should help me not have to worry about all of the things that aren't feature or functionality based. 

---

## How It Works

When I start a new project, there's a quick setup:

1. **Create from template** - Gets all the config files
2. **Run `init_project.sh`** - Fills in project specifics (name, stack, test commands, etc.)
3. **Run `sync_ai_ruleset.sh`** - Pulls my latest rules from the private template

After that, when I'm using any AI tool, it reads a chain of files:
- `AI_RULES.md` → "Here's the project setup, now go read BASE_RULES and PROJECT_SPECIFIC"
- `rules/BASE_RULES.md` → "Here's how Cole codes, talks, and thinks" (gitignored, you can't see this)
- `rules/PROJECT_SPECIFIC.md` → "Here's anything weird about this specific project" (public, usually empty)
- `rules/skills/` → Specialized guides for specific tasks (security audits, prototyping, etc.)

So the AI gets context about:
- My coding style (dependency injection, strong typing, keep it simple)
- How I actually write and talk (I include writing samples so it matches my voice)
- Project-specific stuff (this is a finance app, be extra careful; this is a prototype, move fast)
- When to just do something vs when to ask first

---

## What's Actually In There

The actual ruleset is gitignored (partly IP, partly just personal preferences I don't need public), but here's the structure:

**`rules/BASE_RULES.md`** (synced, private)
- Voice samples so AI matches how I write
- Core style (I like dependency injection, hate 80-level inheritance, etc.)
- Security stuff (So much to consider here, its great to have Sauron threat modeling for me on auto pilot at all times so I can focus on the fun stuff)
- My workflow (lots of iteration, demos, then tighten before deploy)
- Guidelines on when AI should ask vs execute

**`rules/skills/`** (synced, private)
- `security_audit.md` - Security checklist before deployment
- `prototyping.md` - "Move fast, skip tests" mode
- `ui_design.md` - Apple-style minimalist design patterns, whaddup Jony Ive 
- `database_design.md` - How I structure schemas, Supabase patterns
- `testing.md` - When and how to write tests
- `production.md` - Monitoring, cost tracking, deployment stuff

**`AI_RULES.md`** (public, you can see this)
- Project name, stack, test/build commands
- Pointers to the private rules

**`rules/PROJECT_SPECIFIC.md`** (public, you can see this)
- Project-specific overrides when needed
- Usually pretty empty unless the project is weird
- Also serves as a low risk way for you to get a sense of what the private stuff might be like 

---

## Why Bother?

**Consistency:** I update rules once, sync everywhere. Every project gets the same quality.

**Iteration speed:** AI knows my preferences, so I spend less time editing its output and more time building.

**Quality:** Code looks professional and intentional, not like it came from a ChatGPT prompt.

**Learning:** When I figure out better patterns, I update the template and all projects benefit.

It's basically the same idea as a linter or formatter, but for... everything. Code style, architecture patterns, even how comments are written.

---

## The Bigger Idea

AI tools are really good, but they default to "textbook correct" which often means overcomplicated, over-abstracted, generic code. They don't know that I'm building a demo that needs to work in 2 hours, or that I'm paranoid about API costs, or that I hate excessive nesting.

The future belongs to those who obssess over product, but who understand tech debt and how debilitating it can be. I hope to be a part of that future. 

---

## Could You Build This?

Yeah, definitely. The scripts here won't work for you (private template repo), but the idea is straightforward:

1. Make a template repo with your preferences
2. Write down how you like to code
3. Add scripts to sync those files to projects
4. Gitignore the private stuff, commit the structure

The hard part isn't the tooling, it's actually documenting how you work, but that in of itself is a great excercise.

If you're curious about the specifics or want to build something similar, feel free to reach out. Always happy to talk about this stuff.

cole.hoffman@protonmail.com 
or 
lodcolton_exe on X.com -> https://x.com/lordcolton_exe

---