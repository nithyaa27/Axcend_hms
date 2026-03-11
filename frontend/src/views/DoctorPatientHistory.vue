<template>
  <DoctorShell
    active="history"
    :doctor-id="doctorId"
    :doctor-name="doctorDisplayName"
    @profile="showProfileModal = true"
  >
    <template #header-left>
      <div class="search-head">
        <i class="bi bi-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by patient name or ID..."
        />
      </div>
    </template>

    <div v-if="!doctorId" class="id-banner">
      <div class="id-title">Access denied</div>
      <div>Please login as a doctor to view patient history.</div>
    </div>

    <section v-else class="history-page">
      <header class="page-meta">
        <h1>Patient History</h1>
        <p>Manage and review all past patient records</p>
      </header>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
      </div>

      <div v-else-if="!filteredGroups.length" class="empty-state">
        <div class="empty-icon"><i class="bi bi-folder-x"></i></div>
        <h3>No records found</h3>
        <p>Try searching for a different patient name or ID.</p>
      </div>

      <div v-else class="groups-list">
        <section
          v-for="group in filteredGroups"
          :key="group.patient_name"
          class="patient-group"
        >
          <div class="group-header">
            <div class="patient-avatar">{{ group.patient_name.charAt(0).toUpperCase() }}</div>
            <div>
              <h3>{{ group.patient_name }}</h3>
              <span class="record-count">{{ group.records.length }} past record(s)</span>
            </div>
          </div>

          <div class="records-grid">
            <article
              v-for="record in group.records"
              :key="record.appointment_id"
              class="record-card"
              @click="openRecord(record)"
            >
              <div class="record-main">
                <div class="record-date">
                  <i class="bi bi-calendar3"></i>
                  <span>{{ formatDate(record.datetime) }}</span>
                </div>
                <div class="record-time">
                  <i class="bi bi-clock"></i>
                  <span>{{ formatTime(record.datetime) }}</span>
                </div>
              </div>
              <div class="record-info">
                <strong>{{ record.diagnosis }}</strong>
                <p>{{ truncatePrescription(record.prescription) }}</p>
              </div>
              <div class="record-action">
                <span>View Record</span>
                <i class="bi bi-chevron-right"></i>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>

    <!-- Treatment Detail Modal -->
    <div v-if="selectedRecord" class="modal-overlay" @click.self="selectedRecord = null">
      <div class="record-modal">
        <header class="modal-header">
          <div>
            <h3>Treatment Record</h3>
            <span>{{ selectedRecord.patient_name }} | {{ formatDate(selectedRecord.datetime) }}</span>
          </div>
          <button type="button" @click="selectedRecord = null"><i class="bi bi-x-lg"></i></button>
        </header>

        <div class="modal-body">
          <section class="info-block">
            <label>Diagnosis</label>
            <div class="info-val">{{ selectedRecord.diagnosis }}</div>
          </section>

          <section class="info-block">
            <label>Prescription</label>
            <div class="info-val pre-wrap">{{ selectedRecord.prescription }}</div>
          </section>

          <section v-if="selectedRecord.notes" class="info-block">
            <label>Doctor Notes</label>
            <div class="info-val">{{ selectedRecord.notes }}</div>
          </section>

          <section v-if="selectedRecord.follow_up_date" class="info-block">
            <label>Follow-up Date</label>
            <div class="info-val">{{ formatDisplayDate(selectedRecord.follow_up_date) }}</div>
          </section>
        </div>
      </div>
    </div>

    <!-- Doctor Profile Modal -->
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
      groups: [],
      searchQuery: "",
      loading: true,
      selectedRecord: null,
      showProfileModal: false,
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
    filteredGroups() {
      if (!this.searchQuery.trim()) return this.groups
      const query = this.searchQuery.toLowerCase()
      return this.groups.filter((group) => group.patient_name.toLowerCase().includes(query))
    },
  },
  watch: {
    "$route.fullPath": {
      immediate: true,
      handler() {
        this.loadHistory()
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
    formatDate(text) {
      if (!text) return ""
      const d = new Date(text)
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    },
    formatTime(text) {
      if (!text) return ""
      const d = new Date(text)
      return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    },
    formatDisplayDate(value) {
      if (!value) return ""
      const [year, month, day] = value.split("-")
      return `${Number(day)}/${Number(month)}/${year}`
    },
    truncatePrescription(text) {
      if (!text) return "No prescription"
      return text.length > 80 ? `${text.slice(0, 77)}...` : text
    },
    openRecord(record) {
      this.selectedRecord = record
    },
    async loadHistory() {
      if (!this.doctorId) {
        this.groups = []
        this.loading = false
        return
      }
      this.loading = true
      try {
        const response = await api.get(`/api/doctor/${this.doctorId}/completed-appointments`)
        const data = response.data || {}
        const rawItems = data.completed_appointments || []

        const byPatient = {}
        rawItems.forEach((item) => {
          const name = item.patient_name
          if (!byPatient[name]) byPatient[name] = []
          byPatient[name].push(item)
        })

        const sortedGroups = Object.keys(byPatient)
          .sort()
          .map((name) => ({
            patient_name: name,
            records: byPatient[name],
          }))

        this.groups = sortedGroups
      } catch (error) {
        console.error("Failed to load completed appointments:", error)
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.history-page {
  padding: 26px 22px 40px;
}

.search-head {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f3f4f6;
  border-radius: 12px;
  padding: 0 16px;
  width: 320px;
  height: 42px;
}

.search-head i {
  color: #9ca3af;
  font-size: 16px;
}

.search-head input {
  border: 0;
  background: transparent;
  flex: 1;
  font-size: 14px;
  outline: none;
}

.page-meta h1 {
  margin: 0;
  font-family: "Sora", sans-serif;
  font-size: 28px;
  font-weight: 700;
}

.page-meta p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 15px;
}

.loading-state {
  min-height: 300px;
  display: grid;
  place-items: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 12px;
}

.empty-state h3 {
  margin: 0;
  font-size: 20px;
}

.empty-state p {
  color: #6b7280;
  margin-top: 8px;
}

.groups-list {
  margin-top: 30px;
  display: grid;
  gap: 32px;
}

.patient-group {
  display: grid;
  gap: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.patient-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #eef4ff;
  color: #2563eb;
  font-weight: 700;
  font-size: 18px;
}

.group-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.record-count {
  font-size: 13px;
  color: #6b7280;
}

.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 18px;
}

.record-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 18px 20px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}

.record-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}

.record-main {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 14px;
}

.record-date,
.record-time {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.record-date i,
.record-time i {
  color: #9ca3af;
}

.record-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 6px;
}

.record-info p {
  margin: 0;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
}

.record-action {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
}

.record-modal {
  width: min(600px, 92vw);
  background: #ffffff;
  border-radius: 20px;
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.modal-header span {
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
  display: block;
}

.modal-header button {
  border: 0;
  background: transparent;
  color: #6b7280;
  font-size: 18px;
}

.modal-body {
  padding: 24px;
  display: grid;
  gap: 20px;
}

.info-block label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: #9ca3af;
  margin-bottom: 8px;
  letter-spacing: 0.05em;
}

.info-val {
  font-size: 15px;
  line-height: 1.6;
}

.pre-wrap {
  white-space: pre-wrap;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 100;
}

.profile-modal {
  width: min(420px, 92vw);
  background: #ffffff;
  border-radius: 18px;
  padding: 22px;
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
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #2563eb;
  color: #ffffff;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 12px;
}

.profile-modal h3 {
  margin: 0;
  font-size: 22px;
}

.profile-modal p {
  color: #6b7280;
  margin-bottom: 20px;
}

.profile-grid {
  display: grid;
  gap: 12px;
}

.profile-box {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
}

.profile-box span {
  display: block;
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 4px;
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

@media (max-width: 640px) {
  .records-grid {
    grid-template-columns: 1fr;
  }
  .search-head {
    width: 200px;
  }
}
</style>
