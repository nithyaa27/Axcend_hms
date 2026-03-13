import axios from 'axios'
import router from '@/router'

// When teammates open the frontend on another device, the browser must call
// the backend on this machine's LAN IP instead of that device's localhost.
const defaultBaseURL = ''

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultBaseURL,
  // withCredentials: true,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})


let sessionExpiredHandled = false
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const role = localStorage.getItem('role')

    if (
      err.response &&
      err.response.status === 401 &&
      role === 'patient' && // Added to scope session expiry to patients only
      !sessionExpiredHandled
    ) {
      sessionExpiredHandled = true
      const msg = err.response.data?.message === "session_expired" 
        ? "Your session has expired. Please login again." 
        : "Your session is invalid or has expired. Please login again."
      
      alert(msg)

      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('name')
      localStorage.removeItem('isLoggedIn')

      router.push('/login').catch(() => {
        window.location.href = '/login'
      })
    }

    return Promise.reject(err)
  }
)

export default api
