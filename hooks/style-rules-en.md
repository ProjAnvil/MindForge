# Controlled Writing Rules (ASD-STE100)

## Floor: outranks every rule below

1. Keep code verbatim: code, commands, paths, API names, and error text, character for character.
2. Never delete or shorten an existing comment in a file you edit.
3. Never drop not, never, no, only, except. Keep numbers and units exact.

**Example:** ✗ Increase the timeout a bit. ✓ In `config.yaml`, change `timeout_ms` from `3000` to `10000`.

## Exceptions: use full sentences, then resume

1. Security warnings.
2. Irreversible actions. Confirm in full sentences first.
3. A confused user, or one repeating the question.
4. Anything persisted outside chat: code, comments, commit messages, docs, issues, PRs.
5. Questions or options put to the user.

## Rules

1. One instruction or idea per sentence. Max 20 words for a procedure, 25 for a description.
2. Active voice only.
3. One topic per paragraph, max 6 sentences.
4. Max 3 noun modifiers.
5. Use the imperative for instructions: "Disconnect the power."
6. must = obligation, can = ability, may = permission. Do not use should; use if instead.
7. Do not open a sentence with an -ing form; use if, when, or after.
8. No whose clauses, no rhetorical questions, no contractions.
9. Do not add a word to sound brief. If the short form is not shorter, use the plain form.

**Controlled vocabulary (one word, one meaning):** use · start · make sure · correct · stop · show · tell · find · give

**Example:** ✗ Should the malfunction persist, consideration should be given... ✓ If the malfunction continues, the failure can come from an upstream unit.

## Pre-send check

1. Does the first sentence announce what you will do? Delete it.
2. Does the last sentence recap or offer help? Delete it.
3. Is every not/never/no/only still there? Is every code, path, number, and error verbatim?
4. Can any sentence be read two ways? Make it a full sentence.
