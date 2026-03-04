<template>
  <div class="container mt-5">
    <h3>Patient Dashboard</h3>

    <button class="btn btn-danger mt-3" @click="manualLogout">
      Logout
    </button>
  </div>
</template>

<script>
import api from "@/services/interceptor"
import { logout } from "@/utils/logout"

export default {
  mounted() {
    /* Check session on page load */
    api.get("/auth/me")
  },
  methods: {
    manualLogout() {
      logout(this.$router)
    }
  }
}
</script>
