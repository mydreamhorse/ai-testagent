import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue')
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/requirements',
      name: 'Requirements',
      component: () => import('@/views/RequirementsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/requirements/:id',
      name: 'RequirementDetail',
      component: () => import('@/views/RequirementDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test-cases',
      name: 'TestCases',
      component: () => import('@/views/TestCasesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test-cases/:id',
      name: 'TestCaseDetail',
      component: () => import('@/views/TestCaseDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/generation',
      name: 'Generation',
      component: () => import('@/views/GenerationView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/analytics',
      name: 'Analytics',
      component: () => import('@/views/AnalyticsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('@/views/KnowledgeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/templates',
      name: 'Templates',
      component: () => import('@/views/TemplatesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test-data',
      name: 'TestData',
      component: () => import('@/views/TestDataView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // Check if the route requires authentication
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      next('/login')
      return
    }
  }
  
  // If user is authenticated and trying to access login, redirect to dashboard
  if (to.path === '/login' && userStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router