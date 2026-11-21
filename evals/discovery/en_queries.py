"""English L1 discovery queries for the MindForge skill catalog.

Use with::

    uv run smelt discover ../skills/en \
        --distractors discovery/distractors/en \
        --queries discovery/en_queries.py --repeat 2

Query text describes a task scenario. It must not copy a skill description.
The 15 train rows are for iteration; the 11 test rows are the CI gate.
"""

from smelt import discovery_query

queries = [
    discovery_query(
        "Our checkout keeps double charging. Draw the tables and keys for orders and payments first.",
        gold=["database-design"], kind="positive", split="train", name="db-orders",
    ),
    discovery_query(
        "Pick a reusable structure for a checkout flow with many if-else branches.",
        gold=["design-pattern"], kind="paraphrase", split="test", name="pattern-checkout",
    ),
    discovery_query(
        "Our Java service freezes when virtual threads enter synchronized code.",
        gold=["enterprise-java"], kind="positive", split="test", name="java-pinning",
    ),
    discovery_query(
        "Add a data fetching form to a server-rendered route in our Next.js app.",
        gold=["frontend-react"], kind="positive", split="train", name="react-route",
    ),
    discovery_query(
        "Build a single-file form component for a SvelteKit route.",
        gold=["frontend-svelte"], kind="positive", split="test", name="svelte-form",
    ),
    discovery_query(
        "Two pages in our Nuxt app must read the same store. Wire it up.",
        gold=["frontend-vue"], kind="positive", split="train", name="vue-store",
    ),
    discovery_query(
        "Find the commit that broke the build, then tidy the recent commits.",
        gold=["git-guru"], kind="paraphrase", split="test", name="git-regression",
    ),
    discovery_query(
        "A background worker outlives its request because cancellation is ignored.",
        gold=["go-development"], kind="positive", split="train", name="go-cancel",
    ),
    discovery_query(
        "Tighten this module so the compiler rejects mixed value types.",
        gold=["javascript-typescript"], kind="paraphrase", split="train", name="ts-strict",
    ),
    discovery_query(
        "We need versioned public endpoints with safe retries for comments.",
        gold=["api-design"], kind="positive", split="test", name="api-comments",
    ),
    discovery_query(
        "Write the one-page brief for a password reset feature and the smallest first release.",
        gold=["product-management"], kind="positive", split="train", name="pm-reset",
    ),
    discovery_query(
        "My iterator produces nothing on the second pass through the loop.",
        gold=["python-development"], kind="positive", split="test", name="py-generator",
    ),
    discovery_query(
        "Prepare a handover note so tomorrow's session starts with the same context.",
        gold=["session-summary"], kind="positive", split="train", name="handover",
    ),
    discovery_query(
        "Two tasks mutate one model and the compiler reports a data race.",
        gold=["swift-development"], kind="positive", split="test", name="swift-race",
    ),
    discovery_query(
        "Show a scrollable list of items with a detail screen in our iOS UI.",
        gold=["swiftui-development"], kind="paraphrase", split="train", name="swiftui-list",
    ),
    discovery_query(
        "Document the choice between two system designs as an ADR.",
        gold=["system-architecture"], kind="positive", split="test", name="adr",
    ),
    discovery_query(
        "Give the operations team a rollout guide and a runbook for alerts.",
        gold=["tech-documentation"], kind="paraphrase", split="train", name="runbook",
    ),
    discovery_query(
        "Cover the discount calculator with unit cases before the release.",
        gold=["testing"], kind="positive", split="test", name="unit-cases",
    ),
    discovery_query(
        "A newly added source file is missing from the Xcode project navigator.",
        gold=["xcode-management"], kind="positive", split="train", name="xcode-file",
    ),
    discovery_query(
        "Forward this invoice PDF to the client without changing any content.",
        kind="near-miss", split="test", name="forward-pdf",
    ),
    discovery_query(
        "Recommend a coffee shop near the train station.",
        kind="near-miss", split="train", name="coffee",
    ),
    discovery_query(
        "What is the weather in Shanghai tomorrow?",
        kind="none", split="test", name="weather",
    ),
    discovery_query(
        "Compute the area of a circle with radius seven.",
        kind="none", split="train", name="math",
    ),
]
