import { createRouter, createWebHistory } from "vue-router"

import { useAuthStore } from "@/stores/auth"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("@/views/LoginView.vue"), meta: { public: true } },
    { path: "/register", name: "register", component: () => import("@/views/RegisterView.vue"), meta: { public: true } },
    {
      path: "/",
      component: () => import("@/layouts/AppLayout.vue"),
      children: [
        { path: "", redirect: "/dashboard" },
        { path: "dashboard", name: "dashboard", component: () => import("@/views/DashboardView.vue") },
        { path: "vacancies", name: "vacancies", component: () => import("@/views/VacanciesView.vue") },
        { path: "vacancies/ai", name: "vacancy-ai", component: () => import("@/views/AiVacancyView.vue") },
        { path: "vacancies/:id", name: "vacancy", component: () => import("@/views/VacancyDetailView.vue") },
        { path: "vacancies/:id/pipeline", name: "pipeline", component: () => import("@/views/PipelineView.vue") },
        { path: "applications/:id", name: "application", component: () => import("@/views/ApplicationDetailView.vue") },
        { path: "templates", name: "templates", component: () => import("@/views/TemplatesView.vue") },
        { path: "automation", name: "automation", component: () => import("@/views/AutomationView.vue") },
        { path: "settings", name: "settings", component: () => import("@/views/SettingsView.vue") },
        { path: "profile", name: "profile", component: () => import("@/views/ProfileView.vue") },
        // Super-admin
        { path: "admin/organizations", name: "admin-orgs", component: () => import("@/views/admin/OrganizationsView.vue"), meta: { superadmin: true } },
        { path: "admin/platform", name: "admin-platform", component: () => import("@/views/admin/PlatformView.vue"), meta: { superadmin: true } },
      ],
    },
    { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.fetchMe()

  if (to.meta.public) {
    if (auth.isAuthenticated) return { name: auth.isSuperadmin ? "admin-platform" : "dashboard" }
    return true
  }
  if (!auth.isAuthenticated) return { name: "login" }
  if (to.meta.superadmin && !auth.isSuperadmin) return { name: "dashboard" }
  // Org-only pages: keep super-admins out of org dashboard
  if (!to.meta.superadmin && auth.isSuperadmin && ["dashboard", "vacancies", "templates", "automation", "settings"].includes(String(to.name))) {
    return { name: "admin-platform" }
  }
  return true
})

export default router
