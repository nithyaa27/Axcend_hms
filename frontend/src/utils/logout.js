export function logout(router, message = "Logged out successfully") {
  localStorage.removeItem("token")
  localStorage.removeItem("role")
  alert(message)
  router.push("/")
}
