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
          <div>
            <h2>Availability Next 7 Days</h2>
            <p class="panel-subtle">Click below to open and update your next 7 days availability.</p>
          </div>
        </div>

        <div class="availability-toggle-wrap">
          <button type="button" class="availability-toggle" @click="availabilityExpanded = !availabilityExpanded">
            <div class="availability-toggle-copy">
              <span class="availability-toggle-title">Doctor Availability</span>
              <span class="availability-toggle-meta">
                {{ availableDaysCount }} open, {{ unavailableDaysCount }} blocked
              </span>
            </div>
            <i class="bi" :class="availabilityExpanded ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
          </button>
        </div>

        <div v-if="availabilityExpanded" class="availability-shell">
          <div class="availability-toolbar">
            <div class="availability-feedback-box" :class="availabilityFeedbackTone">
              <i :class="availabilityFeedbackIcon"></i>
              <span>{{ availabilityFeedbackText }}</span>
            </div>
            <button
              type="button"
              class="availability-save"
              @click="saveAvailability"
              :disabled="savingAvailability || !availabilityDirty"
            >
              {{ savingAvailability ? "Saving..." : availabilityDirty ? "Save Availability" : "Saved" }}
            </button>
          </div>

          <div class="availability-board">
            <article
              v-for="day in next7Days"
              :key="`availability-${day.date}`"
              class="availability-card"
              :class="{ off: !availabilityMap[day.date], today: day.isReference }"
            >
              <div class="availability-top">
                <div>
                  <div class="availability-weekday">{{ day.weekday }}</div>
                  <div class="availability-date">{{ formatDisplayDate(day.date) }}</div>
                </div>
                <span class="availability-badge" :class="availabilityMap[day.date] ? 'ok' : 'no'">
                  {{ availabilityMap[day.date] ? "Available" : "Unavailable" }}
                </span>
              </div>

              <div class="availability-note">
                {{ availabilityMap[day.date] ? "Patients can request appointments." : "New bookings are blocked for this day." }}
              </div>

              <div class="availability-actions">
                <button
                  type="button"
                  class="availability-btn"
                  :class="{ active: availabilityMap[day.date] }"
                  @click="setAvailability(day.date, true)"
                >
                  <i class="bi bi-check2-circle"></i>
                  <span>Available</span>
                </button>
                <button
                  type="button"
                  class="availability-btn danger"
                  :class="{ active: availabilityMap[day.date] === false }"
                  @click="setAvailability(day.date, false)"
                >
                  <i class="bi bi-dash-circle"></i>
                  <span>Unavailable</span>
                </button>
              </div>
            </article>
          </div>
        </div>
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
              :class="{ today: day.isReference }"
            >
              <div class="weekday">{{ day.weekday }}</div>
              <div class="day-number">{{ day.day }}</div>
            </div>
          </div>

          <div v-for="hour in timeSlots" :key="hour" class="schedule-row">
            <div class="time-slot">{{ formatHour(hour) }}</div>
            <div v-for="day in next7Days" :key="`${day.date}-${hour}`" class="calendar-cell">
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
                <td><span class="status-badge">{{ appointment.status }}</span></td>
                <td>
                  <button type="button" class="table-link" @click="openAppointment(appointment)">
                    View Details <i class="bi bi-arrow-right"></i>
                  </button>
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
                <td><span class="status-badge">{{ appointment.status }}</span></td>
                <td>
                  <button type="button" class="table-link" @click="openAppointment(appointment)">
                    View Details <i class="bi bi-arrow-right"></i>
                  </button>
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
      availabilityMap: {},
      savedAvailabilityMap: {},
      referenceDate: "",
      timeSlots: [9, 10, 11, 12, 14, 15, 16, 17],
      availabilityExpanded: false,
      showProfileModal: false,
      savingAvailability: false,
      availabilityFeedback: "",
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
        return {
          date: this.toDateKey(current),
          weekday: current.toLocaleDateString("en-US", { weekday: "short" }),
          day: current.getDate(),
          isReference: index === 0,
        }
      })
    },
    monthLabel() {
      return this.baseDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })
    },
    availableDaysCount() {
      return this.next7Days.filter((day) => this.availabilityMap[day.date] !== false).length
    },
    unavailableDaysCount() {
      return this.next7Days.length - this.availableDaysCount
    },
    availabilityDirty() {
      return this.next7Days.some((day) => {
        const current = this.availabilityMap[day.date] !== false
        const saved = this.savedAvailabilityMap[day.date] !== false
        return current !== saved
      })
    },
    availabilityFeedbackText() {
      if (this.savingAvailability) return "Saving your updated booking window."
      if (this.availabilityFeedback) return this.availabilityFeedback
      if (this.availabilityDirty) return "You have unsaved availability changes."
      return "Your current 7-day availability is saved."
    },
    availabilityFeedbackTone() {
      if (this.savingAvailability) return "info"
      if (this.availabilityFeedback === "Availability updated") return "success"
      if (this.availabilityFeedback === "Save failed") return "error"
      return this.availabilityDirty ? "warning" : "neutral"
    },
    availabilityFeedbackIcon() {
      if (this.savingAvailability) return "bi bi-arrow-repeat"
      if (this.availabilityFeedback === "Availability updated") return "bi bi-check2-circle"
      if (this.availabilityFeedback === "Save failed") return "bi bi-exclamation-octagon"
      return this.availabilityDirty ? "bi bi-dot" : "bi bi-shield-check"
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
    buildAvailabilityMap(entries = []) {
      const map = {}
      this.next7Days.forEach((day) => {
        map[day.date] = true
      })
      entries.forEach((entry) => {
        if (entry?.date) {
          map[entry.date] = Boolean(entry.is_available)
        }
      })
      return map
    },
    setAvailability(date, isAvailable) {
      this.availabilityMap = {
        ...this.availabilityMap,
        [date]: isAvailable,
      }
    },
    async saveAvailability() {
      if (!this.doctorId || !this.availabilityDirty) return
      this.savingAvailability = true
      this.availabilityFeedback = ""
      try {
        const response = await api.post(`/api/doctor/${this.doctorId}/availability`, {
          dates: this.availabilityMap,
        })
        const savedMap = this.buildAvailabilityMap(response.data?.availability || [])
        this.availabilityMap = savedMap
        this.savedAvailabilityMap = { ...savedMap }
        await this.loadDashboard()
        this.availabilityFeedback = "Availability updated"
      } catch (error) {
        this.availabilityFeedback = "Save failed"
        console.error("Failed to save availability:", error)
      } finally {
        this.savingAvailability = false
        window.setTimeout(() => {
          if (!this.savingAvailability) this.availabilityFeedback = ""
        }, 2500)
      }
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
        const availabilityMap = this.buildAvailabilityMap(payload.availability || [])
        this.availabilityMap = availabilityMap
        this.savedAvailabilityMap = { ...availabilityMap }
      } catch (error) {
        console.error("Failed to load doctor dashboard:", error)
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

.panel-subtle {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.availability-shell {
  display: grid;
  gap: 18px;
}

.availability-toggle-wrap {
  margin-bottom: 14px;
}

.availability-toggle {
  width: 100%;
  border: 1px solid #dbe4f0;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.availability-toggle-copy {
  display: grid;
  gap: 6px;
  text-align: left;
}

.availability-toggle-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.availability-toggle-meta {
  font-size: 14px;
  color: #64748b;
}

.availability-toggle i {
  font-size: 20px;
  color: #2563eb;
}

.availability-feedback-box {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
}

.availability-feedback-box.info,
.availability-feedback-box.neutral {
  background: #eff6ff;
  color: #1d4ed8;
}

.availability-feedback-box.success {
  background: #ecfdf3;
  color: #15803d;
}

.availability-feedback-box.warning {
  background: #fff7ed;
  color: #c2410c;
}

.availability-feedback-box.error {
  background: #fef2f2;
  color: #b91c1c;
}

.availability-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.availability-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.availability-card {
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 16px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.availability-card.today {
  border-color: #93c5fd;
  box-shadow: 0 16px 40px rgba(37, 99, 235, 0.12);
}

.availability-card.off {
  background: linear-gradient(180deg, #ffffff, #fff5f5);
  border-color: #fecaca;
}

.availability-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
}

.availability-weekday {
  font-size: 13px;
  color: #6b7280;
}

.availability-date {
  margin-top: 4px;
  font-weight: 700;
  font-size: 16px;
}

.availability-badge {
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
}

.availability-badge.ok {
  background: #dcfce7;
  color: #166534;
}

.availability-badge.no {
  background: #fee2e2;
  color: #b91c1c;
}

.availability-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 14px;
}

.availability-note {
  margin-top: 14px;
  color: #475569;
  font-size: 13px;
  line-height: 1.5;
}

.availability-btn,
.availability-save {
  border: 1px solid transparent;
  border-radius: 14px;
  font-weight: 700;
}

.availability-btn {
  padding: 12px 14px;
  background: #f8fafc;
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: 0.2s ease;
}

.availability-btn.active {
  background: #eef4ff;
  color: #2563eb;
  border-color: #bfd3ff;
}

.availability-btn.danger.active {
  background: #fff1f2;
  color: #be123c;
  border-color: #fecdd3;
}

.availability-save {
  width: 100%;
  margin-top: 18px;
  padding: 14px 16px;
  background: #2563eb;
  color: #ffffff;
}

.availability-save:disabled {
  opacity: 0.65;
  cursor: not-allowed;
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

  .availability-board {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .availability-board {
    grid-template-columns: 1fr;
  }

  .availability-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
