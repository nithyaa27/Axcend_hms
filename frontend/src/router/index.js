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
import SettingsView from '@/views/Settings.vue'

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
    { path: '/settings', component: SettingsView, meta: { requiresAuth: true } },
  ]
})

router.beforeEach((to) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  const role = localStorage.getItem('role') || 'patient'
  const target = defaultRouteForRole(role)
  const publicPaths = ['/login', '/register', '/forgot', '/reset-info', '/reset', '/doctor-set-password']

  // If already logged in, only redirect away from public pages if they are NOT reset pages.
  // We want to allow people to reach reset pages even if they have an old session.
  if (isLoggedIn && publicPaths.some(p => to.path.startsWith(p))) {
    // Only redirect to dashboard if it's strictly a login/register type page, 
    // NOT a reset page.
    if (!to.path.startsWith('/reset/') && !to.path.startsWith('/doctor-set-password')) {
    return target
    }
    return true
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
