export type UserRole = "superadmin" | "org_admin" | "org_member"
export type OrgStatus = "pending" | "active" | "suspended"
export type VacancyStatus = "draft" | "open" | "closed"
export type ApplicationStatus = "pending" | "processing" | "scored" | "failed"
export type ApplicationStage =
  | "new"
  | "screening"
  | "shortlisted"
  | "test_task"
  | "interview"
  | "offer"
  | "hired"
  | "rejected"
  | "withdrawn"
export type ApplicationSource = "telegram" | "manual"
export type AIProviderName = "claude" | "openai"

export const STAGE_ORDER: ApplicationStage[] = [
  "new",
  "screening",
  "shortlisted",
  "test_task",
  "interview",
  "offer",
  "hired",
]

export const STAGE_LABELS: Record<ApplicationStage, string> = {
  new: "New",
  screening: "Screening",
  shortlisted: "Shortlisted",
  test_task: "Test Task",
  interview: "Interview",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
}

export interface Activity {
  id: number
  type: string
  actor: "user" | "system" | "candidate"
  summary: string
  payload: Record<string, unknown> | null
  created_at: string
}

export type TemplateType = "test_task" | "interview" | "offer" | "rejection" | "custom"

export interface Template {
  id: number
  type: TemplateType
  name: string
  body: string
  is_default: boolean
}

export interface MessageItem {
  id: number
  direction: "outbound" | "inbound"
  body: string
  status: "sent" | "failed" | "received"
  error: string | null
  created_at: string
}

export interface ActionPayload {
  template_id?: number | null
  body?: string | null
  variables?: Record<string, string>
}

export interface SubmissionItem {
  id: number
  original_filename: string | null
  status: "pending" | "processing" | "graded" | "failed"
  ai_score: number | null
  ai_feedback: AIResult | null
  error: string | null
  created_at: string
}

export interface EventType {
  uri: string
  name: string
  scheduling_url: string
  duration: number | null
}

export interface InterviewItem {
  id: number
  provider: string
  scheduled_at: string | null
  end_at: string | null
  join_url: string | null
  location: string | null
  status: "scheduled" | "canceled" | "completed"
}

export type AutomationAction = "reject" | "shortlist" | "set_stage" | "send_template"

export interface AutomationRule {
  id: number
  name: string
  vacancy_id: number | null
  min_score: number
  max_score: number
  action: AutomationAction
  template_id: number | null
  enabled: boolean
  priority: number
}

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  org_id: number | null
  is_active: boolean
}

export interface Tokens {
  access_token: string
  refresh_token: string
  token_type: string
}
export interface LoginResponse extends Tokens {
  user: User
}

export interface Organization {
  id: number
  name: string
  slug: string
  status: OrgStatus
  telegram_bot_username: string | null
  telegram_configured: boolean
  ai_provider: AIProviderName | null
  ai_model: string | null
  ai_configured: boolean
  calendly_configured?: boolean
  calendly_scheduling_url?: string | null
  retention_days?: number | null
  privacy_notice?: string | null
}
export interface OrganizationAdmin extends Organization {
  user_count: number
  vacancy_count: number
}

export interface Vacancy {
  id: number
  org_id: number
  title: string
  description: string
  requirements: string
  employment_type: string | null
  location: string | null
  ai_instructions: string | null
  status: VacancyStatus
  deep_link_param: string | null
  deep_link_url: string | null
  application_count: number
}

export interface Candidate {
  id: number
  telegram_username: string | null
  telegram_user_id: number | null
  full_name: string | null
  email: string | null
}

export interface AIResult {
  match_percentage: number
  verdict: string
  recommended: boolean
  matched_skills: string[]
  missing_skills: string[]
  strengths: string[]
  concerns: string[]
  summary: string
}

export interface ApplicationListItem {
  id: number
  vacancy_id: number
  status: ApplicationStatus
  stage: ApplicationStage
  source: ApplicationSource
  match_percentage: number | null
  original_filename: string | null
  candidate: Candidate | null
  created_at: string
  scored_at: string | null
  last_activity_at: string | null
  chat_open: boolean
}
export interface ApplicationDetail extends ApplicationListItem {
  ai_result: AIResult | null
  ai_provider: string | null
  error: string | null
  extracted_text: string | null
  file_mime: string | null
  decision_reason: string | null
  cover_letter_text: string | null
  cover_letter_filename: string | null
}

export interface VacancyStat {
  vacancy_id: number
  title: string
  application_count: number
  avg_score: number | null
  recommended_count: number
}
export interface OrgDashboard {
  total_applications: number
  scored_applications: number
  pending_applications: number
  failed_applications: number
  avg_score: number | null
  recommended_count: number
  open_vacancies: number
  score_distribution: Record<string, number>
  per_vacancy: VacancyStat[]
  recent: ApplicationListItem[]
}
export interface PlatformDashboard {
  total_organizations: number
  pending_organizations: number
  active_organizations: number
  suspended_organizations: number
  total_users: number
  total_vacancies: number
  total_applications: number
}
