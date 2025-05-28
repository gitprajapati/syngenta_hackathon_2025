<!-- src\views\Dashboard\UserDashboard.vue -->
<template>
  <div class="container mt-4">
    <h2 class="text-center">User Dashboard</h2>
    <div class="btn-group mb-4 w-100" role="group">
      <router-link class="btn btn-outline-primary" to="/chat">Chat</router-link>
      <router-link class="btn btn-outline-primary" to="/profile"
        >Profile</router-link
      >
      <router-link class="btn btn-outline-primary" to="/documents"
        >Documents</router-link
      >
      <button @click="logout" class="btn btn-outline-danger mt-3">
        Logout
      </button>
    </div>

    <router-view />
  </div>
</template>

<script>
  export default {
    methods: {
      logout() {
        localStorage.removeItem("token");
        window.location.href = "/login";
      },
    },
  };
</script>
