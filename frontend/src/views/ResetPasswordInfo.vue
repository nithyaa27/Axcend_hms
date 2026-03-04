<template>
  <div class="container d-flex justify-content-center align-items-center min-vh-100 ff">
    <div class="card shadow p-4 text-center" style="max-width: 420px;">
      <h4 class="text-dark mb-3">Email Sent</h4>
      <p class="text-muted text-center">
        A password reset link has been sent to your registered email.
        Please check your inbox.
      </p>

      <router-link to="/" class="btn btn-dark mt-3">
        Back to Login
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: "ResetPasswordInfo"
}
</script>

<style scoped>
.ff{
  font-family: 'Poppins', sans-serif;
}
</style>