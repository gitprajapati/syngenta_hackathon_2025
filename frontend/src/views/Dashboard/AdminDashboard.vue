<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-8 col-xl-7">
        <div class="card shadow-sm border-0">
          <div class="card-header bg-dark text-white">
            <h3 class="mb-0 text-center">Register New User</h3>
          </div>
          <div class="card-body p-4">
            <form @submit.prevent="registerUser">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="regEmail" class="form-label">Email</label>
                  <input id="regEmail" v-model="form.email" type="email" class="form-control" required />
                </div>
                <div class="col-md-6 mb-3">
                  <label for="regPassword" class="form-label">Password</label>
                  <input id="regPassword" v-model="form.password" type="password" class="form-control" required />
                </div>
              </div>
              <div class="mb-3">
                <label for="regEmpId" class="form-label">Employee ID</label>
                <input id="regEmpId" v-model="form.employee_id" type="text" class="form-control" required />
              </div>
              <hr class="my-4">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="regRole" class="form-label">Role</label>
                  <select id="regRole" v-model="form.role_name" class="form-select" required>
                    <option value="" disabled>Select Role</option>
                    <option v-for="role in metadata.roles" :key="role" :value="role">{{ role }}</option>
                  </select>
                </div>
                <div class="col-md-6 mb-3">
                  <label for="regScope" class="form-label">Scope</label>
                  <select id="regScope" v-model="form.scope" class="form-select" required>
                    <option value="" disabled>Select Scope</option>
                    <option v-for="scope in metadata.scopes" :key="scope" :value="scope">{{ scope }}</option>
                  </select>
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="regRegion" class="form-label">Region</label>
                  <select id="regRegion" v-model="form.region_name" class="form-select" required>
                    <option value="" disabled>Select Region</option>
                    <option v-for="region in metadata.regions" :key="region" :value="region">{{ region }}</option>
                  </select>
                </div>
                <div class="col-md-6 mb-3">
                  <label for="regDept" class="form-label">Department</label>
                  <select id="regDept" v-model="form.department_name" class="form-select" required>
                    <option value="" disabled>Select Department</option>
                    <option v-for="department in metadata.departments" :key="department" :value="department">{{ department }}</option>
                  </select>
                </div>
              </div>
              <div class="d-grid mt-3">
                <button type="submit" class="btn btn-success btn-lg" :disabled="isLoading">
                   <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                   {{ isLoading ? 'Registering...' : 'Register User' }}
                </button>
              </div>
              <div v-if="successMessage" class="alert alert-success mt-3 py-2">{{ successMessage }}</div>
              <div v-if="errorMessage" class="alert alert-danger mt-3 py-2">{{ errorMessage }}</div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const form = ref({
  email: "", password: "", employee_id: "",
  role_name: "", scope: "", region_name: "", department_name: "",
});
const isLoading = ref(false);

const metadata = ref({
  roles:[
      "System Admin",
      "Department Manager",
      "Operations Supervisor",
      "Financial Analyst",
      "Compliance Officer",
      "Auditor",
      "Supplier Representative",
      "Data Engineer",
      "Team Lead",
      "Worker",
    ], scopes: ["Global", "Regional", "Departmental"],
  regions:  [
      "Canada",
      "Caribbean",
      "Central Africa",
      "Central America",
      "Central Asia",
      "East Africa",
      "East of USA",
      "Eastern Asia",
      "Eastern Europe",
      "North Africa",
      "Northern Europe",
      "Oceania",
      "South America",
      "South Asia",
      "South of USA",
      "Southeast Asia",
      "Southern Africa",
      "Southern Europe",
      "US Center",
      "West Africa",
      "West Asia",
      "West of USA",
      "Western Europe",
    ], departments:  [
      "Financial",
      "Operational",
      "Strategic",
      "Compliance",
      "Human Resources",
      "Information Technology",
    ],
});

const successMessage = ref("");
const errorMessage = ref("");

const registerUser = async () => {
  isLoading.value = true;
  successMessage.value = ""; errorMessage.value = "";
  try {
    const token = localStorage.getItem("token");
    await axios.post("http://127.0.0.1:8000/auth/register", form.value, {
      headers: { Authorization: `Bearer ${token}` },
    });
    successMessage.value = "User registered successfully!";
    form.value = { email: "", password: "", employee_id: "", role_name: "", scope: "", region_name: "", department_name: "" }; // Reset
    setTimeout(() => successMessage.value = "", 5000);
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || "Registration failed.";
    setTimeout(() => errorMessage.value = "", 5000);
  } finally {
    isLoading.value = false;
  }
};
</script>