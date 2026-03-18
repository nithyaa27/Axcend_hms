<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center ff">
    <div class="card p-4" style="width: 450px;height:500px ">
      <div class="text-center mb-4">
        <div class="logo-icon-container">
          <i class="bi bi-activity"></i>
        </div>
      </div>

      <h3 class="text-center text-dark fw-bolder mb-3">Hospital Management System</h3>
      <p class="text-secondary text-center">Sign in to your account to continue</p>

      <form @submit.prevent="login">
        <div class="mb-3">
          <label class="form-label fw-semibold">Email</label>
          <input
            type="email"
            placeholder="Enter your Email"
            class="form-control input-soft border custom-input"
            v-model="email"
            required
          />
        </div>

        <div class="mb-1 d-flex justify-content-between">
          <label class="form-label fw-semibold">Password</label>
          <router-link to="/forgot" class="text-decoration-none">Forgot Password?</router-link>
        </div>
        <div class="mb-4 password-wrap">
          <input
            :type="showPassword ? 'text' : 'password'"
            placeholder="Enter your Password"
            class="form-control form-control-lg input-soft border"
            v-model="password"
            required
          />
          <button type="button" class="toggle-eye" @click="showPassword = !showPassword">
            <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
          </button>
        </div>

        <button type="submit" class="btn btn-dark w-100 btn-lg">
          Sign In
        </button>
      </form>

      <div class="divider my-3 text-center text-muted">
        <span>Or continue with</span>
      </div>

      <p class="text-center">
        Don’t have an account?
        <router-link to="/register" class="text-decoration-none fw-semibold">
          Register as Patient
        </router-link>
      </p>

      <p v-if="error" class="text-danger text-center mt-1">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  name: "Login",
  data() {
    return {
      email: "",
      password: "",
      showPassword: false,
      error: ""
    }
  },
  methods: {
    login() {
      this.error = ""
      api
        .post("/auth/login", {
          email: this.email,
          password: this.password
        })
        .then(res => {
          localStorage.setItem("token", res.data.token || "")
          localStorage.setItem("role", res.data.role || "patient")
          localStorage.setItem("name", res.data.name || "")
          localStorage.setItem("userId", res.data.id || "")
          localStorage.setItem("doctorId", res.data.doctor_id || "")
          localStorage.setItem("isLoggedIn", "true")

          if (res.data.redirect_to) {
            this.$router.push(res.data.redirect_to)
          } else if (res.data.role === "admin") {
            this.$router.push("/admin")
          } else if (res.data.role === "doctor") {
            this.$router.push("/doctor")
          } else {
            this.$router.push("/patient")
          }
        })
        .catch(err => {
          if (err.response && err.response.status === 401) {
            this.error = "Invalid email or password"
          } else if (!err.response) {
            this.error = "Backend is not reachable. Start backend on port 5000."
          } else {
            this.error = err.response?.data?.message || err.response?.data?.error || "Server error. Try again."
          }
        })
    }
  }
}
</script>

<style scoped>
.ff{
  font-family: 'Poppins', sans-serif;
}
.input-soft::placeholder {
  color: #a8a7a7;
  font-size: 16px;
}
.input-soft {
  background-color: #f3f4f6;
  border: none;
  border-radius: 10px;
  padding: 11px 13px;
}
.password-wrap {
  position: relative;
}
.toggle-eye {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  cursor: pointer;
  color: #6b7280;
  font-size: 18px;
  padding: 4px;
  z-index: 10;
}

/* Hide browser's native password reveal icon (Edge / IE / Chrome) */
input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear,
input[type="password"]::-webkit-contacts-auto-fill-button,
input[type="password"]::-webkit-credentials-auto-fill-button {
  display: none !important;
  pointer-events: none;
}
.form-control:focus {
  border-color: #9ca3af;
  box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.2);
}
input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px #eeefef inset !important;
  -webkit-text-fill-color: #000 !important;
}
.divider {
  position: relative;
}
.logo-icon-container {
  width: 50px;
  height: 50px;
  background: #2563eb;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 26px;
  margin: 0 auto;
}
</style>
