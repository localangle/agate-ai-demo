// Auto-injected metadata for PeopleExtract
const nodeMetadata = {
  "type": "PeopleExtract",
  "name": "PeopleExtract",
  "label": "People Extract",
  "description": "Extract people information from text using LLM.",
  "category": "extraction",
  "icon": "User",
  "color": "bg-indigo-500",
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
      "id": "people",
      "label": "People",
      "type": "array"
    }
  ],
  "defaultParams": {
    "model": "gpt-5.4-mini",
    "prompt_file": "prompts/extract.md",
    "prompt": "# People Extraction Service\n\nActing as a state-of-the-art entity extraction service, identify and extract all editorially relevant people mentioned in the following text.\n\n## Text to Analyze\n\n{text}\n\n## Overview\n\nExtract a person only if:\n1. **Their name is mentioned in the story** (first name, last name, or full name)\n2. They directly matter to the story's events, actions, statements, or reporting, such as:\n   - People whose actions are central to the story\n   - People affected by the events of the story (victims, residents, business owners, witnesses)\n   - People quoted or paraphrased\n   - Officials, employees, or representatives whose statements or actions are relevant\n   - Subjects of investigations, lawsuits, decisions, or policies\n   - Individuals whose identity is necessary for understanding the story\n\n**IMPORTANT**: Do not extract people who are only referred to generically without a name, such as \"a store owner,\" \"the dispatcher,\" \"a teacher,\" \"residents,\" or \"witnesses\" unless a specific name is provided.\n\n## Who Should NOT Be Included\n\nDo not extract:\n\n### Article authors and contributors\n\n- Journalists, reporters, or writers who authored the article\n- Contributors, editors, or other staff who worked on the article\n- Photographers or other media creators credited with the article\n- Byline names or author credits should not be extracted as people in the story\n\n### Non-story-relevant individuals\n\n- Historical figures (e.g., Abraham Lincoln)\n- Religious figures (Jesus, Buddha, Muhammad, saints, prophets)\n- Mythological or fictional characters\n- Celebrities used metaphorically (\"He pulled a Beyoncé move\")\n- People mentioned only as analogies (\"He's no Einstein\")\n- People referenced in idioms or generic cultural shorthand (\"Don't be a Scrooge.\")\n\n### Not involved in the article's events\n\n- Authors of unrelated studies, reports, or research (unless they actively play a role in the story)\n- People mentioned only as optional context or background, not tied to the current events\n- People quoted in other publications unless the article uses them as primary sources for its own reporting\n\n### Institutional misinterpretations\n\n- Do not treat institutions as people, even if personified\n- Example: \"DHS said…\" — do not create a person for this\n- Statements by unnamed institutions (\"the agency said\") do not count as persons\n\n### Generic references without names\n\n- **Do not extract people referred to only by role or title without a name**, such as:\n  - \"a store owner said…\"\n  - \"the dispatcher reported…\"\n  - \"a teacher mentioned…\"\n  - \"the mayor announced…\" (unless the mayor's name is also mentioned)\n  - \"residents said…\"\n  - \"witnesses reported…\"\n  - \"officials stated…\"\n- Only extract if a specific name (first name, last name, or full name) is provided in the article\n- Crowds or groups (\"residents said…\") should never be extracted, even if they are quoted\n\n## Person Identification Rules\n\n### 1. Names Required\n\n**A person must have a name mentioned in the article to be extracted.** This means:\n- First name, last name, or full name must appear in the text\n- Generic titles alone (\"the mayor,\" \"the dispatcher\") are not sufficient\n- If a person is mentioned by both name and title (e.g., \"Mayor John Smith\"), extract them using the name\n\n### 2. Alias & Coreference Handling\n\nYou must merge all references to the same person into one record:\n\n- Full name → last name only later\n- Full name → pronouns referring back\n- Nicknames → official names (if obvious and unambiguous)\n- Role/title references → same person if clearly linked\n\nExample: \"Superintendent Lisa Johnson\" → \"Johnson\" → \"the superintendent\"\n\n### 3. Disambiguation Rules\n\n- If two people share the same last name, maintain separate entries\n- Only merge when there is unambiguous evidence they are the same person\n\n### 4. Pronoun Linking\n\nFor each person, include any sentence or paragraph where a pronoun refers to them, even if their name is not repeated.\n\n## Quote Identification Rules\n\nMark `quote: true` if the mention contains:\n\n- A direct quote attributed to the person (\"I'm not resigning,\" Johnson said.)\n- An indirect quote (Johnson said she would not resign.)\n- A paraphrased attribution (Johnson argued the policy is flawed.)\n\nIf the person is simply mentioned in a quoted segment but not as the speaker, mark `quote: false`.\n\n### Complete quotes when split by attribution\n\nWhen a direct quote is split by attribution (e.g., \"Part one,\" he said. \"Part two.\"), capture the **complete quote** in a single mention—include both the part before and after the attribution. Do not truncate at the attribution.\n\nExample: \"I want to be a source of inspiration for my students,\" he said when asked about the impact on students. \"When you try to be the best musician, player and conductor you can be, that's one way you can inspire them to try to be the best they can be.\"\n\n→ Extract as one mention containing the full text above (both quoted segments plus the attribution between them).\n\n## Mentions List Granularity\n\n- Use sentences as the default unit\n- If sentence boundaries are unclear or broken, use paragraphs instead\n- Each mention should be self-contained and unmodified except for trimming whitespace\n\n## Public Figure Detection\n\nSet `\"public_figure\": true` if the person is widely known, such as:\n\n- Politicians, elected officials\n- CEOs of major organizations\n- Professional athletes\n- Actors, musicians, artists, authors\n- Major business leaders\n- Any person likely to appear in Wikipedia or Ballotpedia\n\nUse common sense and contextual clues.\n\n## Field Requirements\n\n### name.full\n\nThe complete name as given on first mention. **Must be an actual name** (first name, last name, or full name). Do not use generic titles like \"the mayor\" or \"a store owner\" - only extract if a name is provided.\n\n### name.first / name.last\n\nExtract from the full name when possible. If the article gives only one name, leave the others as empty strings.\n\n### title\n\nThe person's role or position **only**—the job title, role, or descriptor. Include both **official titles** (Mayor, Superintendent, Police Chief, Professor) and **informal or role-based titles** (shortstop, advocate, spokesperson, team captain, store owner, witness).\n\n**CRITICAL**: Do NOT include the organization or affiliation name in the title. Keep title and affiliation separate.\n\n- If the text says \"owner of Billiards on Broadway\" → title: \"Owner\", affiliation: \"Billiards on Broadway\"\n- If the text says \"Former owner of Billiards on Broadway\" → title: \"Former owner\", affiliation: \"Billiards on Broadway\"\n- If the text says \"Superintendent of Chicago Public Schools\" → title: \"Superintendent\", affiliation: \"Chicago Public Schools\"\n\nThe title should be the role/position alone (e.g., \"Owner\", \"Mayor\", \"Spokesperson\"). The affiliation should contain the organization or entity name.\n\n### affiliation\n\nThe institution or organization tied to the title or role. Example: \"Chicago Public Schools,\" \"University of Minnesota,\" \"Billiards on Broadway.\" Do not repeat this in the title field.\n\n### public_figure\n\nSee rules above.\n\n### role_in_story\n\nA concise summary of the person's importance in this article. Should be just a sentence fragment or brief phrase.\n\n### mentions\n\nEvery instance (sentence or paragraph) where the person appears or is referred to by pronoun. Include:\n\n- Verbatim text\n- Whether it contains a quote from the person (`quote: true`)\n\nDo not combine sentences; each mention is separate.\n\n**CRITICAL**: Each mention MUST be a JSON object with exactly two keys:\n- `\"text\"`: string — the verbatim text of the mention\n- `\"quote\"`: boolean — true if the mention contains a direct/indirect quote from the person\n\n**Never** use plain strings for mentions. Always use objects. Example:\n```json\n\"mentions\": [\n  {{\"text\": \"Johnson said she would not resign.\", \"quote\": true}},\n  {{\"text\": \"The superintendent has been in the role since 2019.\", \"quote\": false}}\n]\n```\n\n## Output Format\n\n**IMPORTANT**: Return ONLY valid JSON. Do not include any explanatory text before or after the JSON.\n\nEach person object **must** include:\n- `name`: an object with `full` (required), `first`, and `last` — e.g. `{{\"full\": \"John Smith\", \"first\": \"John\", \"last\": \"Smith\"}}`\n- `title`: string — the person's role or position (official or informal)\n- `affiliation`: string — institution or organization if mentioned\n- `role_in_story`: string\n- `mentions`: array of objects, each with `\"text\"` (string) and `\"quote\"` (boolean) — see example above",
    "json_format": "{\n  \"people\": [\n    {\n      \"name\": {\n        \"full\": \"John Smith\",\n        \"first\": \"John\",\n        \"last\": \"Smith\"\n      },\n      \"title\": \"Mayor\",\n      \"affiliation\": \"City of Chicago\",\n      \"public_figure\": true,\n      \"role_in_story\": \"Announced new policy initiative\",\n      \"mentions\": [\n        {\n          \"text\": \"Mayor John Smith announced a new policy initiative on Monday.\",\n          \"quote\": false\n        },\n        {\n          \"text\": \"\\\"This will benefit all residents,\\\" Smith said.\",\n          \"quote\": true\n        }\n      ]\n    },\n    {\n      \"name\": {\n        \"full\": \"Jane Doe\",\n        \"first\": \"Jane\",\n        \"last\": \"Doe\"\n      },\n      \"title\": \"\",\n      \"affiliation\": \"\",\n      \"public_figure\": false,\n      \"role_in_story\": \"Resident affected by the policy\",\n      \"mentions\": [\n        {\n          \"text\": \"Jane Doe, a local resident, expressed concerns about the new policy.\",\n          \"quote\": false\n        }\n      ]\n    }\n  ]\n}"
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

interface PeopleExtractPanelProps {
  node: any
  onChange?: (text: string) => void
  onRun?: () => void
  running?: boolean
  currentRun?: any
  editMode?: boolean
  setNodes?: (nodes: any) => void
}

export default function PeopleExtractPanel({
  node,
  onChange,
  onRun,
  running,
  currentRun,
  editMode,
  setNodes
}: PeopleExtractPanelProps) {
  // Get latest run data - only show if we have specific node output
  const nodeOutput = currentRun?.node_outputs?.[node.id]
  const latestData = nodeOutput || null

  return (
    <>
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-medium">Description</Label>
          <p className="text-sm text-muted-foreground mt-1">
            This node uses an LLM to process JSON according to your custom prompt and returns structured people data. Use JSON path placeholders in your prompt to extract specific fields:
            <ul className="list-disc list-inside text-xs mt-2 space-y-1">
              <li><code className="bg-muted px-1 rounded">{'{text}'}</code> - extracts the text field</li>
              <li><code className="bg-muted px-1 rounded">{'{url}'}</code> - extracts the url field</li>
              <li><code className="bg-muted px-1 rounded">{'{results.images}'}</code> - extracts nested results.images object/array</li>
              <li><code className="bg-muted px-1 rounded">{'{results.caption}'}</code> - extracts only caption field from array elements</li>
              <li><code className="bg-muted px-1 rounded">{'{results.caption, id}'}</code> - extracts multiple fields from array elements</li>
              <li><code className="bg-muted px-1 rounded">{'{raw}'}</code> - passes entire input JSON</li>
            </ul>
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
          <p className="text-xs text-muted-foreground mt-1">
            Customize the prompt for extracting people. Use placeholders like {`{text}`}, {`{url}`}, {`{results.images}`}, {`{results.caption}`}, {`{results.caption, id}`}, {`{raw}`}.
          </p>
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
              placeholder='{ "people": [] }'
              className="mt-2 min-h-[100px] px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-mono"
            />
          ) : (
            <div className="mt-2 p-2 bg-muted rounded max-h-48 overflow-y-auto">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {node.data?.json_format || nodeMetadata.defaultParams?.json_format || '{ "people": [] }'}
              </pre>
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Example output JSON. Braces are escaped automatically in the prompt.
          </p>
        </div>
      </div>

      {latestData && latestData.people && (
        <div className="pt-4 border-t">
          <Label className="text-sm font-medium">Latest Run</Label>
          <div className="mt-2 space-y-2">
            <div className="text-xs text-muted-foreground">
              <div>People found: {latestData.people.length}</div>
            </div>
            
            {latestData.people.length > 0 && (
              <div>
                <Label className="text-xs font-medium">Sample People:</Label>
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {latestData.people.slice(0, 3).map((person: any, index: number) => (
                    <div key={index} className="text-xs p-2 bg-muted rounded">
                      <div className="font-medium">
                        {person.name?.full || person.name || 'Unknown'}
                        {person.title && ` - ${person.title}`}
                      </div>
                      {person.role_in_story && (
                        <div className="text-muted-foreground mt-1">{person.role_in_story}</div>
                      )}
                      {person.mentions && person.mentions.length > 0 && (
                        <div className="text-muted-foreground mt-1 text-xs">
                          {person.mentions.length} mention{person.mentions.length !== 1 ? 's' : ''}
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

