<template>
  <div class="container d-flex justify-content-center align-items-center min-vh-100 ff">
    <div class="card shadow-lg p-4" style="width: 100%; max-width: 420px;">
      <h3 class="text-center text-dark mb-3">Reset Password</h3>

      <p class="text-muted text-center">
        Enter your new password below
      </p>

      <form @submit.prevent="reset">
        <!-- New Password -->
        <div class="mb-3">
          <label class="form-label fw-semibold">New Password</label>
          <input
            type="password"
            class="form-control input-soft"
            v-model="password"
            placeholder="Enter new password"
            required
          />
        </div>

        <!-- Confirm Password -->
        <div class="mb-3">
          <label class="form-label fw-semibold">Confirm Password</label>
          <input
            type="password"
            class="form-control input-soft"
            v-model="confirmPassword"
            placeholder="Confirm new password"
            required
          />
        </div>

        <button class="btn btn-dark w-100">
          Reset Password
        </button>
      </form>

      <div class="text-center mt-3">
        <router-link to="/" class="text-decoration-none ">
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
      token: ""
    }
  },
  mounted() {
    // Get the token from the URL and decode it
    const encodedToken = this.$route.params.token
    this.token = decodeURIComponent(encodedToken)  // Decode URL-encoded token
  },
  methods: {
    reset() {
      if (this.password !== this.confirmPassword) {
        alert("Passwords do not match")
        return
      }

      // Send POST request to backend
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


<style  scoped>
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
</style>