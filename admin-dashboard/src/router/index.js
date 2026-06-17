import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import KnowledgeBaseView from '../views/KnowledgeBaseView.vue'
import ConversationsView from '../views/ConversationsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DashboardLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: KnowledgeBaseView
        },
        {
          path: 'conversations',
          name: 'conversations',
          component: ConversationsView
        }
      ]
    }
  ]
})

export default router
