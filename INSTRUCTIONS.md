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
`scan.py` covers the boards and careers sites that have a usable API: Ashby, Greenhouse, NVIDIA/Adobe Workday, Apple, Google and TikTok. To add a company, edit the lists at the top of that file.

These sources have no API and have to be searched on the web:
- ByteDance Seed (joinbytedance.com)
- Meta (metacareers.com)
- Microsoft
- Amazon
- Snap
- Netflix and Eyeline
- Roblox
- Dolby
- Sony AI
- Qualcomm
- Samsung Research America
- Black Forest Labs
- Decart
- Moonvalley
- Higgsfield

The topic searches:
- "research scientist video generation"
- "research scientist 3D reconstruction"
- "gaussian splatting research scientist"
- "world model research scientist"
- "neural rendering research"
- "avatar research scientist"
- "2027 start PhD research scientist computer vision"

## Steps
These steps are required. Do every one, every run. A run that skips the scanner or the web checklist counts as a failed run.

1. **Gather the already-seen ids.**
   - `seen.json` maps id to {company, title, url, first_seen, fit, category}.
   - `rejected.json` maps id to "title | reason". It holds postings that were reviewed and turned down earlier.
   - The id is the first 16 hex characters of sha1 of the normalized URL: strip whitespace, drop the `#fragment`, drop the trailing `/`. To compute it:
     ```
     python3 -c "import hashlib,sys;u=sys.argv[1].strip().split('#')[0].rstrip('/');print(hashlib.sha1(u.encode()).hexdigest()[:16])" URL
     ```
   - Read every doc id in the tracker's `jobs` collection with ArtifactData `list` (limit 1000, follow `next_cursor`). Write them one per line to `/tmp/tracker_ids.txt`, and add any that are missing to `seen.json`. The tracker is the source of truth when a previous push failed.
   - Read the tracker doc `meta/rejected` (`get`). Its field `ids` maps id to "title | reason". Merge it into `rejected.json`. If the doc doesn't exist yet, start from the file alone.
2. **Run the scanner:** `python3 -I scan.py /tmp/tracker_ids.txt`
   - Keep its coverage table; it goes into the digest.
   - If a source shows ERROR, retry it once. If it still fails, search that company on the web instead.
3. **Triage `candidates.json`.**
   - Review every entry. Decide from the title first. For anything plausible, fetch the posting and read the requirements.
   - Keep postings that pass "What to look for". Put every other candidate into `rejected.json` with a short reason (off-topic, too senior, non-US, internship, closed), so it isn't reviewed again tomorrow.
4. **Search the web.** Work through every source in the no-API list and every topic search.
   - Prefer the company's own careers page. Use aggregators only to find a posting, then follow it back to the official page.
   - Drop anything already seen. Also drop it if the same company has a posting with the same title, ignoring case and punctuation.
5. **Verify and build records.**
   - Every kept posting must be a live, specific posting page you actually fetched. Never invent postings or URLs.
   - For each one, build: `{company, title, location, url, category: "Big Tech"|"Startup"|"Other", fit: 1-5, why: "<one line tying it to his research>", posted: "<date or empty>", verified: true, first_seen: "<today, YYYY-MM-DD, America/Los_Angeles>", status: "new", notes: ""}`
6. Add the new postings to `seen.json`, and save `rejected.json`. Also write the full merged rejected map to the tracker doc `meta/rejected` as `{ids: {...}}`. Use `set`, with `if_version` when the doc already exists. This keeps the rejected list across runs even when the push to GitHub fails.
7. Write `digests/<today>.md`, using `digests/2026-10-08.md` as the format. Put fit 5 and fit 4 first, and give one line per posting with its `why`. If nothing new turned up, still write the file and say "No new postings today". End the digest with a **Coverage** section. It contains the scanner's table, then the no-API sources and topic searches, each marked done or failed with a reason, then the number of candidates rejected.
8. Commit and push to `main`, with the message `digest: <today> (+N)`.
9. Update the tracker artifact (https://claude.ai/artifact/GHtnjGKVAwJ3WHnUMx94Rv) if the `ArtifactData` tool is available. If not, skip this step and say so.
   - For each new posting, do a `set` in collection `jobs` with doc_id = id. Use `batch` with up to 50 writes.
   - Then `set` `meta/run` to `{last_run: <today>, added: N}`. `meta/run` already exists, so read it first and pass `if_version`.
   - Never overwrite an existing `jobs` doc. The user edits status and notes there.
10. Finish with a short summary: how many new postings, the top ones, whether the tracker was updated, and any coverage gaps.
11. Send a phone notification with the PushNotification tool. If it isn't listed, load it with ToolSearch `select:PushNotification`. Keep it to one or two lines, such as "N new RS postings today. Top: <Company – Title>, … Tracker: https://claude.ai/artifact/GHtnjGKVAwJ3WHnUMx94Rv". When nothing new turned up, send "No new postings today".
