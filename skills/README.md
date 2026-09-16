# Runtime Skills

This directory contains reusable procedural skills consumed by the **harness itself**.

It is intentionally separate from `.claude/skills/`, which contains playbooks used by coding agents while developing this repository.

The runtime loads skills on demand through:

```text
skill_list
skill_load
```

Available initial skills:

- `create-blender-prop` — create/save/export/render Blender game props through harness tools.
- `import-asset-to-unity` — import/configure/place assets through filesystem + Unity Editor APIs.
- `browser-research` — gather information using semantic browser operations while avoiding account side effects.

Skills are procedures, not executable plugins. Security and side-effect enforcement remain in tools, permissions and runtime hooks.

Add a new runtime skill only when a repeatable workflow benefits from procedural guidance. Do not copy general architecture or permanent project rules into runtime skills.

See `SKILLS_HOOKS.md` for the distinction between skills, tools, and hooks.
