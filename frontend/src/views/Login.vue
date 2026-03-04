<template>
  <div class="container-fluid min-vh-100 d-flex align-items-center justify-content-center  ff">
    <div class="card p-4" style="width: 450px;height:500px ">
      
      
      <div class="text-center">
        <img 
        src="@/assets/logo.jpg" 
        alt="Logo"
        class="img-fluid"
        style="width:50px; height:auto;"
        />
      </div>


      <h3 class="text-center text-dark fw-bolder mb-3"> Hospital Management System</h3>
      <p class="text-secondary text-center">Sign in to your account to continue</p>
      
      <form @submit.prevent="login">
        <!-- Email -->
        <div class="mb-3">
          <label class="form-label fw-semibold">Email</label>
          <input
            type="email"
            placeholder="Enter your Email"
            class="form-control  input-soft border custom-input"
            v-model="email"
            required
          />
        </div>

        <!-- Password -->
        <div class="mb-1 d-flex justify-content-between">
          <label class="form-label fw-semibold">Password</label>
        <router-link to="/forgot" class="text-decoration-none ">Forgot Password?</router-link>
        </div>
         <div class="mb-4">
          <input
            type="password"
            placeholder="Enter your Password"
            class="form-control form-control-lg input-soft border"
            v-model="password"
            required
          />
        </div>

        <!-- Login Button -->
        <button type="submit" class="btn btn-dark w-100 btn-lg ">
          Sign In
        </button>
      </form>
      <div class="divider my-3 text-center text-muted">
        <span>Or continue with</span>
      </div>
      <!-- register -->
      <p class="text-center">
        Don’t have an account?
        <router-link to="/register" class=" text-decoration-none fw-semibold">
          Register as Patient
        </router-link>
      </p>
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
      password: ""
    }
  },
  methods: {
    login() {
      api
        .post("/auth/login", {
          email: this.email,
          password: this.password
        })
        .then(res => {
          // Save session
          localStorage.setItem("token", res.data.token)
          localStorage.setItem("role", res.data.role)

          // Role-based redirect
          if (res.data.role === "admin") {
            this.$router.push("/admin")
          } else if (res.data.role === "doctor") {
            this.$router.push("/doctor")
          } else {
            this.$router.push("/patient")
          }
        })
        .catch(err => {
          if (err.response && err.response.status === 401) {
            alert("Invalid email or password")
          } else {
            alert("Server error. Try again.")
          }
        })
    }
  }
}
</script>

<style scoped>

.input-soft::placeholder {
  color: #a8a7a7;
  font-size: 16px;
}

.input-soft {
  background-color: #f3f4f6;
  border: none;
  border-radius: 10px;
  padding: 11px 13px;
  border-color:
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
</style>
