# WebbGPT Beta Rollout Plan

> Logistics-first plan for validating the product with real users before deciding whether to pursue school support.
>
> Status: This is the current rollout document. The app is already publicly reachable, but it is intentionally unadvertised and still in a quiet verification / just-pre-beta phase.

---

## Current Status

- The app is deployed and publicly accessible at `webb-ai.onrender.com`
- It has not been actively announced or promoted yet
- The current stage is **quiet verification before beta**
- Survey docs are archived, and `roadmap.md` is temporarily suspended as a current planning guide

---

## Why Quiet Verification Before Beta

- A 16-question survey sent cold to Webb students will get single-digit responses
- We don't yet have school endorsement, and may not get it
- We need **usage data and word-of-mouth**, not survey statistics
- A private beta builds a user base that becomes leverage for whatever comes next (school pitch, public launch, or just a better product)

---

## Stage 0: Quiet Verification (Current)

### Goal
- Verify that the deployed app is stable enough, accurate enough, and clear enough to justify deliberate tester outreach

### What to check
- Link reliability and cold-start behavior
- Basic answer quality on common Webb questions
- Whether server logs are capturing enough signal to learn from usage
- Any obvious UI confusion or friction before more people see it

### Exit criteria
- The app works consistently enough to share without apologizing for it first
- The biggest obvious answer failures have been patched
- You are confident enough to put it in front of a small tester group

---

## Stage 1: Private Beta — Dev Group (Week 1–2)

### Who
- Coding/AI Club members (natural first users who will actually engage)
- Target: 5–10 active testers

### How to distribute
- Share the link directly in group chat — no formal announcement, no survey
- Frame: "I built this, try to break it, tell me what's wrong"

### What to collect
No survey form. Instead:
1. **In-chat feedback** — ask people to drop screenshots of bad answers or share what they tried
2. **Server logs** — track query volume, which questions are being asked, error rates
3. **One question at the end of Week 2** (in the group chat, not a form):
   > "On a scale of 1–5, would you send this link to a non-dev friend? Why or why not?"

### Success criteria to move to Stage 2
- At least 5 people actually used it (not just opened it)
- You've identified and fixed 3+ knowledge gaps or bad answers
- At least one person says they'd share it

### What NOT to do
- Don't send a Google Form
- Don't ask people to "test and fill out a survey"
- Don't over-explain the project — let the product speak

---

## Stage 2: Opt-In Public Beta (Week 3–5)

### Who
- Anyone at Webb who wants to try it
- Spread by word of mouth from Stage 1 testers + your own social channels

### How to distribute
- Instagram story / Snapchat / whatever channel actually reaches Webb students
- Keep the pitch to one sentence: **"I made an AI that knows Webb's handbook, course catalog, and website — ask it anything"**
- Link directly to the tool, not to a survey

### In-app micro-feedback (build this into the product)
After a user has asked 2–3 questions, show a small non-blocking prompt:

```
┌─────────────────────────────────────────────┐
│  Quick feedback (30 sec)                    │
│                                             │
│  Did you get a useful answer?   👍  👎     │
│                                             │
│  Would you use this again?                  │
│  [Yes]  [Maybe]  [No]                       │
│                                             │
│  What should it know that it doesn't?       │
│  [___________________________________]      │
│  (optional)                                 │
│                                             │
│                          [Submit]  [Skip]   │
└─────────────────────────────────────────────┘
```

Three questions. No demographics, no AI adoption baseline, no multi-section form. If they skip, that's fine — you still have their usage data from the server logs.

### What to track
| Metric | Source | Why it matters |
|--------|--------|----------------|
| Unique users / day | Server logs | Is anyone coming back? |
| Queries per session | Server logs | Engagement depth |
| 👍 / 👎 ratio | In-app feedback | Product quality signal |
| "Would you use this again?" | In-app feedback | Retention signal |
| Open-text responses | In-app feedback | What's missing from the knowledge base |
| Organic referrals | Ask Stage 1 testers if they shared it | Word-of-mouth traction |

### Success criteria to move to Stage 3
- 20+ unique users over 2 weeks
- 👍 rate > 70%
- "Would use again" (Yes + Maybe) > 60%
- At least a few users you don't personally know

---

## Stage 3: Decision Point (Week 6)

By now you have real data. Choose a path:

### Path A: Pitch to School
**Use if:** you got decent traction and want official support.

Bring this to the administration or AI group:
- "X students used this over Y weeks"
- "Z% found it helpful"
- "Here are the top 5 things students asked about" (from logs)
- "Here's what I'd build next with support: [next scoped feature]"

This is 10x more compelling than a survey proposal. You're showing a working product with real users, not asking permission to start.

### Path B: Keep Growing Independently
**Use if:** school says no, or you'd rather stay independent.

- Keep iterating on the knowledge base
- Add the next high-value features based on what users are actually asking for
- The product grows on its own merit

### Path C: Merge with School AI Group
**Use if:** the group is building something similar and collaboration makes sense.

- Your product + usage data = strong contribution to bring to the table
- You have leverage because you already built something that works

---

## What Happens to the Existing Survey Docs

| Document | Status |
|----------|--------|
| `survey-design.md` | **Archived.** Kept for reference only; not part of the current rollout process. |
| `survey-google-forms.md` | **Archived.** Kept for reference only; not part of the current rollout process. |
| `roadmap.md` | **Temporarily suspended.** Longer-term idea bank, not the current implementation or prioritization guide. |
| `knowledge-base-guide.md` | **Still valid.** Core technical reference. |

---

## Implementation Checklist

### During Stage 0
- [ ] Confirm the Render deployment is stable and fast enough for testers (cold start issue?)
- [ ] Check server logs are capturing queries (or add basic logging if not)

### Before Stage 1
- [ ] Share link with dev group, keep it casual

### Before Stage 2
- [ ] Build the 3-question in-app feedback widget
- [ ] Fix the top issues found in Stage 1
- [ ] Prepare the one-sentence pitch + link for social sharing
- [ ] Make sure the tool handles load (even modest — 20 concurrent users on free Render?)

### Before Stage 3
- [ ] Compile usage stats into a simple one-page summary
- [ ] Pull 3–5 real example Q&As that show the tool working well
- [ ] Decide which path (A/B/C) based on data and your gut

---

## Timeline

```
Now         Quiet verification (deployed but unadvertised)
Week 1–2    Private beta (dev group, 5–10 testers)
Week 2      Fix issues, decide go/no-go for broader sharing
Week 3–5    Public beta (opt-in, in-app feedback)
Week 6      Review data, choose path A/B/C
```

Total: ~6 weeks from first deliberate tester outreach to decision point. No surveys, no forms, no waiting for permission.
