# Organizations Extraction Service

Acting as a state-of-the-art entity extraction service, identify and extract all editorially relevant organizations (institutions, agencies, companies, schools, membership organizations, nonprofits, etc.) mentioned in the following text.

Organizations should generally be entities that are incorporated or otherwise formally established. They typically have a staff and/or a membership.

## Text to Analyze

{text}

## Overview

Extract an organization only if:
1. **Its name is mentioned in the story**
2. It directly matters to the story's events, actions, statements, or reporting, such as:
   - Government agencies, courts, legislative bodies
   - Schools, universities, hospitals, transit agencies
   - Companies, nonprofits, community groups
   - Religious organizations, cultural institutions, sports teams
   - Organizations whose statements, actions, or policies are relevant

**IMPORTANT**: **People are not organizations.** Do not extract elected officials, CEOs, athletes, witnesses, or any **named or unnamed individuals** as organizations — even if they speak for or lead an entity; extract the **office or institution** when appropriate (e.g. **"White House"** / **"the administration"** as `government`), not the person. Conversely, do not treat institutions as people: "DHS said…" — extract **DHS** as an organization. Organizations are entities (agencies, companies, schools, teams), not individuals.

**High school / prep / college sports (critical):** For `type` = **`sports_team`**, the `name` must identify the **specific squad** (sport + gender level when the story supports it), **not** a **bare school name, university name, town name, or mascot-only label** that could mean the institution or a place. **College:** **"Seton Hall"** or **"Duke"** alone is the **school**, not the team — see below. **Pro:** **"Cubs"** or **"Blackhawks"** alone is incomplete when the article **anywhere** gives the city/market — use **"Chicago Cubs"**, **"Chicago Blackhawks"**, etc. **When the article is clearly about one sport, assume all team mentions in that article are that sport** unless the text **explicitly** signals otherwise — see **Primary sport for the entire article** and **Professional sports** below.

## Geographies are not organizations

**Cities, boroughs, counties, states, countries, neighborhoods, and other geographic units are not organizations** when the text refers to the **place, territory, population, or nation as such**. Do not extract "Brooklyn," "Chicago," "Ohio," "Iran," "the United States," or "Latin America" as organizations in those cases.

**Countries specifically:** **"Iran," "France," "Japan," "the United States" (as the country)** are **not** organizations. Do **not** extract them.

**Exception — governments and real subentities:** Extract **named government bodies, military units, agencies, and other incorporated institutions** tied to a country, using their **full official names** — for example **"Islamic Revolutionary Guard Corps"** (articles may say **"Iran Revolutionary Guard Corps"** — same entity; use the full institutional name, not **"Iran"** alone), **"Government of Iran,"** **"U.S. Department of State,"** **"British Parliament."** The **country name alone** is still not an organization.

**Exception — place-named bodies that are real organizations:** When the story refers to an organization that represents or governs a place, extract the **full organizational name**, not the place name alone. Put the complete institution in `name`:

- Prefer **"Brooklyn Borough Council"** or **"Brooklyn Borough President's Office"** — not **"Brooklyn"** — when that body is what the story means.
- Prefer **"Chicago City Council"** — not **"Chicago"** — when the council is the actor.
- Prefer **"Neighborhood Association of [Name]"** when a neighborhood association is meant — not the neighborhood label by itself.

If the text only names the geography with no clear incorporated body, **do not extract** an organization.

## People are not organizations

**Individuals — named or unnamed — must never appear as extracted organizations.** That includes public figures, politicians, athletes, coaches, victims, suspects, experts quoted in the story, and roles described as persons ("the mayor," "a spokesperson") when the referent is a **person**, not a formal body.

- **Do not extract** "Mayor Johnson," "Coach Smith," "the witness," or "a company executive" as organizations.
- If the story attributes an action to a **person**, do not duplicate that as an organization unless a **distinct institution** (e.g. **"Chicago Police Department,"** **"Acme Corp."**) is clearly the actor.

## Venues and landmarks are not organizations

**Physical places** — arenas, stadiums, ballparks, concert halls, convention centers, **named theaters or venues as buildings**, parks, plazas, monuments, bridges, and similar **landmarks or addresses** — are **not** organizations when the story only treats them as **where something happened** (e.g. "the game at Wrigley Field," "a rally outside City Hall steps," "performed at the arena").

**Exception — owner or operator as actor:** Extract an organization only when the text clearly refers to the **legal or operating entity** that **owns, runs, or speaks for** the venue — and use **that organization's name** if given (e.g. a named **sports authority**, **arena management company**, **park district**, or **team ownership group** when it is explicitly the subject). Do **not** treat the **venue's proper name** alone as the organization when the referent is still the **building or site**.

**Museums, performing arts centers, etc.:** If the story means the **cultural institution** as an actor (policies, leadership, acquisitions), `culture_arts` may apply. If the text only uses the name as a **location** ("the gala at the museum"), **do not** extract it as an organization.

## Organization types (strict — use exactly one string per row)

The `type` field must be **exactly** one of the following **24** values. Use **lowercase snake_case** only. Do not use synonyms, Title Case, spaced phrases, or near-duplicates (e.g. never `business`, `business_and_economy`, `Court`, `Education`, `Government & Civic` — map mentally to the list below).

| type | Use for |
|------|---------|
| `government` | National, state, local agencies and executive-branch bodies (including civic agencies, departments, administrations) |
| `law_enforcement` | Police departments, sheriff's offices, federal law enforcement agencies |
| `court` | Courts, judicial bodies |
| `legislative_body` | Legislatures, councils acting as lawmaking bodies when that is the referent |
| `political_party` | Political parties and party committees |
| `school_district` | School districts and similar systems |
| `school` | Individual K–12 schools (when the **school** is the organization, not the sports team — see sports rules) |
| `university` | Colleges and universities (same caveat as schools for sports) |
| `hospital` | Hospitals and health systems acting as institutions |
| `public_health` | Public health agencies and boards |
| `public_services` | Other public-service bodies (e.g. transit agencies, parks departments, DMVs) when they are organizations in the story |
| `utilities` | Power, water, gas, or similar utility providers as organizations |
| `company` | Corporations and general businesses (consolidates vague "business" labels) |
| `local_business` | Single-location or local businesses when distinct from a named parent company |
| `financial_institution` | Banks, credit unions, investment firms as institutions |
| `real_estate` | Real estate firms, developers, brokerages as organizations |
| `nonprofit` | Nonprofits and NGOs |
| `community_group` | Community organizations, civic associations, block clubs |
| `religious_org` | Churches, mosques, temples, religious denominations as organizations |
| `culture_arts` | Museums, orchestras, theaters, arts institutions |
| `sports_team` | Teams — follow **all** sports naming rules below; **never** a bare school, **university**, or city name for a competing squad; **never** mascot-only pro names when the article establishes the city/market |
| `sports_league` | Leagues, conferences, governing bodies for sports |
| `media` | News outlets, publishers, broadcasters as organizations |
| `other` | None of the above fits clearly |

If unsure between two types, pick the **single best** match; use `other` only when necessary.

## Who Should NOT Be Included

- **People** — any person or individual role; see **People are not organizations** above
- Generic references without a name ("the agency said", "a company announced")
- **Pure geographic references** (cities, boroughs, states, **countries as places**, regions) when no distinct organization is meant — see **Geographies are not organizations** above
- Historical organizations unless directly relevant to current events
- Fictional or hypothetical organizations
- Transit **lines** or **routes** as such (e.g. "Metra Southwest Rail Service" as a line) — not organizations; transit **agencies** can be `public_services` or `government` when the agency is the actor
- **Venues and landmarks as physical sites** — arenas, stadiums, named buildings, parks, monuments, etc., when not referring to a distinct owner/operator organization; see **Venues and landmarks are not organizations** above
- **`sports_team` with only a school or place name** — e.g. **"Barrington"**, **"Oswego"**, **"Kenwood"**, **"Stevenson"** as the entire `name` when the story is about a **game, matchup, score, or standings** — **invalid**. You must output the **full team string** (see **High school and college sports teams (mandatory naming)**) or **omit** the extraction if you cannot infer sport (and gender level when applicable) from the article.
- **`sports_team` with only a college/university proper name** in **athletics** coverage — e.g. **"Seton Hall"**, **"Duke"**, **"Northwestern"**, **"Villanova"** as the entire `name` — **invalid** (that names the **institution**, not the squad). Use **"[School as in story] [men's | women's] [sport] team"** when sport and gender level can be determined from the **headline, deck, body, scoreline, conference, or league**; if you truly cannot determine sport (or gender level when it matters), **omit** or keep a **non–sports_team** extraction only if the story is about the **university** as an institution, not the game.
- **`sports_team` with mascot-only pro nickname** when the **full franchise name is recoverable** from the article — e.g. **"Cubs"** / **"Blackhawks"** / **"Bears"** when the text **also** establishes **Chicago** (headline, dateline, first reference, caption, standings label, etc.) — **invalid**; use **"Chicago Cubs"**, **"Chicago Blackhawks"**, **"Chicago Bears"**. If the article **never** establishes city/market, **"Cubs"** alone is acceptable.
- Description of places, such as "Grand Canyon Village"
- Any place that is not described with a proper noun, unless you can infer the proper noun it refers to per the instructions in the section below.

## Other special rules

**Compound organizations**: Sometimes two organizations might be compounded together into one, such as "the Trulaske College of Business at the University of Missouri". In these cases, extract two separate organizations, "Trulaske College of Business" and "University of Missouri."

**Events and tournaments**: Events such as sports tournaments are generally not considered organizations unless the story is referring to the bureaucracies and organizing committees responsible for them. For instance the "College Football Playoff" is not an organization but the "College Football Playoff Committee" is.

**Abbreviations and short-hand references**: If an organization is referred to with an abbreviated name, but you are confident you know its full name, return its full name. This often happens with schools, especially in sports stories, as well as sports teams. For example, "Leo" might refer to "Leo Catholic High School." Return the latter if you are certain.

**Sports teams — use the full team name whenever possible:** For professional and club sports, `name` must be the **complete franchise or club name**, not a nickname alone. Prefer **"Chicago Bulls"** over **"Bulls"**; **"New York Yankees"** over **"Yankees"**; **"Green Bay Packers"** over **"Packers"** when you can infer the franchise from context.

**Professional sports — city/market + nickname (mandatory when inferable):** Scan the **entire supplied text** (especially **headline, deck/subhead, dateline, lead paragraph, captions, and box scores**), not only the sentence with the shortest nickname. When **any** of that material identifies the **city or market** for a pro franchise, output **`[City/market] [nickname]`** in `name` — e.g. **"Chicago Cubs"** not **"Cubs"**; **"Chicago Blackhawks"** not **"Blackhawks"**; **"Chicago Bears"** not **"Bears"**; **"Boston Red Sox"** not **"Red Sox"** when Boston is clear. This applies to **MLB, NHL, NFL, NBA, WNBA, MLS**, and analogous leagues. **If the article never establishes which city's team is meant**, do **not** invent a city — output the **short form as in the text** (or omit if ambiguous vs. a place).

**National / "Team USA" style squads:** Do **not** return a bare **"Team USA"** or country name as the organization. Always include **which sport** (and **men's/women's** when the story makes it clear), e.g. **"United States men's national ice hockey team,"** **"United States women's national soccer team,"** or **"Team USA men's hockey team"** / **"Team USA women's basketball team"** — whichever form matches standard usage and the article context.

**High school and college sports teams (mandatory naming):**

In **high school, prep, or college** sports coverage, each `sports_team` row must name the **competing squad**, not the **school as an institution** and not a **bare geographic or school shorthand** that could be confused with a **place**.

**These are INVALID as `name` when `type` is `sports_team` (do not output them):**
- **"Barrington"**, **"Oswego"**, **"Kenwood"**, **"Hillcrest"**, **"New Trier"**, **"York"** — school or community names **alone**
- **"Stevenson"**, **"Glenbrook North"** — same; readers cannot tell **which sport or which gender’s team**
- **"Seton Hall"**, **"Duke"**, **"Gonzaga"**, **"Marquette"**, **"Northwestern"**, **"Butler"**, **"Villanova"** — **university/school names alone** in **game or athletics** stories (same problem: not **which squad**)
- Any **single-word or undifferentiated school nickname** used like a place name in a game story

**REQUIRED pattern (apply to every prep/HS/college team you extract):**  
`[School name as used in the story] [boys | girls | men's | women's] [sport] team`  
when the article gives **gender level** (or it is clearly implied by league, tournament, or phrasing such as "girls soccer"). Examples:
- **"Barrington boys basketball team"** — not **"Barrington"**
- **"Oswego girls volleyball team"** — not **"Oswego"**
- **"Kenwood boys basketball team"** and **"Hillcrest boys basketball team"** in a basketball rankings piece — not **"Kenwood"** / **"Hillcrest"** alone
- **"Seton Hall men's basketball team"** — not **"Seton Hall"** when the story is about the **basketball** program or a game (infer men's/women's and sport from headline, conference, scoreline, or body)
- **"Butler men's basketball team"** and **"Villanova men's basketball team"** — not **"Butler"** / **"Villanova"** when the article is **dominantly men's basketball** (see **Primary sport for the entire article** below), including **"against Villanova and Butler"** where the sport is not repeated in that sentence
- **"Missouri Tigers football team"** or the **full college athletic brand** when that is standard (e.g. **"University of Missouri football team"**) — not **"Missouri"** alone as a country/place

**Inference source:** You may use **any part** of the supplied text — **title, headline, sections, captions** — to determine sport and gender level; do **not** rely only on the single mention that uses the shortest name.

**Primary sport for the entire article (default):** Infer the article’s **dominant sport** (and for prep/HS/college, the dominant **gender level** when one clearly applies — men’s, women’s, boys, girls) from the **headline, deck, league, scores, coaches, standings, venue,** and recurring vocabulary. **Unless the text explicitly refers to a different sport or level** — e.g. **"the football team,"** **"women's soccer,"** **"baseball squad also won,"** **"on the women's side"** — treat **every** prep/HS/college **`sports_team`** mention in the article as **that same sport and level.** That covers **opponents, schedule, teams named once, nicknames, asides,** and **school names with no sport in the same sentence**; still output **`[School] [men's | women's | boys | girls] [sport] team`**, never a bare school name. Do **not** wait for the sport to appear next to each team. For **professional** teams, a single-sport article (e.g. one league) implies the same: use **full franchise names** per the pro rules. **Exceptions:** truly **multi-sport** pieces with no clear primary frame, or a mention the text **explicitly** ties to another sport; if still ambiguous, prefer **`[School] [sport] team`** over a bare name, or **omit** if you cannot pick a sport at all.

If the story **names the sport** but **not** boys/girls explicitly, infer **boys** vs **girls** from **league names, pronouns, tournament labels,** or **section headers** in the text. If the story truly gives **no** basis to choose, use **`[School] [sport] team`** (still **never** the bare school name alone).

Extract the **school** as `school` / **`university`** **separately** only when the **institution** (administration, board, district policy) is the actor — not when the story is about **who won the game**.

**Professional, national, and geographic sports nicknames:** When a **city, country, region, or nickname** clearly refers to a **sports team** in context, extract that **team** with `type` = `sports_team` — still using the **full team name** rules above (franchise name, not mascot-only; national squad + sport + gender when applicable).

Examples:
- "Chicago" in an NBA game story referring to the franchise → **"Chicago Bulls"** (not "Chicago" or "Bulls" alone).
- Body says **"the Cubs"** or **"Cubs win"** but headline or dateline says **Chicago** / **Chicago's NL team** / **at Wrigley** in a clear Cubs context → **"Chicago Cubs"**, not **"Cubs"** alone.
- **"Blackhawks"** in a hockey recap with **Chicago** established anywhere in the supplied text → **"Chicago Blackhawks"**.
- "The Yankees won" → **"New York Yankees"** when that is the referent (not "Yankees" alone if you are confident).
- Olympic or international play → **"United States men's national ice hockey team"** / **"Team USA men's hockey team"** (not **"United States"** as a country and not bare **"Team USA"**).
- National team shorthand → **"Venezuela men's national baseball team"** when the story is about that squad (not **"Venezuela"** as the country).

Use the most standard, recognizable **full** name you can infer; if the referent is ambiguous between **place** and **team**, prefer **no extraction** unless the sports context is clear.

**Business locations and franchises**: If a story is referring to a particular location of a larger business, such as the Target location on East Lake Street, specify that in the extracted organization. For example "Target, East Lake Street location". If it is referring to the broader company, the organization should be "Target Corporation" or "Walmart Inc." etc.

**Converting to proper nouns**: Organizations should generally be proper nouns. If an organization is referred to with an improper noun, such as "the inspector general's office wrote a report," or "the man was charged in district court," and you can infer the proper noun it refers to based on the context — such as "City of Minneapolis Inspector General's Office," or "the Northern District of Illinois" — return the proper noun. Or else do not return anything.

**Contextual inference from story scope**: When the story is clearly about a particular jurisdiction (state, city, county, etc.) and uses generic or shorthand references to government bodies, courts, or agencies, infer the full qualified name from the story's context. Do not extract the generic term alone when the context makes the specific entity clear. Examples:
- In a story about the Missouri House of Representatives, "the Senate" refers to the Missouri State Senate — extract "Missouri State Senate," not "the Senate."
- In a story about Chicago city government, "the council" or "the city council" likely refers to the Chicago City Council.
- In a story about a county, "the court" or "district court" may refer to that county's circuit or district court.
- When the story establishes a jurisdictional frame (e.g., state legislature, city hall, county board), use that frame to disambiguate generic terms like "the House," "the Senate," "the committee," "the board," or "the agency."
- Return the full, disambiguated name when the inference is clear from context. If the reference is genuinely ambiguous, do not infer.

Every organization mention should be subject to these rules, with no exceptions.

## Field Requirements

### name

The organization name as given in the article, **except** for sports teams: use the **most complete standard name supported anywhere in the supplied text** (headline, deck, body, captions), including the article’s **dominant sport** under **Primary sport for the entire article** — e.g. **"Chicago Cubs"** if Chicago is established, **"Butler men's basketball team"** when the piece is overwhelmingly men’s hoops. If the text **never** gives enough context to expand a short form, **keep the short form**; do **not** guess cities or sports that are not supported by the article. Follow all rules above for **full pro franchise names**, **prep/HS/college team strings** (**never** bare school/university names like **"Seton Hall"** or **"Barrington"** for `sports_team` in athletics stories), **country + sport (+ gender)** for national teams, and **full names for government bodies** (never the country alone). **Never use a person's name** as `name` — people are extracted elsewhere, not as organizations.

### type

**Exactly one** of the 24 allowed values in the table above — character-for-character match (snake_case, lowercase).

### role_in_story

A concise summary of the organization's importance in this article.

### mentions

Every instance where the organization appears in the text. Each mention should have:
- `text`: The verbatim text (sentence or paragraph) where the organization appears

**Do not include a `quote` field** — organizations do not have quotes. Only `{text}` for each mention.

## Output Format

**IMPORTANT**: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.
