# Runtime Skills

This directory is reserved for reusable procedural skills consumed by the **harness itself**.

It is intentionally separate from `.claude/skills/`, which contains playbooks used by coding agents while developing this repository.

The runtime skill loader is **not part of the first MVP milestone**. Do not add runtime skills until repeated workflows justify them.

Candidate future skills include:

- `create-blender-prop`
- `import-asset-to-unity`
- `inspect-unity-scene`
- `browser-research`
- `debug-unity-console`
- `generate-texture`
- `verify-game-object`

See `SKILLS_HOOKS.md` for the distinction between skills, tools, and hooks.
