<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top shadow-sm">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/dashboard">
          <i class="bi bi-lightning-charge-fill me-2"></i>DataCoGlobal AI
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#userNavbar" aria-controls="userNavbar" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="userNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <router-link class="nav-link" active-class="active" to="/dashboard/chat"><i class="bi bi-chat-dots me-1"></i>Chat</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" active-class="active" to="/dashboard/documents"><i class="bi bi-file-earmark-text me-1"></i>Documents</router-link>
            </li>
          </ul>
          <ul class="navbar-nav">
            <li class="nav-item dropdown" ref="profileDropdownContainer"> 
              <a class="nav-link dropdown-toggle" href="#" id="userDropdownManual" role="button" @click.prevent="toggleProfileDropdown" :aria-expanded="isProfileDropdownOpen.toString()">
                <i class="bi bi-person-circle me-1"></i> {{ userEmail || 'Profile' }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" :class="{ 'show': isProfileDropdownOpen }" aria-labelledby="userDropdownManual">
                <li><router-link class="dropdown-item" to="/dashboard/profile" @click="handleDropdownItemClick"><i class="bi bi-person-lines-fill me-2"></i>View Profile</router-link></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="handleLogoutClick"><i class="bi bi-box-arrow-right me-2"></i>Logout</a></li>
              </ul>
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
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const userEmail = ref('');
const isProfileDropdownOpen = ref(false);
const profileDropdownContainer = ref(null);

const fetchUserData = async () => {
  try {
    const token = localStorage.getItem("token");
    if (token) {
      const response = await axios.get("http://127.0.0.1:8000/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      userEmail.value = response.data.email;
    }
  } catch (error) {
    console.error("Failed to fetch user data for navbar:", error);
    if (error.response && error.response.status === 401) logout();
  }
};

const toggleProfileDropdown = () => {
  isProfileDropdownOpen.value = !isProfileDropdownOpen.value;
};

const closeProfileDropdown = () => {
  isProfileDropdownOpen.value = false;
};

const handleDropdownItemClick = () => {
  closeProfileDropdown();
};

const handleLogoutClick = () => {
  logout();
  closeProfileDropdown(); 
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  router.push('/login');
};

const handleClickOutside = (event) => {
  if (profileDropdownContainer.value && !profileDropdownContainer.value.contains(event.target)) {
    if (isProfileDropdownOpen.value) { 
        closeProfileDropdown();
    }
  }
};

onMounted(() => {
  fetchUserData();
  document.addEventListener('click', handleClickOutside, true); 
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside, true);
});
</script>

<style scoped>
.navbar-brand { font-weight: 500; }

.dropdown-menu.show {
  display: block;
  position: absolute;

}

.dropdown-toggle::after {
  display: inline-block;
  margin-left: 0.255em;
  vertical-align: 0.255em;
  content: "";
  border-top: 0.3em solid;
  border-right: 0.3em solid transparent;
  border-bottom: 0;
  border-left: 0.3em solid transparent;
}
</style>