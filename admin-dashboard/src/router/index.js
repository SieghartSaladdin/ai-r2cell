import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import KnowledgeBaseView from '../views/KnowledgeBaseView.vue'
import ConversationsView from '../views/ConversationsView.vue'
import GraphView from '../views/GraphView.vue'
import GatewayView from '../views/GatewayView.vue'
import ProductsView from '../views/ProductsView.vue'
import BookingsView from '../views/BookingsView.vue'

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
        },
        {
          path: 'graph',
          name: 'graph',
          component: GraphView
        },
        {
          path: 'gateway',
          name: 'gateway',
          component: GatewayView
        },
        {
          path: 'products',
          name: 'products',
          component: ProductsView
        },
        {
          path: 'bookings',
          name: 'bookings',
          component: BookingsView
        }
      ]
    }
  ]
})

export default router
