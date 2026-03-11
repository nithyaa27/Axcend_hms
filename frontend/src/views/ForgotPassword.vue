<template>
  <div class="container d-flex justify-content-center align-items-center min-vh-100 ff">
    <div class="card shadow-lg p-4" style="width: 100%; max-width: 420px;">
      <div class="text-center mb-4">
        <div class="logo-icon-container">
          <i class="bi bi-activity"></i>
        </div>
      </div>
      <h3 class="text-center text-dark mb-3">Forgot Password?</h3>

      <p class="text-muted text-center">
        No worries! Enter your email and we'll send you a reset password link.
      </p>

      <form @submit.prevent="submit">
        <div class="mb-3">
          <label class="form-label fw-semibold">Email Address</label>
          <input
            type="email"
            class="form-control input-soft border"
            v-model="email"
            placeholder="Enter your email"
            required
          />
        </div>

        <button class="btn btn-dark w-100">
          Send Reset Link
        </button>
      </form>

      <div class="text-center mt-3">
        <router-link to="/" class="text-decoration-none fw-semibold">
          &larr; Back to Login
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  name: "ForgotPassword",
  data() {
    return {
      email: ""
    }
  },
  methods: {
    submit() {
      api
        .post("/auth/forgot-password", { email: this.email })
        .then(() => {
          this.$router.push("/reset-info")
        })
        .catch(err => {
          if (err.response && err.response.status === 408) {
            alert("Network error: Could not send request. Please check your connection.")
          } else if (err.response && err.response.status === 500) {
            alert("Server error: Unable to send reset link, try again later")
          } else {
            alert(err.response?.data?.message || "Unable to process request")
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
.input-soft {
  background-color: #f3f4f6;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
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
