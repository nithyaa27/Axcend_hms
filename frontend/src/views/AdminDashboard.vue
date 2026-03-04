<template>
  <div class="container mt-5">
    <h3>Admin Dashboard</h3>

    <button class="btn btn-danger mt-3" @click="logoutUser">
      Logout
    </button>
  </div>
</template>

<script>
import { logout } from "@/utils/logout"

export default {
  methods: {
    logoutUser() {
      logout(this.$router)
    }
  }
}
</script>
