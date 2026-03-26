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

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight, CheckCircle, XCircle } from 'lucide-react'
import type { VisualizationProps, VisualizationDescriptor } from '@/lib/visualizations'

/**
 * Build visualization descriptor for PeopleExtract node output.
 * Returns null if no valid people data is found.
 */
export function buildVisualization(
  nodeId: string,
  nodeLabel: string,
  output: any
): VisualizationDescriptor | null {
  if (!output || typeof output !== 'object') {
    return null
  }

  const people = output.people
  if (!Array.isArray(people) || people.length === 0) {
    return null
  }

  // Visualization component
  const PeopleExtractVisualization: React.FC<VisualizationProps> = ({ nodeId, nodeLabel, output }) => {
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

    const people = output?.people || []

    return (
      <Card>
        <CardHeader>
          <CardTitle>People Extract</CardTitle>
          {nodeLabel !== nodeId && (
            <CardDescription>{nodeLabel}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[200px]">Name</TableHead>
                  <TableHead className="w-[150px]">Title</TableHead>
                  <TableHead className="w-[200px]">Affiliation</TableHead>
                  <TableHead>Role in Story</TableHead>
                  <TableHead className="w-[100px]">Public Figure</TableHead>
                  <TableHead className="w-[120px]">Mentions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {people.map((person: any, index: number) => {
                  const name = person.name
                  const fullName = typeof name === 'string' ? name : name?.full || 'Unknown'
                  const firstName = typeof name === 'object' ? name?.first || '' : ''
                  const lastName = typeof name === 'object' ? name?.last || '' : ''
                  const displayName = fullName || `${firstName} ${lastName}`.trim() || 'Unknown'
                  
                  const mentions = person.mentions || []
                  const isExpanded = expandedMentions.has(index)

                  return (
                    <React.Fragment key={index}>
                      <TableRow>
                        <TableCell className="font-medium">{displayName}</TableCell>
                        <TableCell>{person.title || '-'}</TableCell>
                        <TableCell>{person.affiliation || '-'}</TableCell>
                        <TableCell>{person.role_in_story || '-'}</TableCell>
                        <TableCell>{person.public_figure ? 'Yes' : 'No'}</TableCell>
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
                      {isExpanded && mentions.length > 0 && (
                        <TableRow>
                          <TableCell colSpan={6} className="bg-muted/50">
                            <div className="space-y-2 py-2">
                              <div className="text-xs font-medium text-muted-foreground">Mentions:</div>
                              {mentions.map((mention: any, mentionIndex: number) => {
                                const isVerified = mention.verified ?? false
                                
                                return (
                                  <div key={mentionIndex} className="text-sm pl-4 border-l-2 border-border">
                                    <div className="flex items-start gap-2">
                                      <div className="flex items-center gap-1.5 mt-0.5">
                                        {isVerified ? (
                                          <CheckCircle className="h-4 w-4 text-green-600" title="Verified: Mention found in original text" />
                                        ) : (
                                          <XCircle className="h-4 w-4 text-red-600" title="Not verified: Mention not found in original text" />
                                        )}
                                        {mention.quote && (
                                          <span className="text-xs font-medium text-primary px-1.5 py-0.5 bg-primary/10 rounded">Quote</span>
                                        )}
                                      </div>
                                      <span className="flex-1">{mention.text}</span>
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
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
    id: `${nodeId}-people`,
    nodeId,
    title: 'People Extract',
    description: nodeLabel !== nodeId ? nodeLabel : undefined,
    component: PeopleExtractVisualization,
    data: undefined,
  }
}

