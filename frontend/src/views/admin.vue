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

      <div class="sidebar-bottom">
        <div class="user-pill">
          <div class="avatar">{{ adminInitial }}</div>
          <div class="user-pill-info">
            <div class="user-pill-name">{{ adminName }}</div>
            <div class="user-pill-role">Admin</div>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm logout-btn" @click="logout">
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
                <th>Password Set</th>
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
                  <span v-if="doc.password_set" class="text-green">Yes</span>
                  <span v-else class="text-red">No</span>
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
        password_set: false
      },
      editPatientForm: { id: null, name: "", email: "", phone: "", age: "", gender: "" },
      showPatientEditModal: false,
    }
  },
  computed: {
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
        this.loadAppointments()
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
            password_set: doc.password_set || false
          }
        : {
            id: null,
            name: "",
            specialization: "",
            email: "",
            phone: "",
            department_id: "",
            status: "active",
            password_set: false
          }
      this.showDoctorModal = true
    },
    async saveDoctor() {
      const payload = { ...this.doctorForm }
      delete payload.id
      delete payload.password_set
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
  width: 260px;
  background: #f3f6fb;
  padding: 30px 20px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e7eb;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 0 28px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
  font-family: "Sora", sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
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

.nav-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 14px 18px;
  margin-bottom: 12px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #111827;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: 0.2s;
}

.nav-item:hover { background: var(--blue); color: white; }
.nav-item.active { background: var(--blue); color: white; }

.sidebar-bottom { 
  margin-top: auto; 
  padding: 16px 0; 
  border-top: 1px solid var(--border); 
}

.user-pill { 
  display: flex; 
  align-items: center; 
  gap: 10px; 
  padding: 10px 12px; 
  background: white; 
  border-radius: 12px; 
  margin-bottom: 12px;
  border: 1px solid var(--border);
}

.avatar { 
  width: 34px; 
  height: 34px; 
  border-radius: 50%; 
  background: var(--blue); 
  color: white; 
  font-weight: 700; 
  font-size: 14px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  flex-shrink: 0; 
}

.user-pill-info { flex: 1; overflow: hidden; }
.user-pill-name { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-pill-role { font-size: 11px; color: var(--muted); }

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
  transition: all .18s; 
}

.btn-ghost { 
  background: transparent; 
  color: var(--blue); 
  border: 1px solid var(--blue); 
}

.btn-ghost:hover { 
  background: var(--blue-lt); 
}

.btn-sm { 
  padding: 5px 12px; 
  font-size: 12px; 
}

.logout-btn {
  width: 100%;
  justify-content: center;
}

.main-content {
  flex: 1;
  padding: 50px;
  overflow-y: auto;
}

/* ---------------- DASHBOARD ---------------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label { font-size: 14px; color: #6b7280; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-icon { font-size: 24px; padding: 12px; border-radius: 12px; }
.bg-blue { background: #3b82f6; color: white; }
.bg-green { background: #10b981; color: white; }
.bg-purple { background: #a855f7; color: white; }
.bg-orange { background: #f97316; color: white; }

/* ---------------- TABLES ---------------- */
.table-card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; }
.table-header { padding: 20px; border-bottom: 1px solid #e5e7eb; }
.data-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.data-table th { background: #f9fafb; padding: 12px 16px; text-align: left; color: #111827; font-weight: 600; font-size: 15px; word-wrap: break-word; overflow-wrap: break-word; word-break: break-word; }
.data-table td { padding: 14px 16px; border-top: 1px solid #e5e7eb; font-size: 14px; word-wrap: break-word; overflow-wrap: break-word; word-break: break-word; }
.empty-row { text-align: center; padding: 40px; color: #9ca3af; }
.font-medium { font-weight: 500; }
.description-cell { max-width: 300px; }

.status-pill {
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}
.status-pill.booked { background: #dbeafe; color: #2563eb; }
.status-pill.completed { background: #dcfce7; color: #16a34a; }
.status-pill.cancelled { background: #fee2e2; color: #dc2626; }
.status-pill.not_attended { background: #fef3c7; color: #d97706; }
.status-pill.not_visited { background: #ffedd5; color: #ea580c; }
.status-pill.not_visited_cancelled { background: #f3f4f6; color: #4b5563; }
.status-pill.active { background: #dcfce7; color: #16a34a; }
.status-pill.inactive { background: #fee2e2; color: #dc2626; }

/* ---------------- BUTTONS ---------------- */
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.btn-primary { background: #2563eb; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 500; cursor: pointer; }
.btn-ghost { background: white; border: 1px solid #d1d5db; padding: 10px 16px; border-radius: 8px; cursor: pointer; }
.btn-warn { background: #f59e0b; color: white; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; }
.text-blue { color: #2563eb; background: none; border: none; cursor: pointer; margin-right: 12px; }
.text-red { color: #dc2626; background: none; border: none; cursor: pointer; }
.text-green { color: #10b981; font-weight: 600; }
.search-input { border: 1px solid #e5e7eb; padding: 8px 12px; border-radius: 8px; }

/* ---------------- MODALS ---------------- */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 50; }
.modal-box { background: white; width: 400px; padding: 24px; border-radius: 12px; display: flex; flex-direction: column; gap: 16px; }
.modal-title { font-size: 18px; font-weight: 600; }
.modal-form { display: flex; flex-direction: column; gap: 12px; }
.form-input { border: 1px solid #e5e7eb; padding: 10px; border-radius: 6px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; }

/* ---------------- UTILS ---------------- */
.success-popup { position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 12px 24px; border-radius: 8px; z-index: 100; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.error-banner { background: #fee2e2; color: #dc2626; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
.space-y-6 > * + * { margin-top: 24px; }
.space-y-8 > * + * { margin-top: 32px; }
.text-2xl { font-size: 24px; }
.font-semibold { font-weight: 600; }
.text-gray-500 { color: #6b7280; }
.text-center { text-align: center; }
</style>
