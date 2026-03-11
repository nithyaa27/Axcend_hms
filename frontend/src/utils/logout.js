import { logoutUser } from '@/api/auth'

export async function logout(router, message = '') {
  try {
    await logoutUser()
  } catch (error) {
    // Ignore backend logout errors and clear local session anyway.
  }

  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('name')
  localStorage.removeItem('isLoggedIn')

  if (message) {
    alert(message)
  }

  router.push('/login')
}
