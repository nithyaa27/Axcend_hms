import api from '@/services/interceptor'

/**
 * API Service Module
 * ------------------
 * Centralized service for all patient-related API interactions.
 * Handles authentication headers automatically via interceptors.
 */

const API_BASE = (api.defaults.baseURL || '').replace(/\/$/, '')

export async function getDashboardData() {
  const res = await api.get('/api/dashboard_data')
  return res.data
}

export async function getAppointments(tab = 'upcoming') {
  const res = await api.get(`/api/appointments?tab=${tab}`)
  return res.data
}

export async function getAppointmentDetail(aptId) {
  const res = await api.get(`/api/appointments/${aptId}`)
  return res.data
}

export async function bookAppointment(doctorId, date, timeSlot) {
  const res = await api.post('/api/appointments', {
    doctor_id: doctorId,
    date,
    time_slot: timeSlot
  })
  return res.data
}

export async function cancelAppointment(aptId) {
  const res = await api.post(`/api/appointments/${aptId}/cancel`)
  return res.data
}

export async function rescheduleAppointment(aptId, date, timeSlot) {
  const res = await api.put(`/api/appointments/${aptId}/reschedule`, {
    date,
    time_slot: timeSlot
  })
  return res.data
}

export async function getDoctors(params = {}) {
  const res = await api.get('/api/doctors', { params })
  return res.data
}

export async function getDoctorSlots(doctorId, date) {
  const res = await api.get(`/api/doctors/${doctorId}/slots`, { params: { date } })
  return res.data
}

export async function getPrescriptions() {
  const res = await api.get('/api/prescriptions')
  return res.data
}

export async function getPrescriptionDetail(prescriptionId) {
  const res = await api.get(`/api/prescriptions/${prescriptionId}`)
  return res.data
}

export async function downloadReport() {
  const res = await api.get('/api/download_report', { responseType: 'blob' })
  _triggerDownload(res)
}

export async function downloadReportPdf() {
  const res = await api.get('/api/download_report_pdf', { responseType: 'blob' })
  _triggerDownload(res)
}

function _triggerDownload(res) {
  const blob = new Blob([res.data], { type: res.headers['content-type'] })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  
  const contentDisposition = res.headers['content-disposition']
  let filename = ''
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/i)
    if (filenameMatch && filenameMatch.length > 1) {
      filename = filenameMatch[1]
    }
  }
  
  if (!filename) {
    const contentType = res.headers['content-type']
    filename = 'Medical_Report'
    if (contentType === 'application/pdf') filename += '.pdf'
    else filename += '.txt'
  }

  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export async function getNotifications() {
  const res = await api.get('/api/notifications')
  return res.data
}

export async function updatePatientEmail(email) {
  const res = await api.put('/api/profile/email', { email })
  return res.data
}

export default api
