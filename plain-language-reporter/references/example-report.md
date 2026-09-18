# Example Report

Read this when the template alone is not enough and you want to see the tone and
the level of detail in a finished report.

The report below is a sample, not a record of real measurements. It shows the
shape; the content of a real report must come from real evidence.

---

# Product photos on social posts

**Result.** We looked at why some product photos look cropped on the customer's
social media posts. Photos are produced as a square, but the post format is
taller than a square, so the sides get trimmed. We recommend producing a second,
taller version for social posts and keeping the square one for the website.

---

## Findings

### Finding 1 — The photo is square, the post is not

**What happened:** Our photos are produced as squares, while the social post
frame is taller than it is wide.

**Why it matters:** The brand mark and the price badge sit near the edges, so
they are the first things cut off — exactly the parts the customer cares about.

**Example:** In one campaign post, the price badge is cut in half down the
middle, and the logo in the corner disappears completely.

**Recommendation:** Produce a second, taller version of the photo for social
posts and leave the square version untouched for the website. This fixes the
crop, not the underlying fact that one image is reused everywhere.

### Finding 2 — Records with no delivery region never reach the results

**What happened:** When a record has no delivery region, it is dropped from the
result list entirely instead of being shown without that detail.

**Why it matters:** A product the customer paid to promote can silently never
appear, and nobody sees an error to explain why.

**Example:** In one search, 3 records out of 12 were missing the region field
and none of them appeared in the output.

**Recommendation:** Show the record anyway and hide only the region line.

**Not certain yet:** We have not checked whether the same filter runs on other
result lists, so the effect may be wider than this one search.

---

## Decisions needed

> If you agree with all recommendations: **1A 2A**

**1. Where should the taller photo be produced?**
- **A) In our own service, next to the square one** — one place to change, adds a
  little processing time *(recommended)*
- B) On the social media tool's side — no change for us, but we lose control over
  how the crop looks

**2. What should happen to a record with no delivery region?**
- **A) Show it, hide the region line** — the record is visible, that one line
  stays empty *(recommended)*
- B) Keep dropping it — no work, but promoted records stay invisible

---

## Appendix

- Photo size is currently fixed at one square value in the image generation step.
- The filter that drops records without a region runs in the mapper, before
  results are returned to the interface layer.
- Verified by running the same search twice, once with the filter disabled.

---

## Compare: the same finding written badly

> **Finding 2:** `ResultMapper.to_dto` raises a validation error when the region
> fields are absent, so the record is filtered out upstream of the presenter
> (see line 118).

Everything in that sentence is true, and almost nobody it was written for can act
on it. It names the class instead of the symptom, gives no example, and never says
what a reader should decide.
