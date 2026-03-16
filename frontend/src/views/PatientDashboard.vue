<script setup>
import { ref, computed, onMounted } from 'vue'
import api, {
  getDashboardData,
  getAppointments,
  getAppointmentDetail,
  bookAppointment,
  cancelAppointment,
  rescheduleAppointment,
  getDoctors,
  getDoctorSlots,
  getPrescriptions,
  downloadReport,
  downloadReportPdf,
  updatePatientEmail,
  getNotifications
} from '../api/api.js'

// ─── Helpers ───────────────────────────────────────────────────────────────

function avatarColor(name) {
  const colors = ['', 'green', 'purple', 'amber']
  return colors[(name || '').charCodeAt(0) % colors.length]
}

// ─── Toast ─────────────────────────────────────────────────────────────────

const toastMsg     = ref('')
const toastVisible = ref(false)
let toastTimer     = null

function showToast(msg, duration = 3500) {
  toastMsg.value     = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, duration)
}

function getErrorMessage(err, fallback) {
  const apiMsg = err?.response?.data?.message
  return apiMsg || fallback
}

function redirectToLoginIfUnauthorized(err) {
  if (err?.response?.status === 401) {
    // Interceptor in services/interceptor.js handles the actually logout logic and redirect
    return true
  }
  return false
}

// ─── Navigation ────────────────────────────────────────────────────────────

const currentView = ref('dashboard')

const pageTitle = computed(() => {
  const map = {
    'dashboard':    'Patient Dashboard',
    'find-doctors': 'Find Doctors',
    'appointments': 'My Appointments',
    'prescriptions':'My Prescriptions',
    'apt-detail':   'Appointment Details',
    'my-data':      'My Data & Records',
  }
  return map[currentView.value] || 'Hospital MS'
})

const pageSub = computed(() => {
  const map = {
    'dashboard':    `Welcome back, ${patient.value.name}`,
    'find-doctors': 'Search for doctors by name or specialization',
    'appointments': 'View your appointment history and details',
    'prescriptions':'View your prescriptions and medication instructions',
    'apt-detail':   'View your appointment information',
    'my-data':      'Download your complete medical records',
  }
  return map[currentView.value] || ''
})

function showView(name) {
  currentView.value = name
  if (name === 'appointments') loadAptTab(activeTab.value)
  if (name === 'find-doctors' && allDoctors.value.length === 0) loadDoctors()
  if (name === 'prescriptions' && prescriptions.value.length === 0) loadPrescriptions()
}

// ─── Patient & Stats ───────────────────────────────────────────────────────

const patient = ref({ name: '', email: '', gender: '', patient_uid: '' })
const stats   = ref({ total_visits: 0, upcoming: 0, completed: 0, cancelled: 0 })

const patientInitial = computed(() => (patient.value.name || 'P')[0].toUpperCase())

// ─── Dashboard ─────────────────────────────────────────────────────────────

const upcomingApts   = ref([])
const todayReminders = ref([])
const nextApt        = computed(() => upcomingApts.value[0] || null)
const today          = new Date().toISOString().split('T')[0]

async function loadDashboard() {
  try {
    const data = await getDashboardData()
    if (!data || data.status !== 'success') return
    patient.value = data.patient
    stats.value   = data.stats

    const apts = await getAppointments('upcoming')
    if (apts?.appointments) {
      upcomingApts.value = apts.appointments
      const todayStr = new Date().toDateString()
      todayReminders.value = apts.appointments.filter(a =>
        a.date_full && new Date(a.date_full).toDateString() === todayStr
      )
    }
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load dashboard data'))
  }
}

// ─── Find Doctors ──────────────────────────────────────────────────────────

const allDoctors = ref([])
const docSearch  = ref('')
const specFilter = ref('')

const specializations = computed(() =>
  [...new Set(allDoctors.value.map(d => d.specialization).filter(Boolean))]
)

const filteredDoctors = computed(() =>
  allDoctors.value.filter(d =>
    (!docSearch.value || d.name.toLowerCase().includes(docSearch.value.toLowerCase())) &&
    (!specFilter.value || d.specialization === specFilter.value)
  )
)

async function loadDoctors() {
  try {
    const data = await getDoctors()
    if (data?.doctors) allDoctors.value = data.doctors
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load doctors'))
  }
}

// ─── My Appointments ───────────────────────────────────────────────────────

const aptList   = ref([])
const activeTab = ref('upcoming')

async function loadAptTab(tab) {
  activeTab.value = tab
  aptList.value   = []
  try {
    const data = await getAppointments(tab)
    if (data?.appointments) aptList.value = data.appointments
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load appointments'))
  }
}

function aptStatusKey(apt) {
  return (apt?.display_status || apt?.status || 'booked').toLowerCase()
}

function aptStatusLabel(apt) {
  if (apt?.display_label) return apt.display_label
  const key = aptStatusKey(apt)
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function aptStatusClass(apt) {
  const key = aptStatusKey(apt)
  if (key === 'completed') return 'badge-completed'
  if (key === 'cancelled' || key === 'not_visited_cancelled') return 'badge-cancelled'
  if (key === 'not_attended' || key === 'not_visited') return 'badge-warning'
  return 'badge-booked'
}

function canRescheduleApt(apt) {
  if (typeof apt?.reschedulable === 'boolean') return apt.reschedulable
  return (apt?.status || '').toLowerCase() === 'booked'
}

function canCancelApt(apt) {
  if (typeof apt?.cancelable === 'boolean') return apt.cancelable
  return (apt?.status || '').toLowerCase() === 'booked'
}

// Prescriptions 

const prescriptions = ref([])

function rxStatusClass(status) {
  const s = (status || '').toLowerCase()
  if (s === 'active') return 'badge-booked'
  if (s === 'completed') return 'badge-completed'
  if (s === 'cancelled' || s === 'stopped') return 'badge-cancelled'
  return 'badge-booked'
}

async function loadPrescriptions() {
  try {
    const data = await getPrescriptions()
    if (data?.prescriptions) prescriptions.value = data.prescriptions
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load prescriptions'))
  }
}

async function doCancel(aptId) {
  if (!confirm('Cancel this appointment?')) return
  try {
    const res = await cancelAppointment(aptId)
    if (res?.status === 'success') {
      showToast('Appointment cancelled')
      loadAptTab(activeTab.value)
      loadDashboard()
      if (currentView.value === 'apt-detail') openAptDetail(aptId)
    } else {
      showToast(res?.message || 'Cancel failed')
    }
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Cancel failed'))
  }
}

// ─── Apt Detail ────────────────────────────────────────────────────────────

const aptDetail = ref(null)

async function openAptDetail(aptId) {
  currentView.value = 'apt-detail'
  aptDetail.value   = null
  try {
    const data = await getAppointmentDetail(aptId)
    if (data?.appointment) aptDetail.value = data.appointment
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load appointment details'))
  }
}

// ─── Reschedule Modal ──────────────────────────────────────────────────────

const showReschedModal = ref(false)
const reschedDate      = ref('')
const reschedSlot      = ref(null)
const reschedSlots     = ref([])

function openReschedule() {
  reschedDate.value      = ''
  reschedSlot.value      = null
  reschedSlots.value     = []
  showReschedModal.value = true
}

function slotToDate(dateStr, slotLabel) {
  const [timePart, period] = slotLabel.split(' ')
  if (!timePart || !period) return null
  const [hStr, mStr] = timePart.split(':')
  let h = Number(hStr)
  const m = Number(mStr)
  if (Number.isNaN(h) || Number.isNaN(m)) return null
  if (period === 'PM' && h !== 12) h += 12
  if (period === 'AM' && h === 12) h = 0
  return new Date(`${dateStr}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00`)
}

function applyClientSlotRules(slotList, dateStr) {
  const now = new Date()
  return slotList.map((s) => {
    if (!s?.available || !s?.slot) return s
    const slotDate = slotToDate(dateStr, s.slot)
    if (!slotDate || Number.isNaN(slotDate.getTime())) return s

    const isToday = slotDate.toDateString() === now.toDateString()
    const hh = slotDate.getHours()
    const isLunch = hh === 13 // 1:00 PM to 1:59 PM
    const isPast = isToday && slotDate <= now

    if (isLunch) return { ...s, available: false, reason: 'lunch_break' }
    if (isPast) return { ...s, available: false, reason: 'past_time' }
    return s
  })
}

async function loadReschedSlots() {
  if (!reschedDate.value || !aptDetail.value) return
  try {
    const data = await getDoctorSlots(aptDetail.value.doctor_id, reschedDate.value)
    if (data?.slots) reschedSlots.value = applyClientSlotRules(data.slots, reschedDate.value)
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load slots'))
  }
}

async function confirmReschedule() {
  if (!reschedDate.value || !reschedSlot.value) { showToast('Please select date and slot'); return }
  try {
    const res = await rescheduleAppointment(aptDetail.value.id, reschedDate.value, reschedSlot.value)
    if (res?.status === 'success') {
      showToast('Rescheduled successfully')
      showReschedModal.value = false
      openAptDetail(aptDetail.value.id)
      loadDashboard()
      loadAptTab(activeTab.value)
    } else {
      showToast(res?.message || 'Reschedule failed')
    }
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Reschedule failed'))
  }
}

// ─── Book Modal ────────────────────────────────────────────────────────────

const showBookModal     = ref(false)
const bookDoctor        = ref(null)
const bookDate          = ref('')
const bookSlot          = ref(null)
const slots             = ref([])
const dailyCount        = ref(0)
const dailyLimit        = ref(3)
const dailyLimitReached = ref(false)

function openBookModal(doctor) {
  bookDoctor.value        = doctor
  bookDate.value          = ''
  bookSlot.value          = null
  slots.value             = []
  dailyCount.value        = 0
  dailyLimitReached.value = false
  showBookModal.value     = true
}

async function loadSlots() {
  if (!bookDate.value) return
  try {
    const data = await getDoctorSlots(bookDoctor.value.id, bookDate.value)
    if (!data?.slots) return
    slots.value             = applyClientSlotRules(data.slots, bookDate.value)
    dailyCount.value        = data.daily_count || 0
    dailyLimit.value        = data.daily_limit || 3
    dailyLimitReached.value = data.daily_limit_reached || false
    bookSlot.value          = null
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Could not load slots'))
  }
}

function selectBookSlot(slot) {
  bookSlot.value = slot
}

function slotReasonLabel(reason) {
  const map = {
    'doctor_taken':     'Doctor already booked at this time',
    'your_appointment': 'You already have an appointment at this time',
    'daily_limit':      'Daily limit of 3 appointments reached',
    'lunch_break':      'Doctor lunch break (1:00 PM to 2:00 PM)',
    'past_time':        'This time has already passed for today',
    'outside_schedule': 'Doctor is not on shift at this time',
    'doctor_off':       'Doctor is off on this day',
  }
  return map[reason] || 'Unavailable'
}

async function confirmBooking() {
  if (!bookDate.value || !bookSlot.value) { showToast('Please select date and slot'); return }
  try {
    const res = await bookAppointment(bookDoctor.value.id, bookDate.value, bookSlot.value)
    if (res?.status === 'success') {
      showToast('Appointment booked successfully')
      showBookModal.value = false
      loadDashboard()
      loadDoctors()
      loadAptTab(activeTab.value)
    } else {
      showToast(res?.message || 'Booking failed')
    }
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Booking failed'))
  }
}

// ─── Profile Modal ─────────────────────────────────────────────────────────

const showProfileModal = ref(false)

// ─── Logout ────────────────────────────────────────────────────────────────

async function doLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('isLoggedIn')
  localStorage.removeItem('role')
  localStorage.removeItem('name')
  window.location.href = '/login'
}

// ─── Notifications ─────────────────────────────────────────────────────────

const notifications = ref([])
const showNotifPanel = ref(false)
const lastSeenTime   = ref(localStorage.getItem('hms_last_seen_notif') || '')

const unreadCount = computed(() => {
  if (!notifications.value.length) return 0
  if (!lastSeenTime.value) return notifications.value.length
  return notifications.value.filter(n => n.time > lastSeenTime.value).length
})

async function loadNotifications() {
  try {
    const res = await getNotifications()
    if (res?.status === 'success') {
      notifications.value = res.notifications
    }
  } catch (err) {
    console.error('Failed to load notifications', err)
  }
}

function toggleNotifications() {
  showNotifPanel.value = !showNotifPanel.value
  if (showNotifPanel.value) {
    // When opening, mark the latest as seen
    if (notifications.value.length > 0) {
      const latest = notifications.value[0].time
      lastSeenTime.value = latest
      localStorage.setItem('hms_last_seen_notif', latest)
    }
  }
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// ─── Email Update ──────────────────────────────────────────────────────────

const showEmailModal = ref(false)
const newEmail       = ref('')

function openEmailUpdate(current = '') {
  newEmail.value = current || patient.value.email
  showEmailModal.value = true
}

async function handleUpdateEmail() {
  if (!newEmail.value) return
  try {
    const res = await updatePatientEmail(newEmail.value)
    if (res?.status === 'success') {
      showToast('Email updated successfully')
      showEmailModal.value = false
      patient.value.email = newEmail.value
    } else {
      showToast(res?.message || 'Update failed')
    }
  } catch (err) {
    showToast(getErrorMessage(err, 'Update failed'))
  }
}

async function handleDownload(type) {
  try {
    if (type === 'pdf') await downloadReportPdf()
    else await downloadReport()
    showToast('Download started successfully')
  } catch (err) {
    if (redirectToLoginIfUnauthorized(err)) return
    showToast(getErrorMessage(err, 'Download failed. Please try again.'))
  }
}

// ─── Lifecycle ─────────────────────────────────────────────────────────────

onMounted(() => {
  loadDashboard()
  loadDoctors()
  loadPrescriptions()
  loadNotifications()
  // Poll notifications every 30s
  setInterval(loadNotifications, 30000)
})
</script>

<template>
  <div class="dashboard-shell">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-icon"><i class="bi bi-activity"></i></div>
      <span>Hospital MS</span>
    </div>
    <nav>
      <button class="nav-item" :class="{ active: currentView === 'dashboard' }" @click="showView('dashboard')">
        <i class="bi bi-grid-1x2"></i> Dashboard
      </button>
      <button class="nav-item" :class="{ active: currentView === 'find-doctors' }" @click="showView('find-doctors')">
        <i class="bi bi-search"></i> Find Doctors
      </button>
      <button class="nav-item" :class="{ active: currentView === 'appointments' || currentView === 'apt-detail' }" @click="showView('appointments')">
        <i class="bi bi-calendar3"></i> My Appointments
      </button>
      <button class="nav-item" :class="{ active: currentView === 'prescriptions' }" @click="showView('prescriptions')">
        <i class="bi bi-prescription2"></i> My Prescriptions
      </button>
      <button class="nav-item" :class="{ active: currentView === 'my-data' }" @click="showView('my-data')">
        <i class="bi bi-cloud-download"></i> My Data
      </button>
    </nav>
    <div class="sidebar-bottom">
      <div class="user-pill" @click="showProfileModal = true">
        <div class="avatar">{{ patientInitial }}</div>
        <div class="user-pill-info">
          <div class="user-pill-name">{{ patient.name || 'Loading…' }}</div>
          <div class="user-pill-role">Patient</div>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" style="width:100%;margin-top:10px;justify-content:center;" @click="doLogout">
        <i class="bi bi-box-arrow-right"></i> Logout
      </button>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">
    <div class="topbar">
      <div>
        <div class="page-title">{{ pageTitle }}</div>
        <div class="page-sub">{{ pageSub }}</div>
        <button v-if="currentView !== 'dashboard'" class="btn-back" @click="showView('dashboard')" style="margin-top: 12px;">
          <i class="bi bi-arrow-left"></i> Back
        </button>
      </div>
      <div class="topbar-right">
        <!-- NOTIFICATIONS -->
        <div class="notif-wrapper">
          <div class="notif-bell" :class="{ has_new: unreadCount > 0 }" @click="toggleNotifications">
            <i class="bi bi-bell"></i>
            <span class="notif-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
          </div>
          
          <div class="notif-panel" v-if="showNotifPanel">
            <div class="notif-header">
              <span>Notifications</span>
              <button class="btn-close-notif" @click="showNotifPanel = false"><i class="bi bi-x"></i></button>
            </div>
            <div class="notif-list">
              <div v-if="notifications.length === 0" class="notif-empty">
                No new notifications
              </div>
              <div v-for="n in notifications" :key="n.id" class="notif-item" :class="n.type">
                <div class="notif-icon">
                  <i v-if="n.type === 'success'" class="bi bi-check-circle-fill"></i>
                  <i v-else-if="n.type === 'invalid_email'" class="bi bi-exclamation-triangle-fill"></i>
                  <i v-else class="bi bi-info-circle-fill"></i>
                </div>
                <div class="notif-content">
                  <div class="notif-title">{{ n.title }}</div>
                  <div class="notif-msg">{{ n.message }}</div>
                  <div class="notif-time">{{ timeAgo(n.time) }}</div>
                  <button v-if="n.type === 'invalid_email'" class="btn btn-primary btn-sm" style="margin-top:8px" @click="openEmailUpdate()">
                    Update Email ID
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="avatar sm" style="cursor:pointer" @click="showProfileModal = true">{{ patientInitial }}</div>
      </div>
    </div>

    <!-- VIEW: DASHBOARD -->
    <div v-if="currentView === 'dashboard'">
      <div class="stats-row">
        <div class="stat-tile">
          <div><div class="stat-value">{{ stats.total_visits ?? '—' }}</div><div class="stat-label">Total Visits</div></div>
          <div class="stat-icon icon-blue"><i class="bi bi-calendar-check"></i></div>
        </div>
        <div class="stat-tile">
          <div><div class="stat-value">{{ stats.upcoming ?? '—' }}</div><div class="stat-label">Upcoming</div></div>
          <div class="stat-icon icon-amber"><i class="bi bi-activity"></i></div>
        </div>
        <div class="stat-tile">
          <div><div class="stat-value">{{ stats.completed ?? '—' }}</div><div class="stat-label">Completed</div></div>
          <div class="stat-icon icon-green"><i class="bi bi-clipboard2-pulse"></i></div>
        </div>
        <div class="stat-tile">
          <div><div class="stat-value">{{ stats.cancelled ?? '—' }}</div><div class="stat-label">Cancelled</div></div>
          <div class="stat-icon icon-red"><i class="bi bi-x-circle"></i></div>
        </div>
      </div>

      <div class="two-col">
        <div class="next-apt-card">
          <div class="next-apt-label">Next Appointment</div>
          <div v-if="nextApt">
            <div class="next-apt-grid">
              <div><div class="nap-item-label">Doctor</div><div class="nap-item-val">{{ nextApt.doctor }}</div></div>
              <div><div class="nap-item-label">Date</div><div class="nap-item-val">{{ nextApt.date_full }}</div></div>
              <div><div class="nap-item-label">Time</div><div class="nap-item-val">{{ nextApt.time }}</div></div>
            </div>
            <button class="btn-view-apt" @click="openAptDetail(nextApt.id)">View Details →</button>
          </div>
          <div v-else style="opacity:.7;font-size:14px">No upcoming appointments.</div>
        </div>
        <div class="card">
          <div class="card-title">Reminders</div>
          <div class="reminder-list">
            <div v-if="todayReminders.length === 0" class="empty-state" style="padding:20px">
              <i class="bi bi-bell-slash"></i>No reminders for today
            </div>
            <div class="reminder-item" v-for="(r, i) in todayReminders" :key="i">
              <i class="bi bi-bell-fill"></i>
              <span>Appointment today with <strong>{{ r.doctor }}</strong> at {{ r.time }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card full">
        <div class="card-title">Quick Actions</div>
        <div class="qa-grid">
          <div class="qa-tile" @click="showView('find-doctors')">
            <span class="qa-icon" style="color:var(--blue)"><i class="bi bi-search"></i></span>
            <div class="qa-label">Find Doctors</div>
            <div class="qa-desc">Search by specialization</div>
          </div>
          <div class="qa-tile" @click="showView('find-doctors')">
            <span class="qa-icon" style="color:var(--green)"><i class="bi bi-calendar-plus"></i></span>
            <div class="qa-label">Book Appointment</div>
            <div class="qa-desc">Schedule a new appointment</div>
          </div>
          <div class="qa-tile" @click="showView('appointments')">
            <span class="qa-icon" style="color:var(--purple)"><i class="bi bi-clock-history"></i></span>
            <div class="qa-label">My Appointments</div>
            <div class="qa-desc">View appointment history</div>
          </div>
        </div>
      </div>

      <div class="card full">
        <div class="card-title">Upcoming Appointments</div>
        <div class="apt-list">
          <div class="empty-state" v-if="upcomingApts.length === 0"><i class="bi bi-calendar-x"></i>No upcoming appointments</div>
          <div class="apt-row" v-for="a in upcomingApts.slice(0, 5)" :key="a.id">
            <div class="avatar" :class="avatarColor(a.doctor)">{{ (a.doctor || '?')[0] }}</div>
            <div class="apt-info">
              <div class="apt-name">{{ a.doctor }}</div>
              <div class="apt-meta">{{ a.date }} at {{ a.time }}</div>
            </div>
            <span class="apt-badge" :class="aptStatusClass(a)">{{ aptStatusLabel(a) }}</span>
            <button class="btn btn-ghost btn-sm" @click="openAptDetail(a.id)">View</button>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: FIND DOCTORS -->
    <div v-if="currentView === 'find-doctors'">
      <div class="card full">
        <div class="search-bar">
          <i class="bi bi-search" style="color:var(--muted)"></i>
          <input type="text" v-model="docSearch" placeholder="Search doctors by name…" />
          <select v-model="specFilter">
            <option value="">All Specializations</option>
            <option v-for="s in specializations" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>
      <div class="doctor-grid">
        <div class="empty-state" style="grid-column:1/-1" v-if="filteredDoctors.length === 0">
          <i class="bi bi-person-slash"></i>No doctors found
        </div>
        <div class="doctor-card" v-for="d in filteredDoctors" :key="d.id">
          <div class="avatar sm" :class="avatarColor(d.name)" style="margin:0 auto 10px">{{ d.name[0] }}</div>
          <div style="font-weight:700;font-size:15px">{{ d.name }}</div>
          <span class="doc-spec">{{ d.specialization || 'General' }}</span>
          <div class="doc-avail" :class="d.is_available ? 'ok' : 'no'">
            <i :class="d.is_available ? 'bi bi-check-circle' : 'bi bi-x-circle'"></i>
            {{ d.is_available ? 'Available' : 'Unavailable' }}
          </div>
          <div class="doc-meta"><i class="bi bi-building"></i> {{ d.department || 'N/A' }}</div>
          <div class="doc-meta"><i class="bi bi-telephone"></i> {{ d.phone || 'N/A' }}</div>
          <div class="doc-actions">
            <button class="btn btn-primary" :disabled="!d.is_available" @click="openBookModal(d)">
              <i class="bi bi-calendar-plus"></i> Book
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: MY APPOINTMENTS -->
    <div v-if="currentView === 'appointments'">
      <div class="card full">
        <div style="display:flex;gap:0;border-radius:10px;overflow:hidden;border:1px solid var(--border);margin-bottom:20px;width:fit-content;">
          <button class="btn btn-sm" :class="activeTab === 'upcoming' ? 'btn-primary' : 'btn-ghost'" style="border-radius:0;border:none" @click="loadAptTab('upcoming')">Upcoming</button>
          <button class="btn btn-sm" :class="activeTab === 'past'     ? 'btn-primary' : 'btn-ghost'" style="border-radius:0;border:none" @click="loadAptTab('past')">Past</button>
        </div>
        <div class="apt-list">
          <div class="empty-state" v-if="aptList.length === 0"><i class="bi bi-calendar-x"></i>No {{ activeTab }} appointments</div>
          <div class="apt-row" v-for="a in aptList" :key="a.id">
            <div class="avatar" :class="avatarColor(a.doctor)">{{ (a.doctor || '?')[0] }}</div>
            <div class="apt-info">
              <div class="apt-name">{{ a.doctor || 'N/A' }}</div>
              <div class="apt-meta">{{ a.date }} at {{ a.time }} · {{ a.specialty || '' }}</div>
            </div>
            <span class="apt-badge" :class="aptStatusClass(a)">{{ aptStatusLabel(a) }}</span>
            <div style="display:flex;gap:8px;align-items:center">
              <button class="btn btn-ghost btn-sm" v-if="canCancelApt(a)" @click="doCancel(a.id)"><i class="bi bi-x"></i> Cancel</button>
              <button class="btn btn-ghost btn-sm" v-if="canRescheduleApt(a)" @click="openAptDetail(a.id)"><i class="bi bi-arrow-repeat"></i> Reschedule</button>
              <button class="btn btn-primary btn-sm" @click="openAptDetail(a.id)">View Details</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: APT DETAIL -->
    <div v-if="currentView === 'apt-detail'">
      <div class="card full" v-if="aptDetail">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
          <div style="font-family:'Sora',sans-serif;font-size:18px;font-weight:700">Appointment Information</div>
          <span class="apt-badge" :class="aptStatusClass(aptDetail)">{{ aptStatusLabel(aptDetail) }}</span>
        </div>
        <div class="detail-grid">
          <div class="detail-box" style="border-left:3px solid var(--blue)">
            <div class="detail-box-label">Doctor</div>
            <div class="detail-box-val">{{ aptDetail.doctor || 'N/A' }}</div>
            <div class="detail-box-sub">{{ aptDetail.specialty || '' }}</div>
          </div>
          <div class="detail-box" style="border-left:3px solid var(--purple)">
            <div class="detail-box-label">Date</div>
            <div class="detail-box-val">{{ aptDetail.date_full || aptDetail.date }}</div>
          </div>
          <div class="detail-box" style="border-left:3px solid var(--green)">
            <div class="detail-box-label">Time</div>
            <div class="detail-box-val">{{ aptDetail.time }}</div>
          </div>
          <div class="detail-box" style="border-left:3px solid var(--amber)">
            <div class="detail-box-label">Department</div>
            <div class="detail-box-val">{{ aptDetail.department || 'N/A' }}</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;margin-bottom:20px" v-if="canCancelApt(aptDetail) || canRescheduleApt(aptDetail)">
          <button class="btn btn-danger" style="flex:1;justify-content:center" v-if="canCancelApt(aptDetail)" @click="doCancel(aptDetail.id)">
            <i class="bi bi-x-circle"></i> Cancel Appointment
          </button>
          <button class="btn btn-ghost" style="flex:1;justify-content:center" v-if="canRescheduleApt(aptDetail)" @click="openReschedule()">
            <i class="bi bi-arrow-repeat"></i> Reschedule
          </button>
        </div>
        <div class="info-alert" v-if="aptDetail.status_note" style="margin-bottom:14px">
          <div style="font-weight:700;margin-bottom:6px"><i class="bi bi-exclamation-circle"></i> Appointment Status</div>
          <div>{{ aptDetail.status_note }}</div>
        </div>
        <div class="info-alert">
          <div style="font-weight:700;margin-bottom:8px"><i class="bi bi-info-circle"></i> Important Information</div>
          <ul style="padding-left:18px">
            <li>Please arrive 15 minutes before your scheduled time</li>
            <li>Bring your ID and insurance card</li>
            <li>If you need to cancel, please do so at least 24 hours in advance</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- VIEW: PRESCRIPTIONS -->
    <div v-if="currentView === 'prescriptions'">
      <div class="card full">
        <div class="card-title">My Prescriptions</div>
        <div class="empty-state" v-if="prescriptions.length === 0">
          <i class="bi bi-prescription2"></i>No prescriptions found
        </div>
        <div class="apt-list" v-else>
          <div class="apt-row" v-for="p in prescriptions" :key="p.id" style="align-items:flex-start;flex-direction:column;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;width:100%">
              <div class="avatar" :class="avatarColor(p.doctor)">{{ (p.doctor || '?')[0] }}</div>
              <div class="apt-info">
                <div class="apt-name">{{ p.diagnosis }}</div>
                <div class="apt-meta">Dr. {{ p.doctor }} • Prescribed on {{ p.prescribed_on || 'N/A' }}</div>
              </div>
              <span class="apt-badge" :class="rxStatusClass(p.status)">{{ p.status }}</span>
            </div>
            <div style="width:100%;padding-left:44px">
              <div class="detail-box-label">Medicines</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">
                <span class="doc-spec" v-for="(m, i) in p.medications" :key="`${p.id}-${i}`">{{ m }}</span>
                <span class="apt-meta" v-if="!p.medications || p.medications.length === 0">No medicines listed</span>
              </div>
              <div class="apt-meta" v-if="p.instructions"><strong>Instructions:</strong> {{ p.instructions }}</div>
              <div class="apt-meta" v-if="p.follow_up_full"><strong>Follow-up:</strong> {{ p.follow_up_full }}</div>
              <div class="apt-meta" v-if="p.notes"><strong>Notes:</strong> {{ p.notes }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: MY DATA -->
    <div v-if="currentView === 'my-data'">
      <div class="stats-row" style="margin-bottom:20px">
        <div class="stat-tile"><div><div class="stat-value">{{ stats.total_visits ?? '—' }}</div><div class="stat-label">Total Visits</div></div><div class="stat-icon icon-blue"><i class="bi bi-calendar-check"></i></div></div>
        <div class="stat-tile"><div><div class="stat-value">{{ stats.upcoming ?? '—' }}</div><div class="stat-label">Upcoming</div></div><div class="stat-icon icon-amber"><i class="bi bi-activity"></i></div></div>
        <div class="stat-tile"><div><div class="stat-value">{{ stats.completed ?? '—' }}</div><div class="stat-label">Completed</div></div><div class="stat-icon icon-green"><i class="bi bi-clipboard2-pulse"></i></div></div>
        <div class="stat-tile"><div><div class="stat-value">{{ stats.cancelled ?? '—' }}</div><div class="stat-label">Cancelled</div></div><div class="stat-icon icon-red"><i class="bi bi-x-circle"></i></div></div>
      </div>
      <div class="card full">
        <div class="card-title">Download Your Complete Data</div>
        <p style="font-size:13px;color:var(--muted);margin-bottom:20px">Download your complete report including appointments, prescriptions, and personal profile details.</p>
        <div class="data-download-grid">
          <div class="download-card">
            <i class="bi bi-file-earmark-text" style="color:var(--green)"></i>
            <h4>Medical Report</h4>
            <p>Human-readable full report with appointments, prescriptions, and notes.</p>
            <button class="btn btn-primary" style="margin-top:4px" @click="handleDownload('text')">
              <i class="bi bi-download"></i> Download Report
            </button>
            <button class="btn btn-ghost" style="margin-top:8px" @click="handleDownload('pdf')">
              <i class="bi bi-filetype-pdf"></i> Download PDF
            </button>
          </div>
        </div>
      </div>
      <div class="card full">
        <div class="card-title">Personal Information</div>
        <div class="detail-grid">
          <div class="detail-box"><div class="detail-box-label">Full Name</div><div class="detail-box-val">{{ patient.name }}</div></div>
          <div class="detail-box"><div class="detail-box-label">Patient ID</div><div class="detail-box-val">{{ patient.patient_uid }}</div></div>
          <div class="detail-box"><div class="detail-box-label">Email</div><div class="detail-box-val">{{ patient.email }}</div></div>
          <div class="detail-box"><div class="detail-box-label">Gender</div><div class="detail-box-val">{{ patient.gender || 'N/A' }}</div></div>
        </div>
      </div>
    </div>
  </main>

  <!-- BOOK MODAL -->
  <div class="modal-overlay" :class="{ open: showBookModal }" @click.self="showBookModal = false">
    <div class="modal-box">
      <button class="modal-close" @click="showBookModal = false"><i class="bi bi-x"></i></button>
      <div class="modal-title">Book Appointment</div>
      <div v-if="bookDoctor" style="font-size:14px;font-weight:600;color:var(--blue);margin-bottom:16px">
        <i class="bi bi-person-badge"></i> {{ bookDoctor.name }}
      </div>
      <div class="form-group">
        <label class="form-label">Select Date</label>
        <input type="date" class="form-control" v-model="bookDate" :min="today" @change="loadSlots" />
      </div>
      <div class="form-group">
        <label class="form-label">Available Slots</label>
        <div v-if="dailyLimitReached" style="background:#fef2f2;border:1px solid #fecaca;color:#dc2626;border-radius:10px;padding:10px 14px;font-size:13px;margin-bottom:10px">
          <i class="bi bi-exclamation-circle"></i> Daily limit reached — <strong>{{ dailyCount }}/{{ dailyLimit }}</strong> appointments booked. No more bookings allowed today.
        </div>
        <div v-else-if="dailyCount > 0" style="background:#fffbeb;border:1px solid #fcd34d;color:#d97706;border-radius:10px;padding:8px 14px;font-size:12px;margin-bottom:10px">
          <i class="bi bi-info-circle"></i> <strong>{{ dailyCount }}/{{ dailyLimit }}</strong> appointments booked on this day.
        </div>
        <div class="slot-grid" v-if="slots.length > 0">
          <div
            class="slot-btn"
            v-for="s in slots" :key="s.slot"
            :class="{ taken: !s.available, selected: bookSlot === s.slot }"
            :title="s.available ? '' : slotReasonLabel(s.reason)"
            @click="s.available && selectBookSlot(s.slot)"
          >
            {{ s.slot }}{{ !s.available ? (s.reason === 'your_appointment' ? ' 🙋' : s.reason === 'daily_limit' ? ' 🚫' : ' ✗') : '' }}
          </div>
        </div>
        <p v-else style="color:var(--muted);font-size:13px">Pick a date first</p>
      </div>
      <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" @click="confirmBooking" :disabled="!bookDate || !bookSlot">
        <i class="bi bi-calendar-check"></i> Confirm Appointment
      </button>
    </div>
  </div>

  <!-- RESCHEDULE MODAL -->
  <div class="modal-overlay" :class="{ open: showReschedModal }" @click.self="showReschedModal = false">
    <div class="modal-box">
      <button class="modal-close" @click="showReschedModal = false"><i class="bi bi-x"></i></button>
      <div class="modal-title">Reschedule Appointment</div>
      <div class="form-group">
        <label class="form-label">New Date</label>
        <input type="date" class="form-control" v-model="reschedDate" :min="today" @change="loadReschedSlots" />
      </div>
      <div class="form-group">
        <label class="form-label">Available Slots</label>
        <div class="slot-grid" v-if="reschedSlots.length > 0">
          <div
            class="slot-btn"
            v-for="s in reschedSlots" :key="s.slot"
            :class="{ taken: !s.available, selected: reschedSlot === s.slot }"
            :title="s.available ? 'Available' : slotReasonLabel(s.reason)"
            @click="s.available && (reschedSlot = s.slot)"
          >
            {{ s.slot }}
          </div>
        </div>
        <p v-else style="color:var(--muted);font-size:13px">Pick a date first</p>
      </div>
      <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" @click="confirmReschedule" :disabled="!reschedDate || !reschedSlot">
        <i class="bi bi-arrow-repeat"></i> Reschedule
      </button>
    </div>
  </div>

  <!-- PROFILE MODAL -->
  <div class="modal-overlay" :class="{ open: showProfileModal }" @click.self="showProfileModal = false">
    <div class="modal-box">
      <button class="modal-close" @click="showProfileModal = false"><i class="bi bi-x"></i></button>
      <div class="modal-title">Patient Profile</div>
      <div style="text-align:center;margin-bottom:24px">
        <div class="avatar sm" style="width:64px;height:64px;font-size:26px;margin:0 auto 10px">{{ patientInitial }}</div>
        <div style="font-size:18px;font-weight:700">{{ patient.name }}</div>
        <div style="font-size:13px;color:var(--muted)">Patient ID: {{ patient.patient_uid }}</div>
      </div>
      <div class="detail-grid">
        <div class="detail-box"><div class="detail-box-label">Email</div><div class="detail-box-val">{{ patient.email }}</div></div>
        <div class="detail-box"><div class="detail-box-label">Gender</div><div class="detail-box-val">{{ patient.gender || 'N/A' }}</div></div>
        <div class="detail-box"><div class="detail-box-label">Patient UID</div><div class="detail-box-val">{{ patient.patient_uid }}</div></div>
      </div>
    </div>
  </div>
  <!-- EMAIL UPDATE MODAL -->
  <div class="modal-overlay" :class="{ open: showEmailModal }" @click.self="showEmailModal = false">
    <div class="modal-box">
      <button class="modal-close" @click="showEmailModal = false"><i class="bi bi-x"></i></button>
      <div class="modal-title">Update Email Address</div>
      <p style="font-size:13px;color:var(--muted);margin-bottom:20px">Please provide a valid email address to receive appointment reminders and medical reports.</p>
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" class="form-control" v-model="newEmail" placeholder="e.g. name@example.com" />
      </div>
      <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" @click="handleUpdateEmail" :disabled="!newEmail">
        Save Changes
      </button>
    </div>
  </div>

  <!-- TOAST -->
  <div class="toast" :class="{ show: toastVisible }">{{ toastMsg }}</div>
  </div>
</template>

<style scoped>
.dashboard-shell {
  --blue: #2563eb; --blue-lt: #eff6ff; --blue-dk: #1d4ed8;
  --green: #16a34a; --green-lt: #f0fdf4;
  --red: #dc2626; --red-lt: #fef2f2;
  --amber: #d97706; --amber-lt: #fffbeb;
  --purple: #7c3aed;
  --text: #0f172a; --muted: #64748b; --border: #e2e8f0;
  --bg: #f8fafc; --card: #ffffff; --sidebar-w: 220px;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
}

/* SIDEBAR */
.sidebar { width: var(--sidebar-w); background: var(--card); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 24px 0; position: fixed; top: 0; left: 0; height: 100vh; z-index: 100; }
.sidebar-logo { display: flex; align-items: center; gap: 10px; padding: 0 20px 28px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
.sidebar-logo .logo-icon { width: 34px; height: 34px; background: var(--blue); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; }
.sidebar-logo span { font-family: 'Sora', sans-serif; font-size: 15px; font-weight: 700; color: var(--text); }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 11px 20px; color: var(--muted); font-size: 14px; font-weight: 500; transition: all .18s; cursor: pointer; border: none; background: none; width: 100%; text-align: left; }
.nav-item:hover { background: var(--blue-lt); color: var(--blue); }
.nav-item.active { background: var(--blue-lt); color: var(--blue); border-left: 3px solid var(--blue); }
.nav-item i { font-size: 17px; width: 20px; }
.sidebar-bottom { margin-top: auto; padding: 16px 20px; border-top: 1px solid var(--border); }
.user-pill { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--bg); border-radius: 12px; cursor: pointer; }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--blue); color: white; font-weight: 700; font-size: 14px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.avatar.sm { width: 40px; height: 40px; font-size: 16px; }
.avatar.green { background: var(--green); }
.avatar.purple { background: var(--purple); }
.avatar.amber { background: var(--amber); }
.user-pill-info { flex: 1; overflow: hidden; }
.user-pill-name { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-pill-role { font-size: 11px; color: var(--muted); }

/* MAIN */
.main { margin-left: var(--sidebar-w); flex: 1; padding: 32px 36px; max-width: calc(100vw - var(--sidebar-w)); }
.topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }
.page-title { font-family: 'Sora', sans-serif; font-size: 22px; font-weight: 700; }
.page-sub { font-size: 13px; color: var(--muted); margin-top: 2px; }
.topbar-right { display: flex; align-items: center; gap: 20px; }

/* NOTIFICATIONS */
.notif-wrapper { position: relative; }
.notif-bell { width: 40px; height: 40px; border-radius: 12px; background: var(--card); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; cursor: pointer; position: relative; color: var(--muted); transition: all .2s; }
.notif-bell:hover { border-color: var(--blue); color: var(--blue); }
.notif-bell.has_new { color: var(--text); border-color: var(--blue-lt); background: var(--blue-lt); }
.notif-badge { position: absolute; top: -5px; right: -5px; background: var(--red); color: white; border-radius: 50%; min-width: 18px; height: 18px; font-size: 10px; font-weight: 700; display: flex; align-items: center; justify-content: center; border: 2px solid var(--bg); }

.notif-panel { position: absolute; top: 50px; right: 0; width: 340px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,.12); z-index: 1000; overflow: hidden; animation: slideDown .25s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

.notif-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.notif-header span { font-weight: 700; font-size: 14px; }
.btn-close-notif { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 18px; }

.notif-list { max-height: 400px; overflow-y: auto; }
.notif-empty { padding: 40px 20px; text-align: center; color: var(--muted); font-size: 13px; }

.notif-item { display: flex; gap: 12px; padding: 16px 20px; border-bottom: 1px solid var(--border); transition: background .2s; }
.notif-item:hover { background: var(--bg); }
.notif-item:last-child { border-bottom: none; }
.notif-icon { flex-shrink: 0; margin-top: 2px; font-size: 18px; }
.notif-item.success .notif-icon { color: var(--green); }
.notif-item.invalid_email .notif-icon { color: var(--amber); }
.notif-item.failed .notif-icon { color: var(--red); }

.notif-content { flex: 1; }
.notif-title { font-size: 13px; font-weight: 700; margin-bottom: 3px; }
.notif-msg { font-size: 12px; color: var(--muted); line-height: 1.5; }
.notif-time { font-size: 11px; color: var(--muted); margin-top: 6px; opacity: .7; }

/* CARDS */
.card { background: var(--card); border-radius: 16px; border: 1px solid var(--border); padding: 20px 24px; }
.card-title { font-family: 'Sora', sans-serif; font-size: 14px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .6px; margin-bottom: 16px; }

/* STATS */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-tile { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 20px 22px; display: flex; align-items: center; justify-content: space-between; transition: box-shadow .2s; }
.stat-tile:hover { box-shadow: 0 4px 20px rgba(0,0,0,.06); }
.stat-value { font-family: 'Sora', sans-serif; font-size: 30px; font-weight: 700; }
.stat-label { font-size: 13px; color: var(--muted); margin-top: 2px; }
.stat-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.icon-blue { background: var(--blue-lt); color: var(--blue); }
.icon-amber { background: var(--amber-lt); color: var(--amber); }
.icon-green { background: var(--green-lt); color: var(--green); }
.icon-red { background: var(--red-lt); color: var(--red); }

/* LAYOUT */
.two-col { display: grid; grid-template-columns: 1fr 380px; gap: 20px; margin-bottom: 20px; }
.full { margin-bottom: 20px; }

/* NEXT APT */
.next-apt-card { background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%); border-radius: 16px; padding: 24px 28px; color: white; position: relative; overflow: hidden; }
.next-apt-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; opacity: .8; margin-bottom: 16px; }
.next-apt-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.nap-item-label { font-size: 11px; opacity: .7; margin-bottom: 4px; }
.nap-item-val { font-size: 15px; font-weight: 600; }
.btn-view-apt { margin-top: 20px; background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.3); color: white; padding: 8px 20px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background .2s; text-decoration: none; display: inline-block; }
.btn-view-apt:hover { background: rgba(255,255,255,.25); }

/* REMINDERS */
.reminder-list { display: flex; flex-direction: column; gap: 10px; }
.reminder-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px; background: var(--amber-lt); border-left: 3px solid var(--amber); border-radius: 10px; font-size: 13px; }
.reminder-item i { color: var(--amber); margin-top: 1px; flex-shrink: 0; }

/* QUICK ACTIONS */
.qa-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.qa-tile { border: 1px solid var(--border); border-radius: 14px; padding: 22px 16px; text-align: center; cursor: pointer; transition: all .2s; background: var(--card); color: var(--text); display: block; }
.qa-tile:hover { border-color: var(--blue); box-shadow: 0 4px 16px rgba(37,99,235,.1); transform: translateY(-2px); }
.qa-icon { font-size: 28px; margin-bottom: 10px; display: block; }
.qa-label { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.qa-desc { font-size: 12px; color: var(--muted); }

/* APT LIST */
.apt-list { display: flex; flex-direction: column; gap: 0; }
.apt-row { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.apt-row:last-child { border-bottom: none; }
.apt-info { flex: 1; }
.apt-name { font-size: 14px; font-weight: 600; }
.apt-meta { font-size: 12px; color: var(--muted); margin-top: 2px; }
.apt-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.badge-booked { background: var(--blue-lt); color: var(--blue); }
.badge-completed { background: var(--green-lt); color: var(--green); }
.badge-warning { background: var(--amber-lt); color: #b45309; }
.badge-cancelled { background: var(--red-lt); color: var(--red); }

/* BUTTONS */
.btn { padding: 8px 18px; border-radius: 9px; font-size: 13px; font-weight: 600; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all .18s; }
.btn-primary { background: var(--blue); color: white; }
.btn-back { 
  background: transparent; 
  border: 1px solid var(--blue); 
  color: var(--blue); 
  padding: 6px 14px; 
  border-radius: 10px; 
  font-size: 13px; 
  font-weight: 600; 
  display: inline-flex; 
  align-items: center; 
  gap: 6px; 
  cursor: pointer; 
  transition: all .18s; 
}
.btn-back:hover { background: var(--blue-lt); }
.btn-back i { color: var(--blue); }
.btn-primary:hover { background: #1d4ed8; }
.btn-ghost { background: transparent; color: var(--blue); border: 1px solid var(--blue); }
.btn-ghost:hover { background: var(--blue-lt); }
.btn-danger { background: var(--red); color: white; }
.btn-danger:hover { background: #b91c1c; }
.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }

/* DOCTOR GRID */
.doctor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; }
.doctor-card { border: 1px solid var(--border); border-radius: 16px; padding: 22px; background: var(--card); text-align: center; transition: box-shadow .2s; }
.doctor-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,.08); }
.doc-spec { font-size: 12px; padding: 3px 10px; border-radius: 20px; background: var(--blue-lt); color: var(--blue); display: inline-block; margin: 6px 0 4px; }
.doc-avail { font-size: 12px; }
.doc-avail.ok { color: var(--green); }
.doc-avail.no { color: var(--red); }
.doc-meta { font-size: 12px; color: var(--muted); margin: 4px 0; }
.doc-actions { display: flex; gap: 8px; margin-top: 14px; }
.doc-actions .btn { flex: 1; justify-content: center; }

/* SEARCH BAR */
.search-bar { display: flex; gap: 10px; align-items: center; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 10px 16px; margin-bottom: 4px; }
.search-bar input, .search-bar select { border: none; outline: none; font-family: 'DM Sans', sans-serif; font-size: 14px; background: transparent; flex: 1; }
.search-bar select { max-width: 180px; color: var(--muted); }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.45); backdrop-filter: blur(4px); display: none; align-items: center; justify-content: center; z-index: 999; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card); border-radius: 20px; padding: 32px; width: 500px; max-width: 94vw; max-height: 90vh; overflow-y: auto; animation: zoomIn .2s ease; }
@keyframes zoomIn { from { opacity: 0; transform: scale(.95) } to { opacity: 1; transform: scale(1) } }
.modal-title { font-family: 'Sora', sans-serif; font-size: 18px; font-weight: 700; margin-bottom: 20px; }
.modal-close { float: right; background: none; border: none; font-size: 20px; cursor: pointer; color: var(--muted); }
.form-group { margin-bottom: 16px; }
.form-label { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; display: block; margin-bottom: 6px; }
.form-control { width: 100%; border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; font-family: 'DM Sans', sans-serif; font-size: 14px; outline: none; transition: border .2s; }
.form-control:focus { border-color: var(--blue); }

/* SLOTS */
.slot-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 8px; }
.slot-btn { padding: 8px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--card); cursor: pointer; text-align: center; transition: all .15s; }
.slot-btn:hover:not(.taken) { border-color: var(--blue); color: var(--blue); background: var(--blue-lt); }
.slot-btn.selected { background: var(--blue); color: white; border-color: var(--blue); }
.slot-btn.taken { opacity: .4; cursor: not-allowed; text-decoration: line-through; }

/* DETAIL */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
.detail-box { border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; }
.detail-box-label { font-size: 11px; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .5px; }
.detail-box-val { font-size: 15px; font-weight: 600; }
.detail-box-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.info-alert { background: var(--amber-lt); border: 1px solid #fcd34d; border-radius: 12px; padding: 16px 18px; font-size: 13px; }
.info-alert li { margin-bottom: 4px; }

/* TOAST */
.toast { position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%); background: #0f172a; color: white; padding: 12px 22px; border-radius: 10px; font-size: 14px; opacity: 0; transition: opacity .3s; pointer-events: none; z-index: 9999; }
.toast.show { opacity: 1; }

/* MISC */
.empty-state { text-align: center; padding: 48px 20px; color: var(--muted); }
.empty-state i { font-size: 48px; opacity: .3; display: block; margin-bottom: 12px; }
.data-download-grid { display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 24px; }
.download-card { border: 1px solid var(--border); border-radius: 16px; padding: 24px; display: flex; flex-direction: column; gap: 8px; }
.download-card i { font-size: 32px; }
.download-card h4 { font-size: 15px; font-weight: 700; }
.download-card p { font-size: 13px; color: var(--muted); flex: 1; }

@media (max-width: 1200px) {
  .two-col { grid-template-columns: 1fr; }
  .doctor-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 1024px) {
  .sidebar {
    position: static;
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
    padding: 14px 0;
  }
  .sidebar-logo { padding-bottom: 16px; margin-bottom: 10px; }
  .sidebar nav {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 0 12px;
  }
  .nav-item {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
  }
  .nav-item.active { border-left: 1px solid var(--blue); }
  .sidebar-bottom { border-top: none; }
  .main {
    margin-left: 0;
    max-width: 100%;
    padding: 24px 16px;
  }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .qa-grid { grid-template-columns: repeat(2, 1fr); }
  .data-download-grid,
  .detail-grid { grid-template-columns: 1fr; }
  .slot-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .main { padding: 16px 12px; }
  .sidebar nav { grid-template-columns: 1fr; }
  .stats-row,
  .qa-grid,
  .doctor-grid,
  .next-apt-grid { grid-template-columns: 1fr; }
}
</style>




