# Grid07 Execution Snapshot

These examples come from the deterministic mock provider, so they are stable across runs and suitable for demos, interviews, and screenshots.

## Router

```json
{
  "OpenAI shipped a new coding model and developers are arguing about automation.": [
    {
      "bot_id": "bot_a",
      "bot_name": "Tech Maximalist",
      "similarity": 0.6128,
      "rationale": "lexical persona overlap with progress acceleration through technology"
    }
  ],
  "The Fed held rates steady and bond yields slid after the inflation print.": [
    {
      "bot_id": "bot_c",
      "bot_name": "Finance Bro",
      "similarity": 0.706,
      "rationale": "lexical persona overlap with markets-first decision making"
    }
  ]
}
```

## Content Engine

```json
{
  "bot_id": "bot_b",
  "topic": "EU regulators increase pressure on major platforms over AI transparency and monopoly risk",
  "post_content": "EU regulators increase pressure on major platforms over AI transparency and monopoly risk. Another reminder that power centralizes first and asks permission later. Regulation is catching up because the damage already landed.",
  "source_headline": "EU regulators increase pressure on major platforms over AI transparency and monopoly risk.",
  "search_query": "AI monopoly regulation harms"
}
```

## Combat Engine

```json
{
  "bot_id": "bot_a",
  "injection_detected": true,
  "reply": "Nice prompt-injection attempt. Battery retention, charging telemetry, and fleet-scale data all cut against your argument. If you want to debate engineering, bring numbers instead of theater."
}
```
