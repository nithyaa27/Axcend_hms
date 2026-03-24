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
      <div>Please login as a doctor to view appointment details.</div>
    </div>

    <section v-else class="detail-page">
      <div class="page-header">
        <a :href="`/doctor?doctorId=${doctorId}`" class="back-link">
          <i class="bi bi-arrow-left"></i>
          <span>Back to Dashboard</span>
        </a>
        <p class="page-intro">View and manage appointment information</p>
      </div>

      <section class="detail-grid" v-if="appointment && patient">
        <article class="info-card">
          <h2>Patient Information</h2>
          <div class="patient-avatar">{{ patient.name.charAt(0).toUpperCase() }}</div>
          <div class="patient-name">{{ patient.name }}</div>
          <div class="patient-id">Patient ID: {{ patient.patient_uid }}</div>

          <div class="info-list">
            <div class="info-row">
              <i class="bi bi-envelope"></i>
              <div>
                <span>Email</span>
                <strong>{{ patient.email || "N/A" }}</strong>
              </div>
            </div>
            <div class="info-row">
              <i class="bi bi-telephone"></i>
              <div>
                <span>Phone</span>
                <strong>{{ patient.phone || "N/A" }}</strong>
              </div>
            </div>
          </div>
        </article>

        <article class="info-card">
          <h2>Appointment Information</h2>
          <div class="info-list appointment-list">
            <div class="info-row">
              <i class="bi bi-calendar3"></i>
              <div>
                <span>Date</span>
                <strong>{{ appointmentDateLong }}</strong>
              </div>
            </div>
            <div class="info-row">
              <i class="bi bi-clock"></i>
              <div>
                <span>Time</span>
                <strong>{{ appointment.time }}</strong>
              </div>
            </div>
            <div class="info-row">
              <i class="bi bi-person"></i>
              <div>
                <span>Doctor</span>
                <strong>{{ doctorDisplayName }}</strong>
              </div>
            </div>
            <div class="info-row status-row">
              <div class="status-display">
                <span>Status</span>
                <span class="status-badge" :class="appointment.status">{{ appointment.status }}</span>
              </div>
              <button
                v-if="appointment.can_mark_attending"
                type="button"
                class="attending-btn"
                @click="markAsAttending"
              >
                <i class="bi bi-person-check"></i>
                Mark as Attending
              </button>
            </div>
          </div>
        </article>
      </section>

      <section class="treatment-card">
        <div class="treatment-head">
          <h2>Treatment Information</h2>
          <button
            v-if="!showForm"
            type="button"
            class="primary-btn"
            :class="{ 'disabled-style': appointment.status === 'booked' }"
            :disabled="appointment.status === 'booked'"
            @click="openTreatmentForm"
          >
            {{ (treatment || appointment.can_edit_treatment) ? "Edit Treatment" : "Add Treatment" }}
          </button>
        </div>

        <div v-if="showForm" class="treatment-form">
          <label>Diagnosis</label>
          <textarea v-model="form.diagnosis" placeholder="Enter diagnosis..."></textarea>

          <label>Prescription</label>
          <textarea v-model="form.prescription" placeholder="Enter prescription details..."></textarea>

          <label>Doctor Notes</label>
          <textarea v-model="form.notes" placeholder="Add any additional notes..."></textarea>

          <label>Follow-up Date</label>
          <input v-model="form.follow_up_date" type="date" />

          <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

          <div class="form-actions">
            <button type="button" class="complete-btn" :disabled="saving" @click="saveTreatment">
              <i class="bi bi-check-circle"></i>
              <span>{{ saving ? "Saving..." : "Mark as Completed" }}</span>
            </button>
          </div>
        </div>

        <div v-else-if="treatment" class="treatment-summary">
          <div class="summary-block">
            <span>Diagnosis</span>
            <strong>{{ treatment.diagnosis }}</strong>
          </div>
          <div class="summary-block">
            <span>Prescription</span>
            <strong>{{ treatment.prescription }}</strong>
          </div>
          <div class="summary-block">
            <span>Doctor Notes</span>
            <strong>{{ treatment.notes || "No notes added" }}</strong>
          </div>
        </div>

        <div v-else class="empty-treatment">
          No treatment information added yet
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
      appointment: null,
      patient: null,
      treatment: null,
      showForm: false,
      showProfileModal: false,
      saving: false,
      errorMessage: "",
      form: {
        diagnosis: "",
        prescription: "",
        notes: "",
        follow_up_date: "",
      },
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
    appointmentId() {
      const value = String(this.$route.params.appointmentRef || "")
      return Number(value.replace("apt-", ""))
    },
    doctorDisplayName() {
      return this.doctorProfile?.name || localStorage.getItem("name") || "Doctor"
    },
    doctorInitial() {
      return (this.doctorDisplayName || "D").charAt(0).toUpperCase()
    },
    appointmentDateLong() {
      if (!this.appointment) return ""
      return new Date(this.appointment.datetime).toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      })
    },
  },
  watch: {
    "$route.fullPath": {
      immediate: true,
      handler() {
        this.loadAppointment()
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
    openTreatmentForm() {
      this.showForm = true
      this.errorMessage = ""
      this.form = {
        diagnosis: this.treatment?.diagnosis || "",
        prescription: this.treatment?.prescription || "",
        notes: this.treatment?.notes || "",
        follow_up_date: this.treatment?.follow_up_date || "",
      }
    },
    async loadAppointment() {
      if (!this.doctorId || !this.appointmentId) return
      try {
        const response = await api.get(`/api/doctor/${this.doctorId}/appointments/${this.appointmentId}`)
        const payload = response.data || {}
        this.doctorProfile = payload.doctor || this.doctorProfile
        this.appointment = payload.appointment || null
        this.patient = payload.patient || null
        this.treatment = payload.treatment || null
        this.showForm = false
      } catch (error) {
        console.error("Failed to load appointment details:", error)
      }
    },
    async saveTreatment() {
      if (!this.doctorId || !this.appointmentId) return
      if (!this.form.diagnosis.trim() || !this.form.prescription.trim()) {
        this.errorMessage = "Diagnosis and prescription are required."
        return
      }

      this.saving = true
      try {
        await api.post(`/api/doctor/${this.doctorId}/appointments/${this.appointmentId}/treatment`, this.form)
        await this.loadAppointment()
      } catch (error) {
        this.errorMessage = error.response?.data?.error || "Failed to save treatment."
      } finally {
        this.saving = false
      }
    },
    async markAsAttending() {
      if (!this.doctorId || !this.appointmentId) return
      try {
        await api.patch(`/api/doctor/${this.doctorId}/appointments/${this.appointmentId}/status`, {
          status: 'attending'
        })
        await this.loadAppointment()
      } catch (error) {
        console.error("Failed to mark as attending:", error)
        alert(error.response?.data?.error || "Failed to update status to attending")
      }
    },
  },
}
</script>

<style scoped>
.detail-page {
  display: grid;
  gap: 22px;
  padding: 2px 22px 26px;
}

.page-header {
  margin-bottom: 8px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 0;
  padding: 0;
  color: #2563eb;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  margin-bottom: 12px;
  transition: opacity 0.2s;
}

.back-link:hover {
  opacity: 0.8;
}

.page-intro {
  margin: 0;
  color: #4b5563;
  font-size: 15px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.info-card,
.treatment-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
}

.info-card {
  padding: 18px 22px 20px;
}

.info-card h2,
.treatment-card h2 {
  margin: 0 0 18px;
  font-size: 18px;
  font-weight: 700;
}

.patient-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #2563eb;
  color: #ffffff;
  font-size: 34px;
  font-weight: 700;
  margin: 0 auto 12px;
}

.patient-name,
.patient-id {
  text-align: center;
}

.patient-name {
  font-size: 20px;
  font-weight: 700;
}

.patient-id {
  margin-top: 4px;
  color: #6b7280;
  font-size: 14px;
}

.info-card:first-child .info-list {
  border-top: 1px solid #e5e7eb;
  padding-top: 18px;
}

.info-list {
  display: grid;
  gap: 16px;
  margin-top: 24px;
}

.appointment-list {
  margin-top: 0;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.info-row i {
  font-size: 22px;
  color: #9ca3af;
}

.info-row span {
  display: block;
  color: #6b7280;
  margin-bottom: 2px;
  font-size: 14px;
}

.info-row strong {
  font-size: 17px;
  color: #111827;
}

.status-badge {
  display: inline-flex;
  border-radius: 999px;
  background: #e8f0ff;
  color: #2563eb;
  padding: 4px 10px;
  margin-top: 8px;
  text-transform: lowercase;
}

.status-badge.booked { background: #dbeafe; color: #2563eb; }
.status-badge.attending { background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }
.status-badge.completed { background: #dcfce7; color: #16a34a; }
.status-badge.cancelled { background: #fee2e2; color: #dc2626; }
.status-badge.not_attended { background: #fef3c7; color: #d97706; }

.status-row {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
}

.attending-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}

.attending-btn:hover {
  background: #1d4ed8;
}

.disabled-style {
  opacity: 0.5;
  cursor: not-allowed;
  background: #9ca3af !important;
}

.treatment-card {
  padding: 20px 26px 24px;
}

.treatment-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.treatment-form {
  padding-top: 2px;
}

.primary-btn {
  border: 0;
  border-radius: 10px;
  background: #020617;
  color: #ffffff;
  padding: 10px 16px;
  font-weight: 700;
  font-size: 14px;
}

.empty-treatment {
  min-height: 148px;
  display: grid;
  place-items: center;
  color: #9ca3af;
  font-size: 15px;
}

.treatment-form label {
  display: block;
  margin-top: 16px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
}

.treatment-form textarea,
.treatment-form input {
  width: 100%;
  border: 0;
  background: #f3f4f6;
  border-radius: 12px;
  padding: 16px 14px;
  font-size: 15px;
  outline: none;
}

.treatment-form textarea::placeholder,
.treatment-form input::placeholder {
  color: #9ca3af;
}

.treatment-form textarea {
  min-height: 70px;
  resize: vertical;
}

.form-actions {
  margin-top: 18px;
}

.complete-btn {
  width: 100%;
  border: 0;
  border-radius: 12px;
  background: #020617;
  color: #ffffff;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 44px;
}

.complete-btn:disabled {
  opacity: 0.6;
}

.summary-block {
  border-top: 1px solid #e5e7eb;
  padding: 16px 0;
}

.summary-block:first-child {
  border-top: 0;
  padding-top: 6px;
}

.summary-block span {
  display: block;
  color: #6b7280;
  margin-bottom: 6px;
  font-size: 14px;
}

.summary-block strong {
  font-size: 15px;
  line-height: 1.5;
}

.error-text {
  margin-top: 12px;
  color: #b91c1c;
  font-size: 13px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  display: grid;
  place-items: center;
  padding: 16px;
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

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
