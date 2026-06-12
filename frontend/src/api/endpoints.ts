import { api } from "./client"
import type {
  ActionPayload,
  Activity,
  AutomationRule,
  ApplicationDetail,
  ApplicationListItem,
  LoginResponse,
  MessageItem,
  Organization,
  OrganizationAdmin,
  OrgDashboard,
  OrgStatus,
  EventType,
  InterviewItem,
  PlatformDashboard,
  SubmissionItem,
  Template,
  TemplateType,
  User,
  Vacancy,
} from "./types"

// ---- Auth ----
export const authApi = {
  async login(email: string, password: string) {
    const form = new URLSearchParams({ username: email, password })
    const { data } = await api.post<LoginResponse>("/auth/login", form)
    return data
  },
  async register(payload: {
    organization_name: string
    full_name: string
    email: string
    password: string
  }) {
    const { data } = await api.post<User>("/auth/register", payload)
    return data
  },
  async me() {
    const { data } = await api.get<User>("/auth/me")
    return data
  },
}

// ---- Organizations ----
export const orgApi = {
  async me() {
    const { data } = await api.get<Organization>("/organizations/me")
    return data
  },
  async setTelegram(bot_token: string) {
    const { data } = await api.put<Organization>("/organizations/me/telegram", { bot_token })
    return data
  },
  async setAI(provider: string, model: string, api_key: string) {
    const { data } = await api.put<Organization>("/organizations/me/ai", { provider, model, api_key })
    return data
  },
  async setGdpr(retention_days: number | null, privacy_notice: string | null) {
    const { data } = await api.put<Organization>("/organizations/me/gdpr", {
      retention_days,
      privacy_notice,
    })
    return data
  },
  async list(status?: OrgStatus) {
    const { data } = await api.get<OrganizationAdmin[]>("/organizations", {
      params: status ? { status_filter: status } : {},
    })
    return data
  },
  async setStatus(orgId: number, status: OrgStatus) {
    const { data } = await api.patch<OrganizationAdmin>(`/organizations/${orgId}/status`, { status })
    return data
  },
}

// ---- Vacancies ----
export const vacancyApi = {
  async list() {
    const { data } = await api.get<Vacancy[]>("/vacancies")
    return data
  },
  async get(id: number) {
    const { data } = await api.get<Vacancy>(`/vacancies/${id}`)
    return data
  },
  async create(payload: Partial<Vacancy>) {
    const { data } = await api.post<Vacancy>("/vacancies", payload)
    return data
  },
  async update(id: number, payload: Partial<Vacancy>) {
    const { data } = await api.patch<Vacancy>(`/vacancies/${id}`, payload)
    return data
  },
  async remove(id: number) {
    await api.delete(`/vacancies/${id}`)
  },
}

// ---- Applications ----
export const applicationApi = {
  async list(params: {
    vacancy_id?: number
    status?: string
    min_score?: number
    sort?: string
  }) {
    const { data } = await api.get<ApplicationListItem[]>("/applications", { params })
    return data
  },
  async get(id: number) {
    const { data } = await api.get<ApplicationDetail>(`/applications/${id}`)
    return data
  },
  async rescore(id: number) {
    const { data } = await api.post<ApplicationDetail>(`/applications/${id}/rescore`)
    return data
  },
  async updateStage(id: number, stage: string, reason?: string) {
    const { data } = await api.patch<ApplicationDetail>(`/applications/${id}/stage`, { stage, reason })
    return data
  },
  async timeline(id: number) {
    const { data } = await api.get<Activity[]>(`/applications/${id}/timeline`)
    return data
  },
  async messages(id: number) {
    const { data } = await api.get<MessageItem[]>(`/applications/${id}/messages`)
    return data
  },
  async sendMessage(id: number, body: string) {
    const { data } = await api.post<MessageItem>(`/applications/${id}/messages`, { body })
    return data
  },
  async setChatOpen(id: number, open: boolean) {
    const { data } = await api.patch<ApplicationDetail>(`/applications/${id}/chat`, { open })
    return data
  },
  async runAction(id: number, action: string, payload: ActionPayload) {
    const { data } = await api.post<ApplicationDetail>(`/applications/${id}/actions/${action}`, payload)
    return data
  },
  async submissions(id: number) {
    const { data } = await api.get<SubmissionItem[]>(`/applications/${id}/submissions`)
    return data
  },
  async interviews(id: number) {
    const { data } = await api.get<InterviewItem[]>(`/applications/${id}/interviews`)
    return data
  },
  resumeUrl(id: number) {
    return `${api.defaults.baseURL}/applications/${id}/resume`
  },
  coverLetterUrl(id: number) {
    return `${api.defaults.baseURL}/applications/${id}/cover-letter`
  },
  async upload(vacancyId: number, file: File) {
    const form = new FormData()
    form.append("file", file)
    const { data } = await api.post<ApplicationDetail>("/applications/upload", form, {
      params: { vacancy_id: vacancyId },
    })
    return data
  },
}

// ---- Scheduling (Calendly) ----
export const schedulingApi = {
  async eventTypes(token: string) {
    const { data } = await api.post<EventType[]>("/scheduling/calendly/event-types", { token })
    return data
  },
  async connect(payload: { token: string; event_type_uri: string; scheduling_url: string }) {
    const { data } = await api.post("/scheduling/calendly/connect", payload)
    return data
  },
}

// ---- Automation rules ----
export const automationApi = {
  async list() {
    const { data } = await api.get<AutomationRule[]>("/automation-rules")
    return data
  },
  async create(payload: Partial<AutomationRule>) {
    const { data } = await api.post<AutomationRule>("/automation-rules", payload)
    return data
  },
  async update(id: number, payload: Partial<AutomationRule>) {
    const { data } = await api.patch<AutomationRule>(`/automation-rules/${id}`, payload)
    return data
  },
  async remove(id: number) {
    await api.delete(`/automation-rules/${id}`)
  },
}

// ---- Templates ----
export const templateApi = {
  async list() {
    const { data } = await api.get<Template[]>("/templates")
    return data
  },
  async create(payload: { type: TemplateType; name: string; body: string }) {
    const { data } = await api.post<Template>("/templates", payload)
    return data
  },
  async update(id: number, payload: { name?: string; body?: string }) {
    const { data } = await api.patch<Template>(`/templates/${id}`, payload)
    return data
  },
  async remove(id: number) {
    await api.delete(`/templates/${id}`)
  },
}

// ---- Analytics ----
export const analyticsApi = {
  async dashboard() {
    const { data } = await api.get<OrgDashboard>("/analytics/dashboard")
    return data
  },
  async platform() {
    const { data } = await api.get<PlatformDashboard>("/analytics/platform")
    return data
  },
}
