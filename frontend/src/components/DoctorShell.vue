<template>
  <div class="doctor-shell">
    <aside class="doctor-sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon"><i class="bi bi-activity"></i></div>
        <span>Hospital MS</span>
      </div>

      <nav class="sidebar-nav">
        <a :href="`/doctor?doctorId=${doctorId}`" class="nav-link" :class="{ active: active === 'dashboard' }">
          <i class="bi bi-grid"></i>
          <span>Dashboard</span>
        </a>
        <a :href="`/doctor/patients?doctorId=${doctorId}`" class="nav-link" :class="{ active: active === 'history' }">
          <i class="bi bi-file-earmark-text"></i>
          <span>Patient History</span>
        </a>
      </nav>

      <div class="sidebar-bottom">
        <div class="user-pill" @click="$emit('profile')">
          <div class="avatar">{{ initial }}</div>
          <div class="user-pill-info">
            <div class="user-pill-name">{{ doctorName || 'Loading…' }}</div>
            <div class="user-pill-role">Doctor</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" style="width:100%;margin-top:10px;justify-content:center;" type="button" @click="doLogout">
          <i class="bi bi-box-arrow-right"></i> Logout
        </button>
      </div>
    </aside>

    <div class="doctor-main">
      <header class="doctor-topbar">
        <slot name="header-left" />
        <div class="topbar-right">
        </div>
      </header>

      <main class="doctor-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  props: {
    active: {
      type: String,
      required: true,
    },
    doctorId: {
      type: [Number, String],
      default: null,
    },
    doctorName: {
      type: String,
      default: "Doctor",
    },
  },
  emits: ["profile"],
  computed: {
    dashboardRoute() {
      return { path: "/doctor", query: this.doctorId ? { doctorId: String(this.doctorId) } : {} }
    },
    historyRoute() {
      return { path: "/doctor/patients", query: this.doctorId ? { doctorId: String(this.doctorId) } : {} }
    },
    initial() {
      return (this.doctorName || "D").charAt(0).toUpperCase()
    },
  },
  methods: {
    async doLogout() {
      try {
        await api.post("/auth/logout")
      } catch (_) {}
      localStorage.removeItem("token")
      localStorage.removeItem("isLoggedIn")
      localStorage.removeItem("role")
      localStorage.removeItem("name")
      localStorage.removeItem("doctorId")
      window.location.href = "/login"
    },
  },
}
</script>

<style scoped>
.doctor-shell {
  min-height: 100vh;
  background: #f3f4f6;
  color: #111827;
  display: flex;
  font-family: "DM Sans", sans-serif;
}

.doctor-sidebar {
  width: 244px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 0 14px 24px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
  --blue: #2563eb;
  --blue-lt: #eef4ff;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px 28px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 16px;
  height: auto;
  font-family: "Sora", sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  margin-top: 24px;
}

.sidebar-logo .logo-icon {
  width: 34px;
  height: 34px;
  background: var(--blue);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.sidebar-nav {
  padding-top: 18px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: #4b5563;
  font-size: 15px;
  padding: 14px 14px;
  border-radius: 12px;
  margin-bottom: 8px;
}

.nav-link.active,
.nav-link.router-link-active {
  background: #eef4ff;
  color: #2563eb;
  font-weight: 600;
}

.doctor-main {
  min-width: 0;
  flex: 1;
  margin-left: 244px;
}

.doctor-topbar {
  height: 72px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg, #f8fafc);
  border-radius: 12px;
  cursor: pointer;
}
.user-pill:hover {
  background: #f1f5f9;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--blue, #2563eb);
  color: white;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.avatar.sm {
  width: 40px;
  height: 40px;
  font-size: 16px;
}
.user-pill-info {
  flex: 1;
  overflow: hidden;
}
.user-pill-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #111827;
}
.user-pill-role {
  font-size: 11px;
  color: #64748b;
}

.doctor-content {
  padding: 0;
}

@media (max-width: 960px) {
  .doctor-shell {
    flex-direction: column;
  }

  .doctor-sidebar {
    position: static;
    width: 100%;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid #e5e7eb;
  }

  .doctor-main {
    margin-left: 0;
  }

  .doctor-content {
    padding: 16px;
  }
}

.sidebar-bottom {
  margin-top: auto;
  padding: 16px 20px;
  border-top: 1px solid var(--border, #e2e8f0);
}

.btn {
  padding: 8px 18px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s;
}

.btn-ghost {
  background: transparent;
  color: var(--blue, #2563eb);
  border: 1px solid var(--blue, #2563eb);
}

.btn-ghost:hover {
  background: var(--blue-lt, #eff6ff);
}

.btn-sm {
  padding: 5px 12px;
  font-size: 12px;
}
</style>
