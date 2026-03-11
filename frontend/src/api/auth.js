import api from '@/services/interceptor'

export async function registerPatient(payload) {
  const res = await api.post('/auth/register', payload)
  return res.data
}

export async function forgotPassword(email) {
  const res = await api.post('/auth/forgot-password', { email })
  return res.data
}

export async function resetPassword(token, password) {
  const res = await api.post('/auth/reset-password', { token, password })
  return res.data
}

export async function loginUser(email, password) {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function me() {
  const res = await api.get('/auth/me')
  return res.data
}

export async function logoutUser() {
  const res = await api.post('/auth/logout')
  return res.data
}
