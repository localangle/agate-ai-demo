// Auto-injected metadata for OrganizationsExtract
const nodeMetadata = {
  "type": "OrganizationsExtract",
  "name": "OrganizationsExtract",
  "label": "Organizations Extract",
  "description": "Extract organizations (institutions, agencies, companies) from text using LLM.",
  "category": "organization",
  "icon": "Building2",
  "color": "bg-amber-500",
  "requiredUpstreamNodes": [],
  "dependencyHelperText": "Requires text input or JSON with a \"text\" attribute.",
  "inputs": [
    {
      "id": "text",
      "label": "Text",
      "type": "string",
      "required": true
    }
  ],
  "outputs": [
    {
      "id": "organizations",
      "label": "Organizations",
      "type": "array"
    }
  ],
  "defaultParams": {
    "model": "gpt-5.4-mini",
    "prompt_file": "prompts/extract.md",
    "prompt": "# Organizations Extraction Service\n\nActing as a state-of-the-art entity extraction service, identify and extract all editorially relevant organizations (institutions, agencies, companies, schools, membership organizations, nonprofits, etc.) mentioned in the following text.\n\nOrganizations should generally be entities that are incorporated or otherwise formally established. They typically have a staff and/or a membership.\n\n## Text to Analyze\n\n{text}\n\n## Overview\n\nExtract an organization only if:\n1. **Its name is mentioned in the story**\n2. It directly matters to the story's events, actions, statements, or reporting, such as:\n   - Government agencies, courts, legislative bodies\n   - Schools, universities, hospitals, transit agencies\n   - Companies, nonprofits, community groups\n   - Religious organizations, cultural institutions, sports teams\n   - Organizations whose statements, actions, or policies are relevant\n\n**IMPORTANT**: **People are not organizations.** Do not extract elected officials, CEOs, athletes, witnesses, or any **named or unnamed individuals** as organizations — even if they speak for or lead an entity; extract the **office or institution** when appropriate (e.g. **\"White House\"** / **\"the administration\"** as `government`), not the person. Conversely, do not treat institutions as people: \"DHS said…\" — extract **DHS** as an organization. Organizations are entities (agencies, companies, schools, teams), not individuals.\n\n**High school / prep / college sports (critical):** For `type` = **`sports_team`**, the `name` must identify the **specific squad** (sport + gender level when the story supports it), **not** a **bare school name, university name, town name, or mascot-only label** that could mean the institution or a place. **College:** **\"Seton Hall\"** or **\"Duke\"** alone is the **school**, not the team — see below. **Pro:** **\"Cubs\"** or **\"Blackhawks\"** alone is incomplete when the article **anywhere** gives the city/market — use **\"Chicago Cubs\"**, **\"Chicago Blackhawks\"**, etc. **When the article is clearly about one sport, assume all team mentions in that article are that sport** unless the text **explicitly** signals otherwise — see **Primary sport for the entire article** and **Professional sports** below.\n\n## Geographies are not organizations\n\n**Cities, boroughs, counties, states, countries, neighborhoods, and other geographic units are not organizations** when the text refers to the **place, territory, population, or nation as such**. Do not extract \"Brooklyn,\" \"Chicago,\" \"Ohio,\" \"Iran,\" \"the United States,\" or \"Latin America\" as organizations in those cases.\n\n**Countries specifically:** **\"Iran,\" \"France,\" \"Japan,\" \"the United States\" (as the country)** are **not** organizations. Do **not** extract them.\n\n**Exception — governments and real subentities:** Extract **named government bodies, military units, agencies, and other incorporated institutions** tied to a country, using their **full official names** — for example **\"Islamic Revolutionary Guard Corps\"** (articles may say **\"Iran Revolutionary Guard Corps\"** — same entity; use the full institutional name, not **\"Iran\"** alone), **\"Government of Iran,\"** **\"U.S. Department of State,\"** **\"British Parliament.\"** The **country name alone** is still not an organization.\n\n**Exception — place-named bodies that are real organizations:** When the story refers to an organization that represents or governs a place, extract the **full organizational name**, not the place name alone. Put the complete institution in `name`:\n\n- Prefer **\"Brooklyn Borough Council\"** or **\"Brooklyn Borough President's Office\"** — not **\"Brooklyn\"** — when that body is what the story means.\n- Prefer **\"Chicago City Council\"** — not **\"Chicago\"** — when the council is the actor.\n- Prefer **\"Neighborhood Association of [Name]\"** when a neighborhood association is meant — not the neighborhood label by itself.\n\nIf the text only names the geography with no clear incorporated body, **do not extract** an organization.\n\n## People are not organizations\n\n**Individuals — named or unnamed — must never appear as extracted organizations.** That includes public figures, politicians, athletes, coaches, victims, suspects, experts quoted in the story, and roles described as persons (\"the mayor,\" \"a spokesperson\") when the referent is a **person**, not a formal body.\n\n- **Do not extract** \"Mayor Johnson,\" \"Coach Smith,\" \"the witness,\" or \"a company executive\" as organizations.\n- If the story attributes an action to a **person**, do not duplicate that as an organization unless a **distinct institution** (e.g. **\"Chicago Police Department,\"** **\"Acme Corp.\"**) is clearly the actor.\n\n## Venues and landmarks are not organizations\n\n**Physical places** — arenas, stadiums, ballparks, concert halls, convention centers, **named theaters or venues as buildings**, parks, plazas, monuments, bridges, and similar **landmarks or addresses** — are **not** organizations when the story only treats them as **where something happened** (e.g. \"the game at Wrigley Field,\" \"a rally outside City Hall steps,\" \"performed at the arena\").\n\n**Exception — owner or operator as actor:** Extract an organization only when the text clearly refers to the **legal or operating entity** that **owns, runs, or speaks for** the venue — and use **that organization's name** if given (e.g. a named **sports authority**, **arena management company**, **park district**, or **team ownership group** when it is explicitly the subject). Do **not** treat the **venue's proper name** alone as the organization when the referent is still the **building or site**.\n\n**Museums, performing arts centers, etc.:** If the story means the **cultural institution** as an actor (policies, leadership, acquisitions), `culture_arts` may apply. If the text only uses the name as a **location** (\"the gala at the museum\"), **do not** extract it as an organization.\n\n## Organization types (strict — use exactly one string per row)\n\nThe `type` field must be **exactly** one of the following **24** values. Use **lowercase snake_case** only. Do not use synonyms, Title Case, spaced phrases, or near-duplicates (e.g. never `business`, `business_and_economy`, `Court`, `Education`, `Government & Civic` — map mentally to the list below).\n\n| type | Use for |\n|------|---------|\n| `government` | National, state, local agencies and executive-branch bodies (including civic agencies, departments, administrations) |\n| `law_enforcement` | Police departments, sheriff's offices, federal law enforcement agencies |\n| `court` | Courts, judicial bodies |\n| `legislative_body` | Legislatures, councils acting as lawmaking bodies when that is the referent |\n| `political_party` | Political parties and party committees |\n| `school_district` | School districts and similar systems |\n| `school` | Individual K–12 schools (when the **school** is the organization, not the sports team — see sports rules) |\n| `university` | Colleges and universities (same caveat as schools for sports) |\n| `hospital` | Hospitals and health systems acting as institutions |\n| `public_health` | Public health agencies and boards |\n| `public_services` | Other public-service bodies (e.g. transit agencies, parks departments, DMVs) when they are organizations in the story |\n| `utilities` | Power, water, gas, or similar utility providers as organizations |\n| `company` | Corporations and general businesses (consolidates vague \"business\" labels) |\n| `local_business` | Single-location or local businesses when distinct from a named parent company |\n| `financial_institution` | Banks, credit unions, investment firms as institutions |\n| `real_estate` | Real estate firms, developers, brokerages as organizations |\n| `nonprofit` | Nonprofits and NGOs |\n| `community_group` | Community organizations, civic associations, block clubs |\n| `religious_org` | Churches, mosques, temples, religious denominations as organizations |\n| `culture_arts` | Museums, orchestras, theaters, arts institutions |\n| `sports_team` | Teams — follow **all** sports naming rules below; **never** a bare school, **university**, or city name for a competing squad; **never** mascot-only pro names when the article establishes the city/market |\n| `sports_league` | Leagues, conferences, governing bodies for sports |\n| `media` | News outlets, publishers, broadcasters as organizations |\n| `other` | None of the above fits clearly |\n\nIf unsure between two types, pick the **single best** match; use `other` only when necessary.\n\n## Who Should NOT Be Included\n\n- **People** — any person or individual role; see **People are not organizations** above\n- Generic references without a name (\"the agency said\", \"a company announced\")\n- **Pure geographic references** (cities, boroughs, states, **countries as places**, regions) when no distinct organization is meant — see **Geographies are not organizations** above\n- Historical organizations unless directly relevant to current events\n- Fictional or hypothetical organizations\n- Transit **lines** or **routes** as such (e.g. \"Metra Southwest Rail Service\" as a line) — not organizations; transit **agencies** can be `public_services` or `government` when the agency is the actor\n- **Venues and landmarks as physical sites** — arenas, stadiums, named buildings, parks, monuments, etc., when not referring to a distinct owner/operator organization; see **Venues and landmarks are not organizations** above\n- **`sports_team` with only a school or place name** — e.g. **\"Barrington\"**, **\"Oswego\"**, **\"Kenwood\"**, **\"Stevenson\"** as the entire `name` when the story is about a **game, matchup, score, or standings** — **invalid**. You must output the **full team string** (see **High school and college sports teams (mandatory naming)**) or **omit** the extraction if you cannot infer sport (and gender level when applicable) from the article.\n- **`sports_team` with only a college/university proper name** in **athletics** coverage — e.g. **\"Seton Hall\"**, **\"Duke\"**, **\"Northwestern\"**, **\"Villanova\"** as the entire `name` — **invalid** (that names the **institution**, not the squad). Use **\"[School as in story] [men's | women's] [sport] team\"** when sport and gender level can be determined from the **headline, deck, body, scoreline, conference, or league**; if you truly cannot determine sport (or gender level when it matters), **omit** or keep a **non–sports_team** extraction only if the story is about the **university** as an institution, not the game.\n- **`sports_team` with mascot-only pro nickname** when the **full franchise name is recoverable** from the article — e.g. **\"Cubs\"** / **\"Blackhawks\"** / **\"Bears\"** when the text **also** establishes **Chicago** (headline, dateline, first reference, caption, standings label, etc.) — **invalid**; use **\"Chicago Cubs\"**, **\"Chicago Blackhawks\"**, **\"Chicago Bears\"**. If the article **never** establishes city/market, **\"Cubs\"** alone is acceptable.\n- Description of places, such as \"Grand Canyon Village\"\n- Any place that is not described with a proper noun, unless you can infer the proper noun it refers to per the instructions in the section below.\n\n## Other special rules\n\n**Compound organizations**: Sometimes two organizations might be compounded together into one, such as \"the Trulaske College of Business at the University of Missouri\". In these cases, extract two separate organizations, \"Trulaske College of Business\" and \"University of Missouri.\"\n\n**Events and tournaments**: Events such as sports tournaments are generally not considered organizations unless the story is referring to the bureaucracies and organizing committees responsible for them. For instance the \"College Football Playoff\" is not an organization but the \"College Football Playoff Committee\" is.\n\n**Abbreviations and short-hand references**: If an organization is referred to with an abbreviated name, but you are confident you know its full name, return its full name. This often happens with schools, especially in sports stories, as well as sports teams. For example, \"Leo\" might refer to \"Leo Catholic High School.\" Return the latter if you are certain.\n\n**Sports teams — use the full team name whenever possible:** For professional and club sports, `name` must be the **complete franchise or club name**, not a nickname alone. Prefer **\"Chicago Bulls\"** over **\"Bulls\"**; **\"New York Yankees\"** over **\"Yankees\"**; **\"Green Bay Packers\"** over **\"Packers\"** when you can infer the franchise from context.\n\n**Professional sports — city/market + nickname (mandatory when inferable):** Scan the **entire supplied text** (especially **headline, deck/subhead, dateline, lead paragraph, captions, and box scores**), not only the sentence with the shortest nickname. When **any** of that material identifies the **city or market** for a pro franchise, output **`[City/market] [nickname]`** in `name` — e.g. **\"Chicago Cubs\"** not **\"Cubs\"**; **\"Chicago Blackhawks\"** not **\"Blackhawks\"**; **\"Chicago Bears\"** not **\"Bears\"**; **\"Boston Red Sox\"** not **\"Red Sox\"** when Boston is clear. This applies to **MLB, NHL, NFL, NBA, WNBA, MLS**, and analogous leagues. **If the article never establishes which city's team is meant**, do **not** invent a city — output the **short form as in the text** (or omit if ambiguous vs. a place).\n\n**National / \"Team USA\" style squads:** Do **not** return a bare **\"Team USA\"** or country name as the organization. Always include **which sport** (and **men's/women's** when the story makes it clear), e.g. **\"United States men's national ice hockey team,\"** **\"United States women's national soccer team,\"** or **\"Team USA men's hockey team\"** / **\"Team USA women's basketball team\"** — whichever form matches standard usage and the article context.\n\n**High school and college sports teams (mandatory naming):**\n\nIn **high school, prep, or college** sports coverage, each `sports_team` row must name the **competing squad**, not the **school as an institution** and not a **bare geographic or school shorthand** that could be confused with a **place**.\n\n**These are INVALID as `name` when `type` is `sports_team` (do not output them):**\n- **\"Barrington\"**, **\"Oswego\"**, **\"Kenwood\"**, **\"Hillcrest\"**, **\"New Trier\"**, **\"York\"** — school or community names **alone**\n- **\"Stevenson\"**, **\"Glenbrook North\"** — same; readers cannot tell **which sport or which gender’s team**\n- **\"Seton Hall\"**, **\"Duke\"**, **\"Gonzaga\"**, **\"Marquette\"**, **\"Northwestern\"**, **\"Butler\"**, **\"Villanova\"** — **university/school names alone** in **game or athletics** stories (same problem: not **which squad**)\n- Any **single-word or undifferentiated school nickname** used like a place name in a game story\n\n**REQUIRED pattern (apply to every prep/HS/college team you extract):**  \n`[School name as used in the story] [boys | girls | men's | women's] [sport] team`  \nwhen the article gives **gender level** (or it is clearly implied by league, tournament, or phrasing such as \"girls soccer\"). Examples:\n- **\"Barrington boys basketball team\"** — not **\"Barrington\"**\n- **\"Oswego girls volleyball team\"** — not **\"Oswego\"**\n- **\"Kenwood boys basketball team\"** and **\"Hillcrest boys basketball team\"** in a basketball rankings piece — not **\"Kenwood\"** / **\"Hillcrest\"** alone\n- **\"Seton Hall men's basketball team\"** — not **\"Seton Hall\"** when the story is about the **basketball** program or a game (infer men's/women's and sport from headline, conference, scoreline, or body)\n- **\"Butler men's basketball team\"** and **\"Villanova men's basketball team\"** — not **\"Butler\"** / **\"Villanova\"** when the article is **dominantly men's basketball** (see **Primary sport for the entire article** below), including **\"against Villanova and Butler\"** where the sport is not repeated in that sentence\n- **\"Missouri Tigers football team\"** or the **full college athletic brand** when that is standard (e.g. **\"University of Missouri football team\"**) — not **\"Missouri\"** alone as a country/place\n\n**Inference source:** You may use **any part** of the supplied text — **title, headline, sections, captions** — to determine sport and gender level; do **not** rely only on the single mention that uses the shortest name.\n\n**Primary sport for the entire article (default):** Infer the article’s **dominant sport** (and for prep/HS/college, the dominant **gender level** when one clearly applies — men’s, women’s, boys, girls) from the **headline, deck, league, scores, coaches, standings, venue,** and recurring vocabulary. **Unless the text explicitly refers to a different sport or level** — e.g. **\"the football team,\"** **\"women's soccer,\"** **\"baseball squad also won,\"** **\"on the women's side\"** — treat **every** prep/HS/college **`sports_team`** mention in the article as **that same sport and level.** That covers **opponents, schedule, teams named once, nicknames, asides,** and **school names with no sport in the same sentence**; still output **`[School] [men's | women's | boys | girls] [sport] team`**, never a bare school name. Do **not** wait for the sport to appear next to each team. For **professional** teams, a single-sport article (e.g. one league) implies the same: use **full franchise names** per the pro rules. **Exceptions:** truly **multi-sport** pieces with no clear primary frame, or a mention the text **explicitly** ties to another sport; if still ambiguous, prefer **`[School] [sport] team`** over a bare name, or **omit** if you cannot pick a sport at all.\n\nIf the story **names the sport** but **not** boys/girls explicitly, infer **boys** vs **girls** from **league names, pronouns, tournament labels,** or **section headers** in the text. If the story truly gives **no** basis to choose, use **`[School] [sport] team`** (still **never** the bare school name alone).\n\nExtract the **school** as `school` / **`university`** **separately** only when the **institution** (administration, board, district policy) is the actor — not when the story is about **who won the game**.\n\n**Professional, national, and geographic sports nicknames:** When a **city, country, region, or nickname** clearly refers to a **sports team** in context, extract that **team** with `type` = `sports_team` — still using the **full team name** rules above (franchise name, not mascot-only; national squad + sport + gender when applicable).\n\nExamples:\n- \"Chicago\" in an NBA game story referring to the franchise → **\"Chicago Bulls\"** (not \"Chicago\" or \"Bulls\" alone).\n- Body says **\"the Cubs\"** or **\"Cubs win\"** but headline or dateline says **Chicago** / **Chicago's NL team** / **at Wrigley** in a clear Cubs context → **\"Chicago Cubs\"**, not **\"Cubs\"** alone.\n- **\"Blackhawks\"** in a hockey recap with **Chicago** established anywhere in the supplied text → **\"Chicago Blackhawks\"**.\n- \"The Yankees won\" → **\"New York Yankees\"** when that is the referent (not \"Yankees\" alone if you are confident).\n- Olympic or international play → **\"United States men's national ice hockey team\"** / **\"Team USA men's hockey team\"** (not **\"United States\"** as a country and not bare **\"Team USA\"**).\n- National team shorthand → **\"Venezuela men's national baseball team\"** when the story is about that squad (not **\"Venezuela\"** as the country).\n\nUse the most standard, recognizable **full** name you can infer; if the referent is ambiguous between **place** and **team**, prefer **no extraction** unless the sports context is clear.\n\n**Business locations and franchises**: If a story is referring to a particular location of a larger business, such as the Target location on East Lake Street, specify that in the extracted organization. For example \"Target, East Lake Street location\". If it is referring to the broader company, the organization should be \"Target Corporation\" or \"Walmart Inc.\" etc.\n\n**Converting to proper nouns**: Organizations should generally be proper nouns. If an organization is referred to with an improper noun, such as \"the inspector general's office wrote a report,\" or \"the man was charged in district court,\" and you can infer the proper noun it refers to based on the context — such as \"City of Minneapolis Inspector General's Office,\" or \"the Northern District of Illinois\" — return the proper noun. Or else do not return anything.\n\n**Contextual inference from story scope**: When the story is clearly about a particular jurisdiction (state, city, county, etc.) and uses generic or shorthand references to government bodies, courts, or agencies, infer the full qualified name from the story's context. Do not extract the generic term alone when the context makes the specific entity clear. Examples:\n- In a story about the Missouri House of Representatives, \"the Senate\" refers to the Missouri State Senate — extract \"Missouri State Senate,\" not \"the Senate.\"\n- In a story about Chicago city government, \"the council\" or \"the city council\" likely refers to the Chicago City Council.\n- In a story about a county, \"the court\" or \"district court\" may refer to that county's circuit or district court.\n- When the story establishes a jurisdictional frame (e.g., state legislature, city hall, county board), use that frame to disambiguate generic terms like \"the House,\" \"the Senate,\" \"the committee,\" \"the board,\" or \"the agency.\"\n- Return the full, disambiguated name when the inference is clear from context. If the reference is genuinely ambiguous, do not infer.\n\nEvery organization mention should be subject to these rules, with no exceptions.\n\n## Field Requirements\n\n### name\n\nThe organization name as given in the article, **except** for sports teams: use the **most complete standard name supported anywhere in the supplied text** (headline, deck, body, captions), including the article’s **dominant sport** under **Primary sport for the entire article** — e.g. **\"Chicago Cubs\"** if Chicago is established, **\"Butler men's basketball team\"** when the piece is overwhelmingly men’s hoops. If the text **never** gives enough context to expand a short form, **keep the short form**; do **not** guess cities or sports that are not supported by the article. Follow all rules above for **full pro franchise names**, **prep/HS/college team strings** (**never** bare school/university names like **\"Seton Hall\"** or **\"Barrington\"** for `sports_team` in athletics stories), **country + sport (+ gender)** for national teams, and **full names for government bodies** (never the country alone). **Never use a person's name** as `name` — people are extracted elsewhere, not as organizations.\n\n### type\n\n**Exactly one** of the 24 allowed values in the table above — character-for-character match (snake_case, lowercase).\n\n### role_in_story\n\nA concise summary of the organization's importance in this article.\n\n### mentions\n\nEvery instance where the organization appears in the text. Each mention should have:\n- `text`: The verbatim text (sentence or paragraph) where the organization appears\n\n**Do not include a `quote` field** — organizations do not have quotes. Only `{text}` for each mention.\n\n## Output Format\n\n**IMPORTANT**: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.\n",
    "json_format": "{\n  \"organizations\": [\n    {\n      \"name\": \"Chicago Public Schools\",\n      \"type\": \"school_district\",\n      \"role_in_story\": \"Announced new policy\",\n      \"mentions\": [\n        {\n          \"text\": \"Chicago Public Schools announced a new policy on Monday.\"\n        }\n      ]\n    },\n    {\n      \"name\": \"Chicago City Council\",\n      \"type\": \"legislative_body\",\n      \"role_in_story\": \"Voted on ordinance\",\n      \"mentions\": [\n        {\n          \"text\": \"The city council approved the measure.\"\n        }\n      ]\n    },\n    {\n      \"name\": \"Chicago Bulls\",\n      \"type\": \"sports_team\",\n      \"role_in_story\": \"Won the game\",\n      \"mentions\": [\n        {\n          \"text\": \"Chicago rallied in the fourth quarter.\"\n        }\n      ]\n    }\n  ]\n}"
  },
  "availableModels": [
    {
      "value": "gpt-5.4-mini",
      "label": "GPT-5.4 Mini"
    },
    {
      "value": "gpt-5.4",
      "label": "GPT-5.4"
    },
    {
      "value": "gpt-5.4-nano",
      "label": "GPT-5.4 Nano"
    }
  ]
};

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { VisualizationProps, VisualizationDescriptor } from '@/lib/visualizations'

export function buildVisualization(
  nodeId: string,
  nodeLabel: string,
  output: any
): VisualizationDescriptor | null {
  if (!output || typeof output !== 'object') {
    return null
  }
  const organizations = output.organizations
  if (!Array.isArray(organizations) || organizations.length === 0) {
    return null
  }

  const OrganizationsExtractVisualization: React.FC<VisualizationProps> = ({
    nodeId,
    nodeLabel,
    output,
  }) => {
    const [expandedMentions, setExpandedMentions] = useState<Set<number>>(new Set())

    const toggleMentions = (index: number) => {
      const newExpanded = new Set(expandedMentions)
      if (newExpanded.has(index)) {
        newExpanded.delete(index)
      } else {
        newExpanded.add(index)
      }
      setExpandedMentions(newExpanded)
    }

    const orgs = output?.organizations || []

    return (
      <Card>
        <CardHeader>
          <CardTitle>Organizations Extract</CardTitle>
          {nodeLabel !== nodeId && <CardDescription>{nodeLabel}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Name</TableHead>
                  <TableHead className="w-[120px]">Type</TableHead>
                  <TableHead>Role in Story</TableHead>
                  <TableHead className="w-[100px]">Mentions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orgs.map((org: any, index: number) => {
                  const mentions = org.mentions || []
                  const isExpanded = expandedMentions.has(index)
                  return (
                    <React.Fragment key={index}>
                      <TableRow>
                        <TableCell className="font-medium">{org.name || '-'}</TableCell>
                        <TableCell>{org.type || '-'}</TableCell>
                        <TableCell>{org.role_in_story || '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span>{mentions.length}</span>
                            {mentions.length > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => toggleMentions(index)}
                              >
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                      {isExpanded &&
                        mentions.map((m: any, mi: number) => (
                          <TableRow key={`${index}-${mi}`} className="bg-muted/50">
                            <TableCell colSpan={4} className="text-xs py-2">
                              {m.text || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                    </React.Fragment>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    )
  }

  return {
    id: `${nodeId}-organizations`,
    title: 'Organizations Extract',
    nodeId,
    nodeLabel,
    component: OrganizationsExtractVisualization,
  }
}
