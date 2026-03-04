import { createRouter, createWebHistory } from "vue-router";
import Login from "./views/Login.vue";
import Register from "./views/Register.vue";
import ForgotPassword from "./views/ForgotPassword.vue";
import ResetPassword from "./views/ResetPassword.vue";
import AdminDashboard from "./views/AdminDashboard.vue";
import DoctorDashboard from "./views/DoctorDashboard.vue";
import PatientDashboard from "./views/PatientDashboard.vue";
import ResetPasswordInfo from "./views/ResetPasswordInfo.vue";

const routes = [
  { path: "/", component: Login , meta: { showNavbar: false }},
  { path: "/register", component: Register ,meta: { showNavbar: false }},
  { path: "/forgot", component: ForgotPassword, meta: { showNavbar: false } },
  { path: "/reset/:token", component: ResetPassword , meta: { showNavbar: false }},
  { path: "/admin", component: AdminDashboard, meta: { requiresAuth: true, showNavbar: true }},
  { path: "/doctor", component: DoctorDashboard, meta: { requiresAuth: true, showNavbar: true }},
  { path: "/patient", component: PatientDashboard, meta: { requiresAuth: true, showNavbar: true } },
  { path: "/reset-info", component: ResetPasswordInfo, meta: { showNavbar: false } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");

  if (to.meta.requiresAuth && !token) {
    next("/");
  } else {
    next();
  }
});

export default router;
