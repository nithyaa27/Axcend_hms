<template>
  <div class="layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon"><i class="bi bi-activity"></i></div>
        <span>Hospital MS</span>
      </div>

      <nav>
        <button 
          @click="tab = 'dashboard'" 
          class="nav-item" 
          :class="{ active: tab === 'dashboard' }"
        >
          Dashboard
        </button>
        <button 
          @click="tab = 'departments'" 
          class="nav-item" 
          :class="{ active: tab === 'departments' }"
        >
          Departments
        </button>
        <button 
          @click="tab = 'doctors'" 
          class="nav-item" 
          :class="{ active: tab === 'doctors' }"
        >
          Doctors
        </button>
        <button 
          @click="tab = 'patients'" 
          class="nav-item" 
          :class="{ active: tab === 'patients' }"
        >
          Patients
        </button>
        <button 
          @click="tab = 'appointments'" 
          class="nav-item" 
          :class="{ active: tab === 'appointments' }"
        >
          Appointments
        </button>
      </nav>

      <button 
  @click="tab = 'settings'" 
  class="nav-item" 
  :class="{ active: tab === 'settings' }"
>
  <i class="bi bi-gear"></i> Settings
</button>

      <div class="sidebar-bottom">
        <div class="user-pill">
          <div class="avatar">{{ adminInitial }}</div>
          <div class="user-pill-info">
            <div class="user-pill-name">{{ adminName }}</div>
            <div class="user-pill-role">Admin</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" style="width:100%;margin-top:10px;justify-content:center;" @click="logout">
          <i class="bi bi-box-arrow-right"></i> Logout
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="main-content">
      <div v-if="successMessage" class="success-popup">
        {{ successMessage }}
      </div>
      
      <p v-if="error" class="error-banner">{{ error }}</p>

      <!-- DASHBOARD TAB -->
      <div v-if="tab === 'dashboard'" class="space-y-8">
        <div>
          <h1>Admin Dashboard</h1>
          <p class="text-gray-500">Overview of hospital management system. Welcome, {{ adminName }}</p>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div>
              <p class="stat-label">Total Doctors</p>
              <h2 class="stat-value">{{ stats.total_doctors }}</h2>
              <p class="stat-sub">Medical Staff</p>
            </div>
            <div class="stat-icon bg-blue">👨‍⚕️</div>
          </div>

          <div class="stat-card">
            <div>
              <p class="stat-label">Total Patients</p>
              <h2 class="stat-value">{{ stats.total_patients }}</h2>
              <p class="stat-sub">Registered</p>
            </div>
            <div class="stat-icon bg-green">👥</div>
          </div>

          <div class="stat-card">
            <div>
              <p class="stat-label">Total Appointments</p>
              <h2 class="stat-value">{{ stats.total_appointments }}</h2>
              <p class="stat-sub">All Time</p>
            </div>
            <div class="stat-icon bg-purple">📅</div>
          </div>

          <div class="stat-card">
            <div>
              <p class="stat-label">Active Today</p>
              <h2 class="stat-value">{{ stats.total_departments }}</h2>
              <p class="stat-sub">Departments</p>
            </div>
            <div class="stat-icon bg-orange">⚡</div>
          </div>
        </div>

        <div class="table-card">
          <div class="table-header">
            <h2 class="text-2xl font-semibold">Recent Appointments</h2>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Appointment ID</th>
                <th>Doctor</th>
                <th>Patient</th>
                <th>Date & Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in appointments.slice(0, 8)" :key="a.id">
                <td class="font-medium">apt-{{ a.id }}</td>
                <td>{{ a.doctor_name }}</td>
                <td>{{ a.patient_name }}</td>
                <td>{{ a.appointment_date }} {{ a.appointment_time }}</td>
                <td>
                  <span class="status-pill" :class="a.status">
                    {{ a.status }}
                  </span>
                </td>
              </tr>
              <tr v-if="appointments.length === 0">
                <td colspan="5" class="empty-row">No recent appointments</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- DEPARTMENTS TAB -->
      <div v-if="tab === 'departments'" class="space-y-6">
        <div class="flex-between">
          <div>
          <h1>Department Management</h1>
          <p class="text-gray-500">Manage all departments in the system</p>
          </div>
          <button class="btn-primary" @click="openDepartmentModal()">+ Add Department</button>
        </div>

        <div class="table-card">
          <div class="table-header flex-between">
            <h1 class="text-2xl font-semibold">All Departments ({{ departments.length }})</h1>
            <input v-model="deptSearch" placeholder="Search department" class="search-input" />
          </div>
          <table class="data-table">
            <thead v-if="filteredDepartments.length > 0">
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Head</th>
                <th>Doctors</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dep in filteredDepartments" :key="dep.id">
                <td class="font-medium">{{ dep.name }}</td>
                <td class="description-cell">{{ dep.description || 'N/A' }}</td>
                <td>{{ dep.head || 'N/A' }}</td>
                <td>{{ dep.doctors_count || 0 }}</td>
                <td class="actions-cell">
                  <button class="text-blue" @click="openDepartmentModal(dep)">Edit</button>
                  <button class="text-red" @click="deleteDepartment(dep.id)">Delete</button>
                </td>
              </tr>
              <tr v-if="filteredDepartments.length === 0">
                <td colspan="5" class="empty-row">No departments found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- DOCTORS TAB -->
      <div v-if="tab === 'doctors'" class="space-y-6">
        <div class="flex-between">
          <div>
          <h1>Doctor Management</h1>
          <p class="text-gray-500">Manage all doctors in the system</p>
          </div>
          <button class="btn-primary" @click="openDoctorModal()">+ Add Doctor</button>
        </div>

        <div class="table-card">
          <div class="table-header flex-between">
            <h1 class="text-2xl font-semibold">All Doctors ({{ filteredDoctors.length }})</h1>
            <input v-model="doctorSearch" placeholder="Search doctor" class="search-input" />
          </div>
          <table class="data-table">
            <thead v-if="filteredDoctors.length > 0">
              <tr>
                <th>Name</th>
                <th>Specialization</th>
                <th>Department</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Password Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in filteredDoctors" :key="doc.id">
                <td class="font-medium">{{ doc.name }}</td>
                <td>{{ doc.specialization }}</td>
                <td>{{ doc.department_name }}</td>
                <td>{{ doc.email }}</td>
                <td>{{ doc.phone }}</td>
                <td>
                  <span class="status-pill" :class="doc.status || 'active'">{{ doc.status || 'active' }}</span>
                </td>
                <td class="text-center">
                  <span :class="doc.password_set ? 'text-green' : 'text-red'">
                    {{ doc.set_password_status || (doc.password_set ? 'password set successfully' : 'password not set') }}
                  </span>
                </td>
                <td class="actions-cell">
                  <button class="text-blue" @click="openDoctorModal(doc)">Edit</button>
                  <button class="text-red" @click="deleteDoctor(doc.id)">Delete</button>
                </td>
              </tr>
              <tr v-if="filteredDoctors.length === 0">
                <td colspan="8" class="empty-row">No doctors found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- PATIENTS TAB -->
      <div v-if="tab === 'patients'" class="space-y-6">
        <div class="flex-between">
          <div>
          <h1>Patient Management</h1>
          <p class="text-gray-500">Manage all patients in the system</p>
          </div>
        </div>

        <div class="table-card">
          <div class="table-header flex-between">
            <h1 class="text-2xl font-semibold">All Patients ({{ filteredPatients.length }})</h1>
            <input v-model="patientSearch" placeholder="Search patient" class="search-input" />
          </div>
          <table class="data-table">
            <thead v-if="filteredPatients.length > 0">
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Registration Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in filteredPatients" :key="p.id">
                <td class="font-medium">{{ p.name }}</td>
                <td>{{ p.email }}</td>
                <td>{{ p.phone }}</td>
                <td>{{ p.age }}</td>
                <td>{{ p.gender }}</td>
                <td>{{ p.created_at ? new Date(p.created_at).toLocaleDateString() : 'N/A' }}</td>
                <td class="actions-cell">
                  <button class="text-blue" @click="openPatientEditModal(p)">Edit</button>
                  <button class="text-red" @click="deletePatient(p.id)">Delete</button>
                </td>
              </tr>
              <tr v-if="filteredPatients.length === 0">
                <td colspan="7" class="empty-row">No patients found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- APPOINTMENTS TAB -->
      <div v-if="tab === 'appointments'" class="space-y-6">
        <div class="flex-between">
          <div>
            <h1>Appointment Management</h1>
            <p class="text-gray-500">View and manage all appointments</p>
          </div>
        </div>

        <div class="table-card">
          <div class="table-header flex-between">
            <h1 class="text-2xl font-semibold">All Appointments ({{ filteredAppointments.length }})</h1>
          </div>
          <table class="data-table">
            <thead v-if="filteredAppointments.length > 0">
              <tr>
                <th>Appointment ID</th>
                <th>Doctor</th>
                <th>Patient</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in filteredAppointments" :key="a.id">
                <td class="font-medium">APT-{{ a.id }}</td>
                <td>{{ a.doctor_name }}</td>
                <td>{{ a.patient_name }}</td>
                <td>{{ a.appointment_date }}</td>
                <td>{{ a.appointment_time }}</td>
                <td>
                  <span class="status-pill" :class="a.status">{{ a.status }}</span>
                </td>
              </tr>
              <tr v-if="filteredAppointments.length === 0">
                <td colspan="6" class="empty-row">No appointments found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
  

  <!-- SETTINGS TAB -->
<div v-if="tab === 'settings'" class="space-y-8">

  <div>
    <h1>Reminder Settings</h1>
    <p class="text-gray-500">Configure system reminders</p>
  </div>

  <!-- Daily Reminder -->
  <div class="table-card">
    <div class="table-header flex-between">
      <h2 class="text-2xl font-semibold">Daily Reminder</h2>

      <label class="switch">
        <input type="checkbox" v-model="dailyToggle">
        <span class="slider"></span>
      </label>
    </div>

    <div v-if="dailyToggle" style="padding:20px; display:flex; gap:10px;">
      <input type="time" class="form-input" v-model="dailyTime">
      <button class="btn-primary" @click="saveReminderSettings">Save</button>
    </div>
  </div>

  <!-- Monthly Reminder -->
  <div class="table-card">
    <div class="table-header flex-between">
      <h2 class="text-2xl font-semibold">Monthly Reminder</h2>

      <label class="switch">
        <input type="checkbox" v-model="monthlyToggle">
        <span class="slider"></span>
      </label>
    </div>

    <div v-if="monthlyToggle" style="padding:20px; display:flex; gap:10px;">
      <input type="date" class="form-input" :min="todayDate" v-model="monthlyDate">
      <input type="time" class="form-input" v-model="monthlyTime">
      <button class="btn-primary" @click="saveReminderSettings">Save</button>
    </div>
  </div>

</div>
</main>

    <!-- MODALS -->
    
    <!-- Department Modal -->
    <div v-if="showDepartmentModal" class="modal-overlay">
      <div class="modal-box">
        <h3 class="modal-title">{{ departmentForm.id ? "Edit Department" : "Add Department" }}</h3>
        <div class="modal-form">
          <input v-model="departmentForm.name" placeholder="Department Name" class="form-input" />
          <input v-model="departmentForm.head" placeholder="Name of Head" class="form-input" />
          <textarea v-model="departmentForm.description" placeholder="Description" class="form-input" rows="3" style="resize: vertical;"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showDepartmentModal = false">Cancel</button>
          <button class="btn-primary" @click="saveDepartment">Save Changes</button>
        </div>
      </div>
    </div>

    <!-- Doctor Modal -->
    <div v-if="showDoctorModal" class="modal-overlay">
      <div class="modal-box">
        <h3 class="modal-title">{{ doctorForm.id ? "Edit Doctor" : "Add Doctor" }}</h3>
        <div class="modal-form">
          <input v-model="doctorForm.name" placeholder="Doctor Name" class="form-input" />
          <input v-model="doctorForm.specialization" placeholder="Specialization" class="form-input" />
          <input v-model="doctorForm.email" placeholder="Email Address" class="form-input" />
          <input v-model="doctorForm.phone" placeholder="Phone Number" class="form-input" />
          <select v-model="doctorForm.department_id" class="form-input">
            <option disabled value="">Select Department</option>
            <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
          <select v-model="doctorForm.status" class="form-input">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div class="modal-footer flex-between">
          <div>
            <button 
              v-if="doctorForm.id && !doctorForm.password_set" 
              class="btn-warn"
              @click="resendDoctorPassword(doctorForm.id)"
            >
              Resend Password Link
            </button>
          </div>
          <div class="flex gap-2">
            <button class="btn-ghost" @click="showDoctorModal = false">Cancel</button>
            <button class="btn-primary" @click="saveDoctor">Save Doctor</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Patient Edit Modal -->
    <div v-if="showPatientEditModal" class="modal-overlay">
      <div class="modal-box">
        <h3 class="modal-title">Edit Patient</h3>
        <div class="modal-form">
          <input v-model="editPatientForm.name" placeholder="Patient Name" class="form-input" />
          <input v-model="editPatientForm.email" placeholder="Email" class="form-input" />
          <input v-model="editPatientForm.phone" placeholder="Phone" class="form-input" />
          <input v-model="editPatientForm.age" type="number" placeholder="Age" class="form-input" />
          <select v-model="editPatientForm.gender" class="form-input">
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showPatientEditModal = false">Cancel</button>
          <button class="btn-primary" @click="savePatient">Update Patient</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  name: "AdminDashboard",
  data() {
    return {
      tab: "dashboard",
      dailyToggle: false,
      monthlyToggle: false,
      dailyTime: "09:00",
      monthlyDate: "",
      monthlyTime: "09:00",
      error: "",
      successMessage: "",
      stats: {
        total_doctors: 0,
        total_departments: 0,
        total_patients: 0,
        total_appointments: 0
      },
      departments: [],
      doctors: [],
      patients: [],
      appointments: [],
      doctorSearch: "",
      patientSearch: "",
      deptSearch: "",
      showDepartmentModal: false,
      showDoctorModal: false,
      showPatientModal: false,
      departmentForm: { id: null, name: "", description: "", head: "" },
      doctorForm: {
        id: null,
        name: "",
        specialization: "",
        email: "",
        phone: "",
        department_id: "",
        status: "active",
        password_set: false,
        set_password_status: ""
      },
      editPatientForm: { id: null, name: "", email: "", phone: "", age: "", gender: "" },
      showPatientEditModal: false,
    }
  },
  computed: {
  todayDate() {
    return new Date().toISOString().split('T')[0]
  },

  adminName() {
    return localStorage.getItem("name") || "Admin"
  },
    adminInitial() {
      return (this.adminName || 'A')[0].toUpperCase()
    },
    filteredDoctors() {
      const q = this.doctorSearch.toLowerCase()
      return this.doctors.filter(d => d.name.toLowerCase().includes(q))
    },
    filteredPatients() {
      const q = this.patientSearch.toLowerCase()
      return this.patients.filter(p => p.name.toLowerCase().includes(q))
    },
    filteredDepartments() {
      const q = this.deptSearch.toLowerCase()
      return this.departments.filter(d => d.name.toLowerCase().includes(q))
    },
    filteredAppointments() {
      return this.appointments
    }
  },
  methods: {
    async loadAll() {
      await Promise.all([
        this.loadDashboard(),
        this.loadDepartments(),
        this.loadDoctors(),
        this.loadPatients(),
        this.loadAppointments(),
        this.loadReminderSettings()
      ])
    },
    async loadDashboard() {
      const res = await api.get("/api/admin/dashboard")
      this.stats = res.data
    },
    async loadDepartments() {
      const res = await api.get("/api/departments")
      this.departments = res.data || []
    },
    async loadDoctors() {
      const res = await api.get("/api/admin/doctors")
      this.doctors = res.data || []
    },
    async loadPatients() {
      const res = await api.get("/api/admin/patients")
      this.patients = res.data || []
    },
    async loadAppointments() {
      const res = await api.get("/api/admin/appointments")
      this.appointments = res.data || []
    },
    normalizeMonthlyDate(day) {
      const now = new Date()
      const year = now.getFullYear()
      const monthNumber = now.getMonth() + 1
      const maxDay = new Date(year, monthNumber, 0).getDate()
      const month = String(monthNumber).padStart(2, "0")
      const normalizedDay = String(Math.max(1, Math.min(maxDay, Number(day) || 1))).padStart(2, "0")
      return `${year}-${month}-${normalizedDay}`
    },
    async loadReminderSettings() {
      const res = await api.get("/api/admin/reminder-settings")
      const settings = res.data || {}
      this.dailyToggle = Boolean(settings.daily?.enabled)
      this.dailyTime = settings.daily?.time || "09:00"
      this.monthlyToggle = Boolean(settings.monthly?.enabled)
      this.monthlyTime = settings.monthly?.time || "09:00"
      this.monthlyDate = this.normalizeMonthlyDate(settings.monthly?.day || 1)
    },
    async saveReminderSettings() {
      const monthlyDay = Number(String(this.monthlyDate || "").split("-")[2] || 1)
      const payload = {
        daily: {
          enabled: this.dailyToggle,
          time: this.dailyTime || "09:00",
        },
        monthly: {
          enabled: this.monthlyToggle,
          day: monthlyDay,
          time: this.monthlyTime || "09:00",
        },
      }
      try {
        const res = await api.put("/api/admin/reminder-settings", payload)
        const settings = res.data?.settings || payload
        this.dailyToggle = Boolean(settings.daily?.enabled)
        this.dailyTime = settings.daily?.time || "09:00"
        this.monthlyToggle = Boolean(settings.monthly?.enabled)
        this.monthlyTime = settings.monthly?.time || "09:00"
        this.monthlyDate = this.normalizeMonthlyDate(settings.monthly?.day || 1)
        this.notify("Reminder settings saved")
      } catch (err) {
        alert(err.response?.data?.error || err.message || "Failed to save reminder settings")
      }
    },
    openDepartmentModal(dep = null) {
      this.departmentForm = dep
        ? { id: dep.id, name: dep.name, description: dep.description || "", head: dep.head || "" }
        : { id: null, name: "", description: "", head: "" }
      this.showDepartmentModal = true
    },
    async saveDepartment() {
      if (!this.departmentForm.name) { alert("Name required"); return; }
      try {
        const payload = {
          name: this.departmentForm.name,
          description: this.departmentForm.description || "",
          head: this.departmentForm.head || ""
        }
        if (this.departmentForm.id) {
          await api.put(`/api/update_department/${this.departmentForm.id}`, payload)
        } else {
          await api.post("/api/add_department", payload)
        }
        this.showDepartmentModal = false
        this.loadDepartments()
        this.notify("Department saved")
      } catch (err) { alert(err.response?.data?.error || err.message || "Failed to save department"); }
    },
    async deleteDepartment(id) {
      if (!confirm("Delete this department?")) return
      try { await api.delete(`/api/delete_department/${id}`); this.loadDepartments(); } catch (err) { alert("Cannot delete department,doctor assigned to it"); }
    },
    openDoctorModal(doc = null) {
      this.doctorForm = doc
        ? {
            id: doc.id,
            name: doc.name.replace(/^Dr\.?\s/i, ""),
            specialization: doc.specialization || "",
            email: doc.email || "",
            phone: doc.phone || "",
            department_id: doc.department_id || "",
            status: doc.status || "active",
            password_set: doc.password_set || false,
            set_password_status: doc.set_password_status || ""
          }
        : {
            id: null,
            name: "",
            specialization: "",
            email: "",
            phone: "",
            department_id: "",
            status: "active",
            password_set: false,
            set_password_status: ""
          }
      this.showDoctorModal = true
    },
    async saveDoctor() {
      const payload = { ...this.doctorForm }
      delete payload.id
      delete payload.password_set
      delete payload.set_password_status
      if (!payload.name || !payload.email || !payload.phone || !payload.specialization || !payload.department_id) {
        alert("All fields are required"); return;
      }
      if (!/^Dr\.?\s/i.test(payload.name)) payload.name = `Dr. ${payload.name}`
      try {
        if (this.doctorForm.id) {
          await api.put(`/api/update_doctor/${this.doctorForm.id}`, payload)
        } else {
          await api.post("/api/add_doctor", payload)
        }
        this.showDoctorModal = false
        this.loadDoctors()
        this.notify("Doctor saved")
      } catch (err) { alert(err.response?.data?.error || err.message || "Failed to save doctor"); }
    },
    async resendDoctorPassword(id) {
      if (!confirm("Resend link?")) return
      try { await api.post(`/api/admin/resend-doctor-password/${id}`); this.showDoctorModal = false; this.notify("Link resent"); } catch (err) { alert("Failed resend"); }
    },
    async deleteDoctor(id) {
      if (!confirm("Delete doctor?")) return
      await api.delete(`/api/delete_doctor/${id}`)
      this.loadDoctors()
    },
    openPatientEditModal(patient) {
      this.editPatientForm = { id: patient.id, name: patient.name, email: patient.email || "", phone: patient.phone || "", age: patient.age || "", gender: patient.gender || "" }
      this.showPatientEditModal = true
    },
    async savePatient() {
      const { name, email, phone, age, gender } = this.editPatientForm
      if (!name || !email || !phone || !gender || !age) {
        alert("All fields are required"); return;
      }
      try {
        await api.put(`/api/admin/patients/${this.editPatientForm.id}`, this.editPatientForm)
        this.showPatientEditModal = false
        this.loadPatients()
        this.notify("Patient updated")
      } catch (err) { alert(err.response?.data?.error || err.message || "Failed to update patient"); }
    },
    async deletePatient(id) {
      if (!confirm("Delete?")) return
      await api.delete(`/api/admin/patients/${id}`)
      this.loadPatients()
    },
    notify(msg) {
      this.successMessage = msg
      setTimeout(() => { this.successMessage = "" }, 2000)
    },
    async logout() {
      localStorage.clear()
      this.$router.push("/login")
    }
  },
  async mounted() {
    try { await this.loadAll(); } catch (err) { this.error = "Connection error"; }
  }
}
</script>

<style scoped>
/* ---------------- LAYOUT ---------------- */

/* SETTINGS ALIGNMENT FIX */
.settings-wrapper{
  width:100%;
}

.settings-card{
  width:100%;
  max-width:900px;
  background:white;
  padding:24px;
  border-radius:16px;
  box-shadow:0 1px 3px rgba(0,0,0,0.1);
  margin-bottom:20px;
}

.settings-title{
  font-size:22px;
  font-weight:600;
}

.settings-body{
  margin-top:15px;
  display:flex;
  gap:10px;
}

/* toggle */
.switch{
  position:relative;
  display:inline-block;
  width:46px;
  height:24px;
}

.switch input{
  display:none;
}

.slider{
  position:absolute;
  background:#ccc;
  border-radius:20px;
  top:0;
  left:0;
  right:0;
  bottom:0;
}

.slider:before{
  position:absolute;
  content:"";
  height:18px;
  width:18px;
  left:3px;
  bottom:3px;
  background:white;
  border-radius:50%;
  transition:0.3s;
}

input:checked + .slider{
  background:#2563eb;
}

input:checked + .slider:before{
  transform:translateX(22px);
}
.layout {
  display: flex;
  height: 100vh;
  background: #f6f8fc;
  font-family: 'Segoe UI', sans-serif;
  color: #111827;
  --blue: #2563eb;
  --blue-lt: #eff6ff;
  --border: #e5e7eb;
  --bg: #f6f8fc;
  --muted: #6b7280;
}

.sidebar {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
  font-size: 20px;
  font-weight: 700;
  color: var(--blue);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--blue);
  color: white;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 24px;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 0;
  background: transparent;
  border-radius: 12px;
  color: var(--muted);
  font-weight: 500;
  text-align: left;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--blue-lt);
  color: var(--blue);
}

.nav-item.active {
  background: var(--blue);
  color: white;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.sidebar-bottom {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
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

.user-pill-name {
  font-weight: 600;
  font-size: 14px;
}

.user-pill-role {
  font-size: 12px;
  color: var(--muted);
}

/* ---------------- BUTTONS ---------------- */
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

/* ---------------- MAIN CONTENT ---------------- */

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 20px;
  border: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: var(--muted);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.stat-sub {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 24px;
}

.bg-blue { background: #eff6ff; color: #2563eb; }
.bg-green { background: #f0fdf4; color: #16a34a; }
.bg-purple { background: #faf5ff; color: #9333ea; }
.bg-orange { background: #fff7ed; color: #ea580c; }

/* ---------------- TABLES ---------------- */

.table-card {
  background: white;
  border-radius: 20px;
  border: 1px solid var(--border);
  overflow: hidden;
}

.table-header {
  padding: 24px;
  border-bottom: 1px solid var(--border);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 16px 24px;
  background: #f9fafb;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.description-cell {
  max-width: 300px;
  color: var(--muted);
}

.status-pill {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-pill.active, .status-pill.booked { background: #dcfce7; color: #16a34a; }
.status-pill.inactive, .status-pill.cancelled { background: #fee2e2; color: #dc2626; }
.status-pill.pending { background: #fef3c7; color: #d97706; }

.actions-cell button {
  padding: 4px 8px;
  font-weight: 600;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.text-blue { color: var(--blue); }
.text-red { color: #ef4444; }
.text-green { color: #16a34a; }

.empty-row {
  text-align: center;
  padding: 40px !important;
  color: var(--muted);
}

/* ---------------- UTILITIES ---------------- */

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.space-y-6 > * + * { margin-top: 24px; }
.space-y-8 > * + * { margin-top: 32px; }

.btn-primary {
  background: var(--blue);
  color: white;
  padding: 10px 20px;
  border-radius: 12px;
  border: 0;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}



.btn-warn {
  background: #fff7ed;
  color: #ea580c;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #ffedd5;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
}

.search-input {
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 280px;
}

.success-popup {
  position: fixed;
  top: 24px;
  right: 24px;
  background: #16a34a;
  color: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 10px 15px rgba(0,0,0,0.1);
  z-index: 100;
}

/* ---------------- MODALS ---------------- */

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  display: grid;
  place-items: center;
  z-index: 50;
}

.modal-box {
  background: white;
  width: 480px;
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-input {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
}

.modal-footer {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
