<template>
  <div class="d-flex align-items-center justify-content-center min-vh-100 bg-light">
    <div class="container" style="max-width: 400px;">
      <div class="card shadow-lg border-0 rounded-3">
        <div class="card-body p-4 p-sm-5">
          <div class="text-center mb-4">
       
            <h2 class="card-title fw-bold mt-2">User Login</h2>
          </div>
          <form @submit.prevent="loginUser">
            <div class="form-floating mb-3">
              <input v-model="email" type="email" class="form-control" id="loginEmail" placeholder="name@example.com" required />
              <label for="loginEmail">Email address</label>
            </div>
            <div class="form-floating mb-3">
              <input v-model="password" type="password" class="form-control" id="loginPassword" placeholder="Password" required />
              <label for="loginPassword">Password</label>
            </div>
            <div class="d-grid">
              <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                {{ isLoading ? 'Logging in...' : 'Login' }}
              </button>
            </div>
            <div v-if="error" class="alert alert-danger mt-3 py-2">{{ error }}</div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";
import { useRouter, useRoute } from "vue-router";

const email = ref("");
const password = ref("");
const error = ref("");
const isLoading = ref(false);
const router = useRouter();
const route = useRoute();

const loginUser = async () => { 
  isLoading.value = true;
  error.value = "";
  try {
    const formData = new URLSearchParams();
    formData.append('username', email.value); 
    formData.append('password', password.value);

    const response = await axios.post("http://127.0.0.1:8000/auth/login", formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    const { access_token, role, token_type } = response.data; 

    localStorage.setItem("token", access_token);
    localStorage.setItem("token_type", token_type);

    let userRole = "";
    if (typeof role === 'object' && role !== null && 'role' in role) {
        userRole = role.role; 
    } else if (typeof role === 'string') {
        userRole = role;
    } else {
        console.error("Unexpected role format:", role);
        error.value = "Login successful, but role information is missing or malformed.";
        isLoading.value = false;
        return;
    }
    localStorage.setItem("role", userRole);

    if (route.query.redirect) {
      router.push(route.query.redirect);
    } else {
      if (userRole === "System Admin") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Invalid email or password";
    console.error("Login error:", err);
  } finally {
    isLoading.value = false;
  }
};
</script>
<style scoped> .min-vh-100 { min-height: 100vh; } </style>