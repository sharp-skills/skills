# Examples — registry-ssot

Run the self-test (no network, stdlib only):

```bash
sh selftest.sh
```

| Registry | What it demonstrates | Expected |
|---|---|---|
| `registry.good.json` | Wired 3-agent pipeline + wildcard observer + derived bus graph | exit 0 |
| `registry.bad.json` | Orphan subscriptions (typo'd / legacy event), dead-end publishes, bus graph drifted from the registry | exit 1 |

The bad registry's defects are the drift classes that motivated deriving the
bus graph from the registry in the first place.
