import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import Login from '@/pages/Login.vue'
import Dashboard from '@/pages/Dashboard.vue'
import Generate from '@/pages/Generate.vue'
import Articles from '@/pages/Articles.vue'
import Styles from '@/pages/Styles.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'generate',
        name: 'Generate',
        component: Generate
      },
      {
        path: 'articles',
        name: 'Articles',
        component: Articles
      },
      {
        path: 'articles/:id',
        name: 'ArticleDetail',
        component: () => import('@/pages/ArticleDetail.vue')
      },
      {
        path: 'styles',
        name: 'Styles',
        component: Styles
      },
      {
        path: 'notes',
        name: 'Notes',
        component: () => import('@/pages/Notes.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Settings.vue')
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  if (requiresAuth && !token) {
    return '/login'
  } else if (to.path === '/login' && token) {
    return '/dashboard'
  }
})

export default router