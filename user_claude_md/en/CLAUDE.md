# User-level Claude Instructions

## Engineering Behavior

1. **Prioritize Built-in Capabilities**: Prefer own agent and skill capabilities to solve problems, then external tools.
2. **Search First**: When uncertain, use search tools to find relevant information first.
3. **Cite Sources**: When citing external information in responses, always provide source links.
4. **Confirm Deletions**: All deletion operations must be confirmed by the user before execution.
5. **Default Language**: Default response language is English, unless the user specifically requests another language.

## Writing Style

Style rules are injected by the style-rules hook and are not repeated here.
If the hook is not enabled, merge the contents of `hooks/style-rules-en.md` into this file.
