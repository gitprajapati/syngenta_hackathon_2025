<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top shadow-sm">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/admin">
          <i class="bi bi-shield-lock-fill me-2"></i>Admin Panel
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#adminNavbar" aria-controls="adminNavbar" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="adminNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
               <router-link class="nav-link" active-class="active" to="/admin"><i class="bi bi-person-plus-fill me-1"></i>User Registration</router-link>
            </li>
          </ul>
           <ul class="navbar-nav">
            <li class="nav-item">
              <button @click="logout" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-right me-1"></i>Logout</button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <main class="container-fluid" style="padding-top: 70px;">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
const router = useRouter();
const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  router.push('/login');
};
</script>
<style scoped> .navbar-brand { font-weight: 500; } </style>