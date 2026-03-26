import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Sparkles, Workflow, KeyRound, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react'
import { listProjects, setProjectApiKey, type Project } from '@/lib/api'
import { DEFAULT_PROJECT_NAME, LEGACY_DEFAULT_PROJECT_NAME } from '@/lib/defaultProject'

const STORAGE_KEY = 'agate_demo_welcome_dismissed'

function readInitiallyOpen(): boolean {
  if (typeof window === 'undefined') return false
  return sessionStorage.getItem(STORAGE_KEY) !== '1'
}

export default function WelcomeScreen() {
  const [open, setOpen] = useState(readInitiallyOpen)
  const [step, setStep] = useState(0)
  const [projects, setProjects] = useState<Project[]>([])
  const [projectsLoading, setProjectsLoading] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [savingKey, setSavingKey] = useState(false)
  const [keySaved, setKeySaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const dismiss = useCallback(() => {
    sessionStorage.setItem(STORAGE_KEY, '1')
    setOpen(false)
  }, [])

  const isFinalStep = step === 2
  const canGoNext = step < 2
  const canGoBack = step > 0

  useEffect(() => {
    if (!open) return
    const loadProjects = async () => {
      try {
        setProjectsLoading(true)
        const allProjects = await listProjects()
        setProjects(allProjects)
        const defaultProject =
          allProjects.find((p) => p.name === DEFAULT_PROJECT_NAME) ??
          allProjects.find((p) => p.name === LEGACY_DEFAULT_PROJECT_NAME) ??
          allProjects[0]
        if (defaultProject) {
          setSelectedProjectId(defaultProject.id.toString())
        }
      } catch (e) {
        setError('Could not load projects. You can still continue and set your key later in Project Settings.')
      } finally {
        setProjectsLoading(false)
      }
    }
    loadProjects()
  }, [open])

  const saveApiKey = useCallback(async () => {
    if (!selectedProjectId) {
      setError('Select a project before saving your API key.')
      return false
    }
    if (!apiKey.trim()) {
      setError('Enter an OpenAI API key to continue.')
      return false
    }

    try {
      setSavingKey(true)
      setError(null)
      await setProjectApiKey(Number(selectedProjectId), {
        key_name: 'OPENAI_API_KEY',
        value: apiKey.trim(),
      })
      setKeySaved(true)
      return true
    } catch (e) {
      setError('Failed to save API key. Please try again.')
      return false
    } finally {
      setSavingKey(false)
    }
  }, [apiKey, selectedProjectId])

  const onPrimaryAction = useCallback(async () => {
    if (canGoNext) {
      setStep((s) => s + 1)
      return
    }

    if (!keySaved) {
      const saved = await saveApiKey()
      if (!saved) return
    }
    dismiss()
  }, [canGoNext, dismiss, keySaved, saveApiKey])

  // Lock page scroll while overlay is open so the document doesn't scroll behind it.
  useEffect(() => {
    if (!open) return
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [open])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[100] overflow-hidden"
      aria-modal="true"
      role="dialog"
      aria-labelledby="welcome-title"
    >
      {/* Scrim: dims and blurs the app behind for clear separation */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-md supports-[backdrop-filter]:bg-black/45"
        aria-hidden
      />

      <div className="relative z-10 flex h-[100dvh] items-center justify-center px-4 py-8 sm:px-6">
        <Card className="w-full max-w-3xl border-border/80 bg-card/95 shadow-2xl ring-1 ring-border/60 backdrop-blur-sm">
          <CardHeader className="space-y-4">
            <div className="flex items-center gap-2 text-primary">
              <Sparkles className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Agate AI Demo</span>
            </div>
            <CardTitle id="welcome-title" className="text-2xl font-semibold tracking-tight sm:text-3xl">
              {step === 0 && 'Welcome to Agate'}
              {step === 1 && 'An engine for structured journalism'}
              {step === 2 && 'Get started'}
            </CardTitle>
            <div className="flex items-center gap-2">
              {[0, 1, 2].map((idx) => (
                <div
                  key={idx}
                  className={`h-1.5 flex-1 rounded-full ${idx <= step ? 'bg-primary' : 'bg-muted'}`}
                />
              ))}
            </div>
          </CardHeader>

          <CardContent className="space-y-4 text-sm text-muted-foreground">
            {step === 0 && (
              <div className="rounded-lg border bg-background/60 p-5">
                <p className="text-sm leading-relaxed">
                  Agate uses large language models, along with other tools, to turn news articles into
                  structured, durable knowledge. It is built and maintained by{' '}
                  <a
                    href="https://localangle.co"
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Local Angle
                  </a>
                  {' '}and released under an MIT License.
                </p>
                <p className="mt-3 text-sm leading-relaxed">
                  <a
                    href="https://github.com/minneapolisstartribune/agate-ai"
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Initial work
                  </a>
                  {' '}began under Lenfest AI Collaborative and Fellowship Program at the Minnesota Star
                  Tribune and has continued with additional support from Chicago Public Media and the
                  Reynolds Journalism Institute.
                </p>
                <p className="mt-3 text-sm leading-relaxed">
                  This demo will demonstrate some of Agate&apos;s basic capabilities, using a series
                  of composable workflows to extract and enrich data from news articles provided by
                  Chicago Public Media.
                </p>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-3">
                <div className="rounded-lg border bg-background/60 p-5">
                  <p className="text-sm leading-relaxed">
                    Agate is capable of creating countless types of structured information from news
                    articles, keeping journalistic conventions and local knowledge in mind.
                  </p>
                  <p className="mt-3 text-sm leading-relaxed">This demo includes examples of:</p>
                  <ul className="mt-3 space-y-2">
                    <li className="flex items-start gap-2 text-sm leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <span>Extracting and geocoding places mentioned in news articles</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <span>Identifying and verifying people, organizations, quotes and other atomic elements of news stories</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <span>Turning text (in this case a recipe) into a structured schema</span>
                    </li>
                    <li className="flex items-start gap-2 text-sm leading-relaxed">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <span>Adding bespoke metadata to stories to define their editorial purpose</span>
                    </li>
                  </ul>
                  <p className="mt-4 text-sm leading-relaxed">
                    It is part of an ecosystem of applications created by Local Angle, designed to
                    simplify and scale the creation of{' '}
                    <a
                      href="https://www.niemanlab.org/2025/12/a-renaissance-for-structured-journalism/"
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-primary underline-offset-4 hover:underline"
                    >
                      structured journalism
                    </a>{' '}
                    and create more impact from the stories journalists produce every day.
                  </p>
                  <p className="mt-3 text-sm leading-relaxed">
                    If you have questions, contact{' '}
                    <strong className="font-semibold text-foreground">chase@localangle.co</strong>.
                  </p>
                </div>
              </div>
            )}

            {isFinalStep && (
              <div className="space-y-4">
                <div className="flex items-start gap-3 rounded-lg border bg-background/60 p-4">
                  <KeyRound className="mt-0.5 h-4 w-4 text-primary" />
                  <p>
                    This demo vesion of Agate relies only on free and open source services to support its workflows, with one exception: It requires an{' '}
                    <a
                      href="https://platform.openai.com/"
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-primary underline-offset-4 hover:underline"
                    >
                      OpenAI API key
                    </a>
                    . Enter yours below to get started.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="welcome-openai-key">OpenAI API Key</Label>
                  <Input
                    id="welcome-openai-key"
                    type="password"
                    placeholder="sk-..."
                    value={apiKey}
                    onChange={(e) => {
                      setApiKey(e.target.value)
                      if (keySaved) setKeySaved(false)
                      if (error) setError(null)
                    }}
                  />
                </div>

                {error && <p className="text-sm text-destructive">{error}</p>}
                {keySaved && (
                  <p className="text-sm text-emerald-600">
                    OpenAI key saved successfully. You are ready to enter the demo.
                  </p>
                )}
              </div>
            )}
          </CardContent>

          <CardFooter className="flex flex-col items-stretch gap-2 sm:flex-row sm:justify-between">
            <div className="flex gap-2">
              {canGoBack && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep((s) => Math.max(0, s - 1))}
                  disabled={savingKey}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
              )}
              {isFinalStep && (
                <Button type="button" variant="ghost" onClick={dismiss} disabled={savingKey}>
                  Skip for now
                </Button>
              )}
            </div>

            <Button type="button" onClick={onPrimaryAction} disabled={savingKey || projectsLoading}>
              {savingKey ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving key...
                </>
              ) : isFinalStep ? (
                keySaved ? 'Enter demo' : 'Save key and enter demo'
              ) : (
                <>
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
