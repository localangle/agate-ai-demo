// Auto-injected metadata for WorksExtract
const nodeMetadata = {
  "type": "WorksExtract",
  "name": "WorksExtract",
  "label": "Works Extract",
  "description": "Extract works (laws, reports, books, products, artworks) from text using LLM.",
  "category": "work",
  "icon": "BookOpen",
  "color": "bg-teal-500",
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
      "id": "works",
      "label": "Works",
      "type": "array"
    }
  ],
  "defaultParams": {
    "model": "gpt-5.4-mini",
    "prompt_file": "prompts/extract.md",
    "prompt": "# Works Extraction Service\n\nActing as a state-of-the-art entity extraction service, identify and extract all editorially relevant **works** (named human-created artifacts) mentioned in the following text.\n\nWorks are distinct from people, organizations, locations, and **events**. They are tangible or intangible artifacts that humans create: laws, reports, books, movies, products, artworks, etc.\n\n## Text to Analyze\n\n{text}\n\n## Overview\n\nExtract a work only if:\n1. **A specific work is identifiable** — not a generic category word (e.g. \"ordinances\" or \"laws\" in the abstract). The text must refer to a **particular artifact** by proper name, clear identifier, or enough context that the `name` you output is **unambiguous** (see **Disambiguating `name`** below).\n2. It directly matters to the story's events, actions, statements, or reporting, such as:\n   - Laws, bills, policies, ordinances, court rulings\n   - Reports, studies, white papers\n   - Books, movies, plays, albums, songs, TV shows, podcasts\n   - Drugs, consumer products, technologies, software\n   - Artworks, statues, installations, exhibitions\n   - Awards, prizes, honors\n\n**IMPORTANT**: Works are artifacts, not people, organizations, locations, or events. \"The Affordable Care Act\" is a work (law). \"The FDA\" is an organization. \"Dr. Smith\" is a person. \"The sectional semifinal\" is an event, not a work. Extract works separately; they can be linked to people, organizations, and locations later. **Event extraction will be handled by a separate process in the future** — do not treat events as works here.\n\n## Events are not works\n\n**Games, matches, tournaments, rounds, playoffs, hearings, conferences, ceremonies, shows-as-happenings, and similar occurrences are events, not works.** Do not extract them, even if they have a proper-sounding label.\n\nExamples — **do not extract**:\n- **\"Sectional semifinal\"**, **\"regional final\"**, **\"Game 7\"** (as the event), **\"the hearing\"**, **\"commencement\"** (the ceremony)\n\n**Do extract** when the story refers to an **artifact**: a **rulebook**, **tournament bracket document**, **official agenda**, **published decision**, or **named report** about an event — those are works with distinct types (e.g. report, ruling), not the event itself.\n\n## Organizations and locations are not works (with exceptions)\n\n**When the text refers to an organization or a place as such, that entity is not a work.**\n\nExamples:\n- **\"Chicago Sun-Times\"** or **\"the Sun-Times\"** meaning the **news organization** → **not** a work (that is an organization).\n- **\"Navy Pier\"** as a **location / landmark** → **not** a work.\n\n**Exception — physical or edition-specific artifacts tied to an org or place:**\n- An **individual physical copy** of a newspaper **from a particular date** (e.g. **\"Chicago Sun-Times (print edition, March 12, 2024)\"** or **\"March 12, 2024 Chicago Sun-Times\"**) **is** a work when the story treats that **copy or edition** as an artifact.\n- A **specific broadcast episode** or **named program** as a creative work can be a **tv_show** / **podcast** when it is a **named installment**, not the network as an organization.\n\nIf the referent is ambiguous, prefer **no extraction** unless the text clearly means the **artifact**, not the org or venue.\n\n## Proper names and specificity (dishes excepted)\n\n**Generally, extract only works that have a proper, distinctive name** — a title, brand, bill number, formal report title, statute name, product name, etc.\n\n**Do not extract** vague **category + generic noun** phrases when no **specific** product, drug, law, or title is identified in the story.\n\nExamples — **do not extract**:\n- **\"Glaucoma medicine\"** / **\"blood pressure medication\"** — generic drug categories unless the text names a **specific** medicine (brand or generic proper name) you can infer **from the story** (e.g. **\"Latanoprost\"**, **\"Drug X (trial name)\"** when explicitly named).\n\n**Exception — dishes (`dish` type):** Named or story-specific **menu items** and **dishes** may be extracted even when the name is short or descriptive, as already described for `dish` (include restaurant when helpful).\n\n## Work Types (strict taxonomy)\n\nUse **only** one of these exact type strings. Do not invent variations (e.g. \"legal policy\", \"legal/policy\", \"legal_policy\" — use the specific type below).\n\n| Type | Use for |\n|------|---------|\n| **law** | Enacted laws, statutes |\n| **legislation** | Bills (HB 232, House Bill 892, Senate Bill 444, C.R. 454, etc.) — any proposed or pending legislative measure |\n| **policy** | Policies, regulations, guidelines |\n| **ordinance** | Local ordinances |\n| **ruling** | Court rulings, judicial decisions |\n| **report** | Reports |\n| **study** | Studies |\n| **white_paper** | White papers |\n| **book** | Books |\n| **movie** | Movies |\n| **play** | Plays |\n| **album** | Albums |\n| **song** | Songs |\n| **tv_show** | TV shows |\n| **podcast** | Podcasts |\n| **drug** | Drugs |\n| **consumer_product** | Consumer products |\n| **technology** | Technologies |\n| **software** | Software |\n| **artwork** | Artworks |\n| **statue** | Statues |\n| **installation** | Installations |\n| **exhibition** | Exhibitions |\n| **award** | Awards, prizes, honors |\n| **dish** | Dishes (food) — include restaurant name when available, e.g. \"Carbonara (Joe's Italian)\" |\n| **other** | Fallback when none of the above fit (e.g. a **lawsuit** as a distinct legal filing when not better typed as **ruling**) |\n\n## Who Should NOT Be Included\n\n- **People** — extract as people, not works\n- **Organizations** — companies, agencies, newsrooms, publishers as institutions; see **Organizations and locations are not works** above\n- **Locations** — places, venues, addresses as places; see above\n- **Events** — games, rounds, hearings, ceremonies, etc.; see **Events are not works** above\n- Abstract concepts without a named artifact\n- Generic references without a name (\"a new law\", \"the report\") when you cannot build a **specific, non-ambiguous `name`** from the article\n\n- **Generic category words** — do not extract when the text refers to a class of things rather than a specific named work. Examples:\n  - \"more than 20 ordinances\" → do not extract \"ordinances\" (generic plural, no specific ordinance named)\n  - \"several laws were passed\" → do not extract (generic reference)\n  - \"the report\" without enough detail to identify which report → do not extract **unless** you can expand `name` using story context per **Disambiguating `name`**\n  - **\"Glaucoma medicine\"** and similar — not a work unless a **specific** medicine is named or clearly inferable\n\n- **Symbolic or metaphorical references** — do not extract when a work name is used as a metaphor, simile, or comparison rather than referring to the actual artifact. Example: \"the design has been derided as a 'Taj Mahal'\" → do not extract \"Taj Mahal\" (metaphor for extravagance, not the monument).\n\n- **Generic components of a larger work** — do not extract generic sub-parts that lack a distinct identity and are redundant with the parent project. Example: \"the global terminal\" as a component of \"the O'Hare expansion project\" → extract only the named project, not the generic component. If the component has its own distinct name (e.g., \"Terminal 3\", \"Satellite Concourse A\"), it may be extracted.\n\n- **Generically named policies** — do not extract policies that are only named by a generic label without enough context. If the text provides place, year, or subject, **fold that into `name`** (see below).\n\n## Field Requirements\n\n### name\n\nThe work as a **specific, identifiable artifact**. Use the full, official name when the article provides it.\n\n**Capitalization:** The **first letter of the first word** in `name` must be **uppercase**, even when the article lowercases it or when the phrase is not otherwise a proper noun. Examples: **\"Study on river levels\"** not **\"study on river levels\"**; **\"The midnight library\"** if that is the article’s wording for a book title. Do **not** force title case on every word unless that matches the **official** title (e.g. keep **\"iPhone 15\"**, **\"eBay\"** as the article or official styling shows).\n\n**Disambiguating `name`:** When the article uses a **vague or generic label** for a work (\"2023 report\", \"federal lawsuit\", \"the study\", \"new policy\"), **do not** use that bare phrase as `name` if it would be ambiguous. **Expand `name` with concise context drawn only from the story** so another reader could tell which work is meant:\n\n- **\"2023 report\"** → e.g. **\"2023 report on San Francisco affordability\"** (add subject / author / agency if given)\n- **\"federal lawsuit\"** → e.g. **\"Federal lawsuit against X Corp. (2025)\"** (parties, year, court district if given)\n- **\"the city's climate plan\"** → include year or formal title if stated\n\nUse parentheses for extra metadata when helpful: **\"Production Tax Credit (Missouri, 2026)\"**, **\"Chicago Climate Action Plan (2008)\"**.\n\nIf the article does not provide enough detail to produce a **non-vague** `name`, **do not extract** the work.\n\n### type\n\nOne of the exact work types from the table above (e.g. legislation, law, policy, report). Use the string exactly as shown — no variations.\n\n### role_in_story\n\nA concise summary of the work's importance in this article.\n\n### mentions\n\nEvery instance where the work appears in the text. Each mention should have:\n- `text`: The verbatim text (sentence or paragraph) where the work appears\n\n**Do not include a `quote` field** — works do not have quotes. Only `{text}` for each mention.\n\n## Output Format\n\n**IMPORTANT**: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.\n",
    "json_format": "{\n  \"works\": [\n    {\n      \"name\": \"Affordable Care Act\",\n      \"type\": \"law\",\n      \"role_in_story\": \"Health law cited in debate\",\n      \"mentions\": [\n        {\n          \"text\": \"The Affordable Care Act was cited in the debate.\"\n        }\n      ]\n    },\n    {\n      \"name\": \"Chicago Climate Action Plan\",\n      \"type\": \"report\",\n      \"role_in_story\": \"City sustainability report\",\n      \"mentions\": [\n        {\n          \"text\": \"The Chicago Climate Action Plan outlines emissions targets.\"\n        }\n      ]\n    }\n  ]\n}"
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

import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface WorksExtractPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function WorksExtractPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: WorksExtractPanelProps) {
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node uses an LLM to extract works (laws, reports, books, products, artworks) from text. Use placeholders like {`{text}`} in your prompt.
          </p>
        </div>
      </div>

      <div className="pt-4 border-t">
        <div>
          <Label className="text-sm font-medium">Parameters</Label>
        </div>

        <div className="space-y-2 text-sm mt-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Model</Label>
            {editMode && setNodes ? (
              <Select
                value={node.data.model || 'gpt-5.4-mini'}
                onValueChange={(value) => {
                  setNodes((nds: any[]) =>
                    nds.map((n: any) =>
                      n.id === node.id
                        ? { ...n, data: { ...n.data, model: value } }
                        : n
                    )
                  )
                }}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {nodeMetadata.availableModels?.map((model: any) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="flex justify-between items-center p-2 bg-muted rounded">
                <span className="text-muted-foreground">Model</span>
                <span className="font-medium text-xs">{node.data.model || 'gpt-5.4-mini'}</span>
              </div>
            )}
          </div>
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Prompt</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data?.prompt || nodeMetadata.defaultParams?.prompt || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, prompt: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder="Enter custom prompt"
              className="mt-2 min-h-[200px] px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded max-h-48 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {node.data?.prompt || nodeMetadata.defaultParams?.prompt || 'Using default prompt'}
              </pre>
            </div>
          )}
        </div>

        <div className="pt-2">
          <Label className="text-sm font-medium">Output Format</Label>
          {editMode && setNodes ? (
            <Textarea
              value={node.data?.json_format || nodeMetadata.defaultParams?.json_format || ''}
              onChange={(e) => {
                setNodes((nds: any[]) =>
                  nds.map((n: any) =>
                    n.id === node.id
                      ? { ...n, data: { ...n.data, json_format: e.target.value } }
                      : n
                  )
                )
              }}
              placeholder='{ "works": [] }'
              className="mt-2 min-h-[100px] px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded max-h-48 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {node.data?.json_format || nodeMetadata.defaultParams?.json_format || '{ "works": [] }'}
              </pre>
            </div>
          )}
        </div>
      </div>

      {latestData && latestData.works && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              Works found: {latestData.works.length}
            </div>
            {latestData.works.length > 0 && (
              <div>
                <Label className="text-xs font-medium">Sample Works:</Label>
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {latestData.works.slice(0, 3).map((work: any, index: number) => (
                    <div key={index} className="text-xs p-2 bg-muted rounded">
                      <div className="font-medium">
                        {work.name || 'Unknown'}
                        {work.type && ` (${work.type})`}
                      </div>
                      {work.role_in_story && (
                        <div className="text-muted-foreground mt-1">{work.role_in_story}</div>
                      )}
                      {work.mentions && work.mentions.length > 0 && (
                        <div className="text-muted-foreground mt-1 text-xs">
                          {work.mentions.length} mention{work.mentions.length !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
