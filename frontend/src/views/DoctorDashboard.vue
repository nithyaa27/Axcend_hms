<template>
  <DoctorShell
    active="dashboard"
    :doctor-id="doctorId"
    :doctor-name="doctorDisplayName"
    @profile="showProfileModal = true"
  >
    <template #header-left />

    <div v-if="!doctorId" class="id-banner">
      <div class="id-title">Access denied</div>
      <div>Please login as a doctor to view this dashboard.</div>
    </div>

    <section v-else class="dashboard-page">
      <header class="hero">
        <h1>Doctor Dashboard</h1>
        <p>Welcome back, {{ doctorDisplayName }}</p>
      </header>

      <section class="panel availability-section">
        <div class="panel-head">
          <div class="title-with-icon">
            <i class="bi bi-calendar2-check"></i>
            <h2>Manage Availability</h2>
          </div>
        </div>
        <div class="availability-info">
          <p>Manage your day-wise availability below in your 7-day schedule.</p>
        </div>
      </section>

      <section class="stats-grid">
        <article class="stat-card">
          <div>
            <div class="stat-label">Today's Appointments</div>
            <div class="stat-value">{{ todayAppointments.length }}</div>
          </div>
          <div class="stat-icon blue">
            <i class="bi bi-calendar-week"></i>
          </div>
        </article>
        <article class="stat-card">
          <div>
            <div class="stat-label">Upcoming</div>
            <div class="stat-value">{{ upcomingAppointments.length }}</div>
          </div>
          <div class="stat-icon violet">
            <i class="bi bi-clock-history"></i>
          </div>
        </article>
        <article class="stat-card">
          <div>
            <div class="stat-label">Total Patients</div>
            <div class="stat-value">{{ stats.total_patients || 0 }}</div>
          </div>
          <div class="stat-icon green">
            <i class="bi bi-person"></i>
          </div>
        </article>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Next 7 Days Schedule</h2>
          <div class="month-pill">
            <i class="bi bi-calendar3"></i>
            <span>{{ monthLabel }}</span>
          </div>
        </div>

        <div class="schedule-grid">
          <div class="schedule-header">
            <div class="time-head">Time</div>
            <div
              v-for="day in next7Days"
              :key="day.date"
              class="day-head"
              :class="{ today: day.isReference, 'day-off': !day.isAvailable }"
            >
              <div class="weekday">{{ day.weekday }}</div>
              <div class="day-number">{{ day.day }}</div>
              <button 
                type="button" 
                class="btn-day-toggle" 
                :class="day.isAvailable ? 'on' : 'off'"
                @click="toggleDayAvailability(day)"
              >
                {{ day.isAvailable ? 'Available' : 'Day Off' }}
              </button>
            </div>
          </div>

          <div v-for="hour in timeSlots" :key="hour" class="schedule-row">
            <div class="time-slot">{{ formatHour(hour) }}</div>
            <div v-for="day in next7Days" :key="`${day.date}-${hour}`" class="calendar-cell" :class="{ 'cell-off': !day.isAvailable }">
              <template v-if="day.isAvailable">
                <button
                  v-for="appointment in getAppointments(day.date, hour)"
                  :key="appointment.id"
                  type="button"
                  class="appt-card"
                  :class="{ completed: appointment.status === 'completed' }"
                  @click="openAppointment(appointment)"
                >
                  <div class="appt-name">{{ truncateName(appointment.patient_name) }}</div>
                  <div class="appt-time">{{ appointment.time }}</div>
                </button>
              </template>
              <div v-else class="off-label">OFF</div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel">
        <h2>Today's Appointments</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Patient</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!todayAppointments.length">
                <td colspan="4" class="empty-cell">No appointments scheduled.</td>
              </tr>
              <tr v-for="appointment in todayAppointments" :key="appointment.id">
                <td>{{ appointment.time }}</td>
                <td>{{ appointment.patient_name }}</td>
                <td><span class="status-badge" :class="appointment.status">{{ appointment.status }}</span></td>
                <td>
                  <div class="action-btns">
                    <button v-if="appointment.status === 'booked'" type="button" class="btn-visited" @click="markVisited(appointment)">
                      <i class="bi bi-person-check"></i>
                    </button>
                    <button type="button" class="table-link" @click="openAppointment(appointment)">
                      View Details <i class="bi bi-arrow-right"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <h2>Upcoming Appointments</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Patient</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!upcomingAppointments.length">
                <td colspan="5" class="empty-cell">No upcoming appointments found.</td>
              </tr>
              <tr v-for="appointment in upcomingAppointments" :key="appointment.id">
                <td>{{ formatDisplayDate(appointment.date) }}</td>
                <td>{{ appointment.time }}</td>
                <td>{{ appointment.patient_name }}</td>
                <td><span class="status-badge" :class="appointment.status">{{ appointment.status }}</span></td>
                <td>
                  <div class="action-btns">
                    <button v-if="appointment.status === 'booked'" type="button" class="btn-visited" @click="markVisited(appointment)">
                      <i class="bi bi-person-check"></i>
                    </button>
                    <button type="button" class="table-link" @click="openAppointment(appointment)">
                      View Details <i class="bi bi-arrow-right"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>

    <div v-if="showProfileModal" class="modal-overlay" @click.self="showProfileModal = false">
      <div class="profile-modal">
        <button type="button" class="close-btn" @click="showProfileModal = false">
          <i class="bi bi-x-lg"></i>
        </button>
        <div class="profile-avatar">{{ doctorInitial }}</div>
        <h3>{{ doctorDisplayName }}</h3>
        <p>Doctor ID: {{ doctorId || "N/A" }}</p>
        <div class="profile-grid">
          <div class="profile-box">
            <span>Email</span>
            <strong>{{ doctorProfile.email || "N/A" }}</strong>
          </div>
          <div class="profile-box">
            <span>Specialization</span>
            <strong>{{ doctorProfile.specialization || "N/A" }}</strong>
          </div>
        </div>
      </div>
    </div>
  </DoctorShell>
</template>

<script>

/**
 * DoctorDashboard View
 * -------------------
 * The primary interface for medical practitioners.
 * Features:
 * - Weekly appointment schedule (grid view).
 * - Real-time statistics for daily and upcoming consultations.
 * - Quick access to patient details and treatment recording.
 * - Profile management for the logged-in doctor.
 */
 
import DoctorShell from "@/components/DoctorShell.vue"
import api from "@/services/interceptor"

export default {
  components: { DoctorShell },
  data() {
    return {
      doctorProfile: {
        name: localStorage.getItem("name") || "Doctor",
        email: "",
        specialization: "",
      },
      stats: {},
      schedule: [],
      referenceDate: "",
      timeSlots: [9, 10, 11, 12, 14, 15, 16, 17],
      showProfileModal: false,
      availabilities: [],
    }
  },
  computed: {
    doctorId() {
      const queryId = Number(this.$route.query.doctorId)
      if (Number.isInteger(queryId) && queryId > 0) return queryId

      const direct = Number(localStorage.getItem("doctorId"))
      if (Number.isInteger(direct) && direct > 0) return direct

      const tokenDoctorId = this.getDoctorIdFromToken()
      if (Number.isInteger(tokenDoctorId) && tokenDoctorId > 0) return tokenDoctorId

      return null
    },
    doctorDisplayName() {
      return this.doctorProfile?.name || localStorage.getItem("name") || "Doctor"
    },
    doctorInitial() {
      return (this.doctorDisplayName || "D").charAt(0).toUpperCase()
    },
    baseDate() {
      return this.referenceDate ? new Date(`${this.referenceDate}T00:00:00`) : new Date()
    },
    next7Days() {
      return Array.from({ length: 7 }, (_, index) => {
        const current = new Date(this.baseDate)
        current.setDate(this.baseDate.getDate() + index)
        const dateKey = this.toDateKey(current)
        const av = this.availabilities.find(a => a.date === dateKey)
        return {
          date: dateKey,
          weekday: current.toLocaleDateString("en-US", { weekday: "short" }),
          day: current.getDate(),
          isReference: index === 0,
          isAvailable: av ? av.is_available : true
        }
      })
    },
    monthLabel() {
      return this.baseDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })
    },
    todayAppointments() {
      return this.schedule
        .filter((appointment) => appointment.date === this.referenceDate && appointment.status === "booked")
        .sort((left, right) => new Date(left.datetime) - new Date(right.datetime))
    },
    upcomingAppointments() {
      return this.schedule
        .filter((appointment) => appointment.status === "booked" && appointment.date > this.referenceDate)
        .sort((left, right) => new Date(left.datetime) - new Date(right.datetime))
    },
  },
  watch: {
    "$route.query.doctorId": {
      immediate: true,
      handler() {
        this.loadDashboard()
      },
    },
  },
  methods: {
    getDoctorIdFromToken() {
      const token = localStorage.getItem("token")
      if (!token) return null
      try {
        const payloadPart = token.split(".")[1]
        const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/")
        const payloadJson = decodeURIComponent(
          atob(normalized)
            .split("")
            .map((char) => "%" + ("00" + char.charCodeAt(0).toString(16)).slice(-2))
            .join("")
        )
        const payload = JSON.parse(payloadJson)
        const claimDoctorId = Number(payload.user_id)
        if (Number.isInteger(claimDoctorId) && claimDoctorId > 0) return claimDoctorId
        const subId = Number(payload.sub)
        return Number.isInteger(subId) ? subId : null
      } catch (_) {
        return null
      }
    },
    toDateKey(input) {
      const date = input instanceof Date ? input : new Date(input)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, "0")
      const day = String(date.getDate()).padStart(2, "0")
      return `${year}-${month}-${day}`
    },
    formatHour(hour) {
      const suffix = hour >= 12 ? "PM" : "AM"
      const normalized = hour % 12 || 12
      return `${normalized}:00 ${suffix}`
    },
    truncateName(name) {
      return name.length > 14 ? `${name.slice(0, 11)}...` : name
    },
    formatDisplayDate(value) {
      const [year, month, day] = value.split("-")
      return `${Number(day)}/${Number(month)}/${year}`
    },
    getAppointments(date, hour) {
      return this.schedule.filter((appointment) => {
        const appointmentDate = new Date(appointment.datetime)
        return appointment.date === date && appointmentDate.getHours() === hour
      })
    },
    openAppointment(appointment) {
      this.$router.push({
        path: `/doctor/appointment/${appointment.reference}`,
        query: this.doctorId ? { doctorId: String(this.doctorId) } : {},
      })
    },
    async loadDashboard() {
      if (!this.doctorId) {
        this.schedule = []
        this.stats = {}
        this.referenceDate = ""
        return
      }

      try {
        const response = await api.get(`/api/doctor/${this.doctorId}/dashboard`)
        const payload = response.data || {}
        this.doctorProfile = payload.doctor || this.doctorProfile
        this.stats = payload.stats || {}
        this.schedule = payload.schedule || []
        this.referenceDate = payload.reference_date || this.toDateKey(new Date())
        this.availabilities = payload.availability || []

      } catch (error) {
        console.error("Failed to load doctor dashboard:", error)
      }
    },
    async toggleDayAvailability(day) {
      if (!this.doctorId) return
      const newVal = !day.isAvailable
      try {
        await api.post(`/api/doctor/${this.doctorId}/availability`, {
          dates: { [day.date]: newVal }
        })
        const existing = this.availabilities.find(a => a.date === day.date)
        if (existing) {
          existing.is_available = newVal
        } else {
          this.availabilities.push({ date: day.date, is_available: newVal })
        }
      } catch (err) {
        console.error("Failed to update availability:", err)
      }
    },
    async markVisited(appointment) {
      try {
        await api.patch(`/api/doctor/${this.doctorId}/appointments/${appointment.id}/status`, {
          status: 'visited'
        })
        appointment.status = 'visited'
      } catch (err) {
        console.error("Failed to mark visited:", err)
      }
    },
  },
}
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 24px;
  padding: 26px 22px 26px;
}

.hero h1 {
  margin: 0;
  font-family: "Sora", sans-serif;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.hero p {
  margin: 8px 0 0;
  font-size: 16px;
  color: #6b7280;
}

.availability-section {
  border-left: 4px solid var(--blue);
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-with-icon i {
  font-size: 20px;
  color: var(--blue);
}

.availability-info {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.5;
  margin-top: -6px;
}


.toggle-switch:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
}

.stat-card,
.panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
}

.stat-card {
  padding: 22px 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 132px;
  border-radius: 18px;
}

.stat-label {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.25;
}

.stat-value {
  font-size: 40px;
  line-height: 1;
  font-weight: 700;
  margin-top: 12px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 28px;
  color: #ffffff;
}

.stat-icon.blue { background: linear-gradient(135deg, #60a5fa, #2563eb); }
.stat-icon.violet { background: linear-gradient(135deg, #d946ef, #8b5cf6); }
.stat-icon.green { background: linear-gradient(135deg, #22c55e, #16a34a); }

.panel {
  padding: 20px 22px 18px;
  border-radius: 18px;
}

.panel h2 {
  margin: 0 0 18px;
  font-size: 17px;
  font-weight: 700;
}

.panel + .panel {
  margin-top: 2px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.month-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #4b5563;
  font-size: 14px;
  font-weight: 600;
}

.schedule-grid {
  overflow-x: auto;
  padding-top: 2px;
}

.schedule-header,
.schedule-row {
  display: grid;
  grid-template-columns: 120px repeat(7, minmax(110px, 1fr));
  gap: 8px;
}

.schedule-header {
  margin-bottom: 8px;
}

.schedule-row {
  margin-bottom: 2px;
}

.schedule-row:last-child {
  margin-bottom: 0;
}

.time-head,
.time-slot {
  padding: 16px 8px 10px;
  font-size: 14px;
  color: #4b5563;
}

.day-head {
  text-align: center;
  color: #6b7280;
  padding: 8px 8px 10px;
}

.day-head.today {
  background: #eef4ff;
  border: 1px solid #bfd3ff;
  border-radius: 14px;
}

.weekday {
  font-size: 13px;
}

.day-number {
  margin-top: 4px;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.btn-day-toggle {
  margin-top: 8px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-day-toggle.on { color: #16a34a; border-color: #bbf7d0; background: #f0fdf4; }
.btn-day-toggle.off { color: #dc2626; border-color: #fecaca; background: #fef2f2; }

.day-head.day-off {
  background: #f9fafb;
  opacity: 0.8;
}

.calendar-cell.cell-off {
  background: #f3f4f6;
  border-color: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.off-label {
  font-size: 12px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 0.05em;
}

.calendar-cell {
  min-height: 82px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f7f8fa;
  padding: 4px;
}

.appt-card {
  width: 100%;
  border: 0;
  border-radius: 7px;
  background: linear-gradient(180deg, #3b82f6, #2563eb);
  color: #ffffff;
  text-align: left;
  padding: 9px 10px 8px;
  min-height: 100%;
}

.appt-card.completed {
  background: linear-gradient(180deg, #34d399, #16a34a);
}

.appt-name {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
}

.appt-time {
  margin-top: 6px;
  font-size: 12px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

tbody tr:last-child td {
  border-bottom: 0;
}

th,
td {
  text-align: left;
  padding: 14px 10px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

th {
  color: #374151;
  font-weight: 700;
  padding-top: 10px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #e8f0ff;
  color: #2563eb;
  padding: 4px 12px;
  font-size: 13px;
  text-transform: lowercase;
}
.status-badge.completed { background: #dcfce7; color: #16a34a; }
.status-badge.visited { background: #e0f2fe; color: #0369a1; }
.status-badge.cancelled { background: #fee2e2; color: #dc2626; }
.status-badge.not_attended { background: #fef3c7; color: #d97706; }
.status-badge.not_visited { background: #ffedd5; color: #ea580c; }
.status-badge.not_visited_cancelled { background: #f3f4f6; color: #4b5563; }

.action-btns {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-visited {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  color: #0369a1;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-visited:hover {
  background: #e0f2fe;
}

.table-link {
  border: 0;
  background: transparent;
  color: #111827;
  font-weight: 700;
  font-size: 14px;
}

.table-link i {
  margin-left: 8px;
}

.empty-cell {
  text-align: center;
  color: #6b7280;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.4);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 20;
}

.profile-modal {
  width: min(520px, 92vw);
  background: #ffffff;
  border-radius: 22px;
  padding: 24px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  border: 0;
  background: transparent;
  color: #6b7280;
}

.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #2563eb;
  color: #ffffff;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.profile-modal h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.profile-modal p {
  margin: 6px 0 18px;
  color: #6b7280;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.profile-box {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 16px;
}

.profile-box span {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.id-banner {
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 12px;
  padding: 14px;
}

.id-title {
  font-weight: 700;
  margin-bottom: 6px;
  color: #9a3412;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .hero h1 {
    font-size: 28px;
  }

  .hero p {
    font-size: 16px;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
