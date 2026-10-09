# Daily job search: instructions for the routine

A scheduled cloud agent runs this once a day. Edit this file to change what it looks for.

## Candidate
Weijie Lyu is a final-year EECS Ph.D. at UC Merced (advisor Ming-Hsuan Yang) and will graduate in 2027.
- **Research:** video generation, 3D/4D reconstruction, Gaussian splatting / neural rendering, 3D face and head reconstruction, camera control for video, 3D scene editing and inpainting, world models, agentic auto-research.
- **Papers (first author):** NeurIPS'26, CVPR'26, ECCV'26 Oral, ICCV'25, TMLR'26.
- **Internships:** Apple, ByteDance, Adobe Research.

See `profile.md`.

## What to look for
Accept a posting only if all of these hold:
- **Location:** in the US, or remote within the US.
- **Type:** a full-time role titled Research Scientist, Research Engineer, Applied Scientist, MTS (research), or ML Engineer on generative or 3D vision.
- **Level:** new-grad PhD up to about 3 years of experience.
- **Exclude:** internships, postdocs, and Staff/Principal roles or anything requiring 5+ years. A 5+ year role may be kept only as fit 3 when the topic matches exactly.

## Where to look
Search for postings from roughly the last 7 days, and include older ones you haven't seen before.
- **Job boards to fetch directly:**
  - Ashby: `https://api.ashbyhq.com/posting-api/job-board/<org>`
  - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<org>/jobs`
  - Lever: `https://api.lever.co/v0/postings/<org>`
- **Startups:**
  - Ashby: lumaai, worldlabs, genmo, krea, odysseyml, hedra, pika, applied, captions/mirage, heygen, physicalintelligence, figureai
  - Greenhouse: waymo, kodiak, nuro, stabilityai
  - Lever and others: runway, blackforestlabs, decart, moonvalley, xai, openai, anthropic
- **Big tech** (use web search plus the careers site): Apple (jobs.apple.com), Adobe (Workday), NVIDIA (Workday), TikTok/ByteDance (lifeattiktok.com, jobs.bytedance.com), Google/DeepMind, Meta, Microsoft, Amazon, Snap, Netflix, Roblox, Dolby, Sony AI, Qualcomm, Samsung Research America.
- **Topic searches:**
  - "research scientist video generation"
  - "research scientist 3D reconstruction"
  - "gaussian splatting research scientist"
  - "world model research scientist"
  - "neural rendering research"
  - "avatar research scientist"
  - "2027 start PhD research scientist computer vision"

## Steps
1. Load `seen.json`. It maps id to {company, title, url, first_seen, fit, category}. The id is the first 16 hex characters of sha1 of the normalized URL: strip whitespace, drop the `#fragment`, drop the trailing `/`. To compute it:
   ```
   python3 -c "import hashlib,sys;u=sys.argv[1].strip().split('#')[0].rstrip('/');print(hashlib.sha1(u.encode()).hexdigest()[:16])" URL
   ```
   Also read every doc id in the tracker's `jobs` collection with ArtifactData `list` (limit 1000, follow `next_cursor`). Treat the union of those ids and `seen.json` as already seen, and add any tracker ids missing from `seen.json` to it. The tracker is the source of truth when a previous push failed.
2. Search thoroughly and collect candidate postings. Plan for 10–20 minutes, not 2.
   - Fetch every listed Ashby and Greenhouse board through its API.
   - For big tech, query each careers site's own search for "research scientist" combined with video, 3D, generative and world model.
     - Apple: https://jobs.apple.com/en-us/search?search=research%20scientist%20video
     - NVIDIA and Adobe: Workday search
     - TikTok/ByteDance: lifeattiktok.com or joinbytedance.com search
     - Others: Google careers search
   - Run all the topic searches listed above.
   - If a board's API returns 404, find the company's real careers page with a web search instead of skipping it.
3. Drop a candidate if either is true:
   - its id is already in `seen.json`
   - the same company has the same title, ignoring case and punctuation
4. Verify that each remaining posting is a live, specific posting page. Fetch it, and drop any posting that is closed or not a match. Never invent postings or URLs.
5. For each new posting, build: `{company, title, location, url, category: "Big Tech"|"Startup"|"Other", fit: 1-5, why: "<one line tying it to his research>", posted: "<date or empty>", verified: true, first_seen: "<today, YYYY-MM-DD, America/Los_Angeles>", status: "new", notes: ""}`
6. Add the new postings to `seen.json`.
7. Write `digests/<today>.md`, using `digests/2026-10-08.md` as the format. Put fit 5 and fit 4 first, and give one line per posting with its `why`. If nothing new turned up, still write the file and say "No new postings today".
8. Commit and push to `main`, with the message `digest: <today> (+N)`.
9. Update the tracker artifact (https://claude.ai/artifact/GHtnjGKVAwJ3WHnUMx94Rv) if the `ArtifactData` tool is available. If not, skip this step and say so.
   - For each new posting, do a `set` in collection `jobs` with doc_id = id. Use `batch` with up to 50 writes.
   - Then `set` `meta/run` to `{last_run: <today>, added: N}`. `meta/run` already exists, so read it first and pass `if_version`.
   - Never overwrite an existing `jobs` doc. The user edits status and notes there.
10. Finish with a short summary: how many new postings, the top ones, and whether the tracker was updated.
