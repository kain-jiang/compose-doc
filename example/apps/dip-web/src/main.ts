import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import HomeView from "./views/HomeView.vue";


const router = createRouter({
  history: createWebHistory("/dip/"),
  routes: [
    {
      path: "/",
      component: HomeView,
    },
  ],
});


createApp(App).use(router).mount("#app");
