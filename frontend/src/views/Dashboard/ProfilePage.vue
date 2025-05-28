<!-- src\views\Dashboard\ProfilePage.vue -->
<template>
  <div>
    <h4>User Profile</h4>
    <div v-if="profile">
      <ul class="list-group">
        <li class="list-group-item">
          <strong>Email:</strong> {{ profile.email }}
        </li>
        <li class="list-group-item">
          <strong>Employee ID:</strong> {{ profile.employee_id }}
        </li>
        <li class="list-group-item">
          <strong>Role:</strong> {{ profile.role }}
        </li>
        <li class="list-group-item">
          <strong>Department:</strong> {{ profile.department }}
        </li>
        <li class="list-group-item">
          <strong>Scope:</strong> {{ profile.scope }}
        </li>
        <li class="list-group-item">
          <strong>Region:</strong> {{ profile.region }}
        </li>
        <li class="list-group-item">
          <strong>Active:</strong> {{ profile.is_active }}
        </li>
        <li class="list-group-item">
          <strong>Last Login:</strong> {{ profile.last_login }}
        </li>
      </ul>
    </div>
    <div v-else>Loading...</div>
  </div>
</template>

<script>
  import axios from "axios";

  export default {
    name: "UserProfile",
    data() {
      return {
        profile: null,
      };
    },
    mounted() {
      this.fetchUserProfile();
    },
    methods: {
      async fetchUserProfile() {
        try {
          const token = localStorage.getItem("token");
          const { data } = await axios.get("http://127.0.0.1:8000/auth/me", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          this.profile = data;
        } catch (error) {
          console.error("Failed to fetch profile", error);
        }
      },
    },
  };
</script>
