<template>
  <div class="container d-flex justify-content-center align-items-center min-vh-100 ff">
    <div class="card shadow-lg p-4" style="width: 100%; max-width: 420px;">
      <div class="text-center mb-4">
        <div class="logo-icon-container">
          <i class="bi bi-activity"></i>
        </div>
      </div>
      <h3 class="text-center text-dark mb-3">Reset Password</h3>

      <p class="text-muted text-center">
        Enter your new password below
      </p>

      <form @submit.prevent="reset">
        <div class="mb-3 password-wrap">
          <label class="form-label fw-semibold">New Password</label>
          <input
            :type="showPassword ? 'text' : 'password'"
            class="form-control input-soft"
            v-model="password"
            placeholder="Enter new password"
            required
          />
          <button type="button" class="toggle-eye" @click="showPassword = !showPassword">
            <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
          </button>
        </div>

        <div class="mb-3 password-wrap">
          <label class="form-label fw-semibold">Confirm Password</label>
          <input
            :type="showConfirmPassword ? 'text' : 'password'"
            class="form-control input-soft"
            v-model="confirmPassword"
            placeholder="Confirm new password"
            required
          />
          <button type="button" class="toggle-eye" @click="showConfirmPassword = !showConfirmPassword">
            <i :class="showConfirmPassword ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
          </button>
        </div>

        <button class="btn btn-dark w-100">
          Reset Password
        </button>
      </form>

      <div class="text-center mt-3">
        <router-link to="/" class="text-decoration-none">
          Back to Login
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  name: "ResetPassword",
  data() {
    return {
      password: "",
      confirmPassword: "",
      token: "",
      showPassword: false,
      showConfirmPassword: false
    }
  },
  mounted() {
    const encodedToken = this.$route.params.token
    this.token = decodeURIComponent(encodedToken)
  },
  methods: {
    reset() {
      if (this.password !== this.confirmPassword) {
        alert("Passwords do not match")
        return
      }

      api
        .post(`/auth/reset-password`, {
          token: this.token,
          password: this.password
        })
        .then(() => {
          alert("Password reset successfully")
          this.$router.push("/")
        })
        .catch(err => {
          alert(err.response?.data?.message || "Reset failed")
        })
    }
  }
}
</script>

<style scoped>
.ff{
  font-family: 'Poppins', sans-serif;
}
.input-soft {
  background-color: #f3f4f6;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
}
.password-wrap {
  position: relative;
}
.toggle-eye {
  position: absolute;
  right: 10px;
  top: 38px;
  border: none;
  background: transparent;
  cursor: pointer;
}
.form-control:focus {
  border-color: #9ca3af;
  box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.2);
}
input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px #eeefef inset !important;
  -webkit-text-fill-color: #000 !important;
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
