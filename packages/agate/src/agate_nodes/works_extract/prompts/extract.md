# Works Extraction Service

Acting as a state-of-the-art entity extraction service, identify and extract all editorially relevant **works** (named human-created artifacts) mentioned in the following text.

Works are distinct from people, organizations, locations, and **events**. They are tangible or intangible artifacts that humans create: laws, reports, books, movies, products, artworks, etc.

## Text to Analyze

{text}

## Overview

Extract a work only if:
1. **A specific work is identifiable** — not a generic category word (e.g. "ordinances" or "laws" in the abstract). The text must refer to a **particular artifact** by proper name, clear identifier, or enough context that the `name` you output is **unambiguous** (see **Disambiguating `name`** below).
2. It directly matters to the story's events, actions, statements, or reporting, such as:
   - Laws, bills, policies, ordinances, court rulings
   - Reports, studies, white papers
   - Books, movies, plays, albums, songs, TV shows, podcasts
   - Drugs, consumer products, technologies, software
   - Artworks, statues, installations, exhibitions
   - Awards, prizes, honors

**IMPORTANT**: Works are artifacts, not people, organizations, locations, or events. "The Affordable Care Act" is a work (law). "The FDA" is an organization. "Dr. Smith" is a person. "The sectional semifinal" is an event, not a work. Extract works separately; they can be linked to people, organizations, and locations later. **Event extraction will be handled by a separate process in the future** — do not treat events as works here.

## Events are not works

**Games, matches, tournaments, rounds, playoffs, hearings, conferences, ceremonies, shows-as-happenings, and similar occurrences are events, not works.** Do not extract them, even if they have a proper-sounding label.

Examples — **do not extract**:
- **"Sectional semifinal"**, **"regional final"**, **"Game 7"** (as the event), **"the hearing"**, **"commencement"** (the ceremony)

**Do extract** when the story refers to an **artifact**: a **rulebook**, **tournament bracket document**, **official agenda**, **published decision**, or **named report** about an event — those are works with distinct types (e.g. report, ruling), not the event itself.

## Organizations and locations are not works (with exceptions)

**When the text refers to an organization or a place as such, that entity is not a work.**

Examples:
- **"Chicago Sun-Times"** or **"the Sun-Times"** meaning the **news organization** → **not** a work (that is an organization).
- **"Navy Pier"** as a **location / landmark** → **not** a work.

**Exception — physical or edition-specific artifacts tied to an org or place:**
- An **individual physical copy** of a newspaper **from a particular date** (e.g. **"Chicago Sun-Times (print edition, March 12, 2024)"** or **"March 12, 2024 Chicago Sun-Times"**) **is** a work when the story treats that **copy or edition** as an artifact.
- A **specific broadcast episode** or **named program** as a creative work can be a **tv_show** / **podcast** when it is a **named installment**, not the network as an organization.

If the referent is ambiguous, prefer **no extraction** unless the text clearly means the **artifact**, not the org or venue.

## Proper names and specificity (dishes excepted)

**Generally, extract only works that have a proper, distinctive name** — a title, brand, bill number, formal report title, statute name, product name, etc.

**Do not extract** vague **category + generic noun** phrases when no **specific** product, drug, law, or title is identified in the story.

Examples — **do not extract**:
- **"Glaucoma medicine"** / **"blood pressure medication"** — generic drug categories unless the text names a **specific** medicine (brand or generic proper name) you can infer **from the story** (e.g. **"Latanoprost"**, **"Drug X (trial name)"** when explicitly named).

**Exception — dishes (`dish` type):** Named or story-specific **menu items** and **dishes** may be extracted even when the name is short or descriptive, as already described for `dish` (include restaurant when helpful).

## Work Types (strict taxonomy)

Use **only** one of these exact type strings. Do not invent variations (e.g. "legal policy", "legal/policy", "legal_policy" — use the specific type below).

| Type | Use for |
|------|---------|
| **law** | Enacted laws, statutes |
| **legislation** | Bills (HB 232, House Bill 892, Senate Bill 444, C.R. 454, etc.) — any proposed or pending legislative measure |
| **policy** | Policies, regulations, guidelines |
| **ordinance** | Local ordinances |
| **ruling** | Court rulings, judicial decisions |
| **report** | Reports |
| **study** | Studies |
| **white_paper** | White papers |
| **book** | Books |
| **movie** | Movies |
| **play** | Plays |
| **album** | Albums |
| **song** | Songs |
| **tv_show** | TV shows |
| **podcast** | Podcasts |
| **drug** | Drugs |
| **consumer_product** | Consumer products |
| **technology** | Technologies |
| **software** | Software |
| **artwork** | Artworks |
| **statue** | Statues |
| **installation** | Installations |
| **exhibition** | Exhibitions |
| **award** | Awards, prizes, honors |
| **dish** | Dishes (food) — include restaurant name when available, e.g. "Carbonara (Joe's Italian)" |
| **other** | Fallback when none of the above fit (e.g. a **lawsuit** as a distinct legal filing when not better typed as **ruling**) |

## Who Should NOT Be Included

- **People** — extract as people, not works
- **Organizations** — companies, agencies, newsrooms, publishers as institutions; see **Organizations and locations are not works** above
- **Locations** — places, venues, addresses as places; see above
- **Events** — games, rounds, hearings, ceremonies, etc.; see **Events are not works** above
- Abstract concepts without a named artifact
- Generic references without a name ("a new law", "the report") when you cannot build a **specific, non-ambiguous `name`** from the article

- **Generic category words** — do not extract when the text refers to a class of things rather than a specific named work. Examples:
  - "more than 20 ordinances" → do not extract "ordinances" (generic plural, no specific ordinance named)
  - "several laws were passed" → do not extract (generic reference)
  - "the report" without enough detail to identify which report → do not extract **unless** you can expand `name` using story context per **Disambiguating `name`**
  - **"Glaucoma medicine"** and similar — not a work unless a **specific** medicine is named or clearly inferable

- **Symbolic or metaphorical references** — do not extract when a work name is used as a metaphor, simile, or comparison rather than referring to the actual artifact. Example: "the design has been derided as a 'Taj Mahal'" → do not extract "Taj Mahal" (metaphor for extravagance, not the monument).

- **Generic components of a larger work** — do not extract generic sub-parts that lack a distinct identity and are redundant with the parent project. Example: "the global terminal" as a component of "the O'Hare expansion project" → extract only the named project, not the generic component. If the component has its own distinct name (e.g., "Terminal 3", "Satellite Concourse A"), it may be extracted.

- **Generically named policies** — do not extract policies that are only named by a generic label without enough context. If the text provides place, year, or subject, **fold that into `name`** (see below).

## Field Requirements

### name

The work as a **specific, identifiable artifact**. Use the full, official name when the article provides it.

**Capitalization:** The **first letter of the first word** in `name` must be **uppercase**, even when the article lowercases it or when the phrase is not otherwise a proper noun. Examples: **"Study on river levels"** not **"study on river levels"**; **"The midnight library"** if that is the article’s wording for a book title. Do **not** force title case on every word unless that matches the **official** title (e.g. keep **"iPhone 15"**, **"eBay"** as the article or official styling shows).

**Disambiguating `name`:** When the article uses a **vague or generic label** for a work ("2023 report", "federal lawsuit", "the study", "new policy"), **do not** use that bare phrase as `name` if it would be ambiguous. **Expand `name` with concise context drawn only from the story** so another reader could tell which work is meant:

- **"2023 report"** → e.g. **"2023 report on San Francisco affordability"** (add subject / author / agency if given)
- **"federal lawsuit"** → e.g. **"Federal lawsuit against X Corp. (2025)"** (parties, year, court district if given)
- **"the city's climate plan"** → include year or formal title if stated

Use parentheses for extra metadata when helpful: **"Production Tax Credit (Missouri, 2026)"**, **"Chicago Climate Action Plan (2008)"**.

If the article does not provide enough detail to produce a **non-vague** `name`, **do not extract** the work.

### type

One of the exact work types from the table above (e.g. legislation, law, policy, report). Use the string exactly as shown — no variations.

### role_in_story

A concise summary of the work's importance in this article.

### mentions

Every instance where the work appears in the text. Each mention should have:
- `text`: The verbatim text (sentence or paragraph) where the work appears

**Do not include a `quote` field** — works do not have quotes. Only `{text}` for each mention.

## Output Format

**IMPORTANT**: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.
