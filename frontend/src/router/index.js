// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import LoginPage from "@/views/LoginPage.vue";

// Layouts
import AdminLayout from "@/layouts/AdminLayout.vue";
import UserLayout from "@/layouts/UserLayout.vue";

// Views
import AdminDashboard from "@/views/Dashboard/AdminDashboard.vue"; 
import ChatPage from "@/views/Dashboard/ChatPage.vue";
import ProfilePage from "@/views/Dashboard/ProfilePage.vue";
import DocumentPage from "@/views/Dashboard/DocumentPage.vue";
import NotFoundPage from "@/views/NotFoundPage.vue";

const routes = [
  { path: "/login", name: "Login", component: LoginPage },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresAuth: true, allowedRoles: ["System Admin"] },
    children: [
      { path: "", name: "AdminDashboard", component: AdminDashboard },
    ],
  },
  {
    path: "/dashboard", 
    component: UserLayout,
    meta: { requiresAuth: true, allowedRoles: [
        "Department Manager", "Operations Supervisor", "Financial Analyst", 
        "Compliance Officer", "Auditor", "Supplier Representative", 
        "Data Engineer", "Team Lead", "Worker"
    ]},
    children: [
      { path: "", redirect: { name: "Chat" } }, 
      { path: "chat", name: "Chat", component: ChatPage },
      { path: "profile", name: "Profile", component: ProfilePage },
      { path: "documents", name: "Documents", component: DocumentPage },
    ],
  },
  {
    path: "/",
    redirect: () => {
      const role = localStorage.getItem("role");
      if (role === "System Admin") return "/admin";
      if (role) return "/dashboard"; 
      return "/login";
    },
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundPage },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL), 
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem("token");
  const userRole = localStorage.getItem("role");

  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      next({ name: "Login", query: { redirect: to.fullPath } });
    } else {
      if (to.meta.allowedRoles && !to.meta.allowedRoles.includes(userRole)) {
        next({ name: "NotFound" }); 
      } else {
        next(); 
      }
    }
  } else {
    next(); 
  }
});

export default router;