import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '@/views/Login.vue'
import RegisterView from '@/views/Register.vue'
import ForgotPasswordView from '@/views/ForgotPassword.vue'
import ResetPasswordView from '@/views/ResetPassword.vue'
import ResetInfoView from '@/views/ResetInfo.vue'

import PatientDashboardView from '@/views/PatientDashboard.vue'
import AdminView from '@/views/admin.vue'
import DoctorDashboardView from '@/views/DoctorDashboard.vue'

import DoctorSetPasswordView from '@/views/DoctorSetPassword.vue'
import DoctorPatientHistoryView from '@/views/DoctorPatientHistory.vue'
import DoctorAppointmentDetailView from '@/views/DoctorAppointmentDetail.vue'


function defaultRouteForRole(role) {
  if (role === 'admin') return '/admin'
  if (role === 'doctor') return '/doctor'
  return '/patient'
}

function canAccess(role, path) {
  if (path.startsWith('/admin')) return role === 'admin'
  if (path.startsWith('/doctor')) return role === 'doctor'
  if (path.startsWith('/patient')) return role === 'patient'
  return true
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },

    { path: '/login', component: LoginView },
    { path: '/register', component: RegisterView },
    { path: '/forgot', component: ForgotPasswordView },
    { path: '/reset/:token', component: ResetPasswordView },

    { path: '/doctor-set-password/:token', component: DoctorSetPasswordView },
    { path: '/reset-info', component: ResetInfoView },
    { path: '/patient', component: PatientDashboardView, meta: { requiresAuth: true } },
    { path: '/doctor', component: DoctorDashboardView, meta: { requiresAuth: true } },
    { path: '/doctor/patients', component: DoctorPatientHistoryView, meta: { requiresAuth: true } },
    { path: '/doctor/appointment/:appointmentRef', component: DoctorAppointmentDetailView, meta: { requiresAuth: true } },
    { path: '/admin', component: AdminView, meta: { requiresAuth: true } },

  ]
})

router.beforeEach((to) => {
  // Allow password-action links even if someone is already logged in.
  if (to.path.startsWith('/doctor-set-password') || to.path.startsWith('/reset/')) {
    return
  }

  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  const role = localStorage.getItem('role') || 'patient'
  const target = defaultRouteForRole(role)
  const publicPaths = ['/login', '/register', '/forgot', '/reset-info']

  if (publicPaths.includes(to.path) && isLoggedIn) {
    return target
  }

  if (to.meta.requiresAuth && !isLoggedIn) {
    return '/login'
  }

  if (to.meta.requiresAuth && !canAccess(role, to.path)) {
    return target
  }

  return true
})

export default router
