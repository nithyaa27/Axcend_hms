<template>
  <div class="page-wrap">
    <div class="card-box">

      <!-- SUCCESS STATE -->
      <div v-if="success" class="success-view">
        <div class="success-icon">✅</div>
        <h2 class="success-title">Password Set Successfully!</h2>
        <p class="success-sub">Your doctor account is now secured. Redirecting you to login...</p>
        <div class="redirect-bar">
          <div class="redirect-fill"></div>
        </div>
        <p class="redirect-hint">Redirecting in 3 seconds…</p>
      </div>

      <!-- FORM STATE -->
      <div v-else>
        <div class="logo-wrap">
          <div class="logo-icon-container">
            <i class="bi bi-activity"></i>
          </div>
        </div>

        <h3 class="form-title">Set Your Password</h3>
        <p class="form-sub">Enter your new password below to secure your Doctor account.</p>

        <form @submit.prevent="setPassword" class="form-body">
          <div class="field">
            <label class="field-label">New Password</label>
            <div class="input-with-eye">
              <input
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password (min. 6 characters)"
                class="field-input"
                v-model="password"
                required
                minlength="6"
                :disabled="loading"
              />
              <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                <i class="bi" :class="showPassword ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
          </div>

          <div class="field">
            <label class="field-label">Confirm Password</label>
            <div class="input-with-eye">
              <input
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="Re-enter your password"
                class="field-input"
                v-model="confirmPassword"
                required
                minlength="6"
                :disabled="loading"
              />
              <button type="button" class="eye-btn" @click="showConfirmPassword = !showConfirmPassword">
                <i class="bi" :class="showConfirmPassword ? 'bi-eye-slash' : 'bi-eye'"></i>
              </button>
            </div>
          </div>

          <p v-if="error" class="error-msg">{{ error }}</p>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="loading">Setting Password…</span>
            <span v-else>Set Password</span>
          </button>
        </form>
      </div>

    </div>
  </div>
</template>

<script>
import api from "@/services/interceptor"

export default {
  name: "DoctorSetPassword",
  data() {
    return {
      password: "",
      confirmPassword: "",
      error: "",
      loading: false,
      success: false,
      showPassword: false,
      showConfirmPassword: false
    }
  },
  methods: {
    async setPassword() {
      this.error = ""

      if (this.password !== this.confirmPassword) {
        this.error = "Passwords do not match. Please try again."
        return
      }
      if (this.password.length < 6) {
        this.error = "Password must be at least 6 characters."
        return
      }

      this.loading = true
      const token = this.$route.params.token
      try {
        await api.post("/api/doctor/set-password", {
          token: token,
          password: this.password
        })
        this.success = true
        setTimeout(() => {
          this.$router.push("/login")
        }, 3000)
      } catch (err) {
        this.error = err.response?.data?.error || err.response?.data?.message || "Error setting password. The link may have expired."
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Segoe UI', sans-serif;
  padding: 20px;
}

.card-box {
  background: white;
  border-radius: 20px;
  padding: 48px 40px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
}

/* SUCCESS STATE */
.success-view {
  text-align: center;
  animation: fadeIn 0.4s ease-out;
}

.success-icon {
  font-size: 64px;
  margin-bottom: 16px;
  animation: pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.success-title {
  font-size: 22px;
  font-weight: 700;
  color: #16a34a;
  margin-bottom: 8px;
}

.success-sub {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
}

.redirect-bar {
  height: 4px;
  background: #dcfce7;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 8px;
}

.redirect-fill {
  height: 100%;
  background: #16a34a;
  width: 0%;
  border-radius: 99px;
  animation: fill 3s linear forwards;
}

.redirect-hint {
  font-size: 12px;
  color: #9ca3af;
}

/* FORM STATE */
.logo-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon-container {
  width: 54px;
  height: 54px;
  background: #2563eb;
  border-radius: 12px;
  display: flex !important;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
  margin: 0 auto;
}

.form-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 6px;
}

.form-sub {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 28px;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.field-input {
  padding: 12px 16px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  font-size: 15px;
  background: #f9fafb;
  transition: border-color 0.2s;
}

.field-input:focus {
  border-color: #2563eb;
  outline: none;
  background: white;
}

.field-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-with-eye {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-eye .field-input {
  width: 100%;
  padding-right: 46px;
}

.eye-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: color 0.2s;
}

.eye-btn:hover {
  color: #2563eb;
}

.error-msg {
  color: #dc2626;
  background: #fef2f2;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  text-align: center;
  font-weight: 500;
}

.submit-btn {
  background: #1d4ed8;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.submit-btn:hover:not(:disabled) {
  background: #1e40af;
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* ANIMATIONS */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes pop {
  from { transform: scale(0.5); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}

@keyframes fill {
  from { width: 0%; }
  to   { width: 100%; }
}
</style>
