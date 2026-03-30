<script setup lang="ts">
import { onMounted, ref } from "vue";


type ApiResponse = {
  app: string;
  path: string;
  method: string;
  query: Record<string, string>;
  headers: Record<string, string>;
  body: string;
};

const loading = ref(false);
const error = ref("");
const response = ref<ApiResponse | null>(null);

async function loadDemo() {
  loading.value = true;
  error.value = "";

  try {
    const result = await fetch("/dip/api/demo?source=dip-web&lang=zh-CN", {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!result.ok) {
      throw new Error(`Request failed with status ${result.status}`);
    }

    response.value = (await result.json()) as ApiResponse;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadDemo();
});
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <p class="eyebrow">Vue 3 + Vite + TypeScript</p>
      <h1>DIP Frontend Demo</h1>
      <p class="lead">
        根路由固定在 <code>/dip</code>，页面直接通过
        <code>/dip/api</code> 访问 router-app API。
      </p>

      <div class="actions">
        <button type="button" @click="loadDemo" :disabled="loading">
          {{ loading ? "请求中..." : "重新请求 API" }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <pre v-else-if="response" class="payload">{{ JSON.stringify(response, null, 2) }}</pre>
      <p v-else class="empty">等待接口返回...</p>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #14213d;
  background:
    radial-gradient(circle at top left, rgba(244, 162, 97, 0.3), transparent 35%),
    linear-gradient(135deg, #f7ede2 0%, #f4f1de 45%, #dfe7fd 100%);
}

.page-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.hero-card {
  width: min(860px, 100%);
  padding: 32px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  box-shadow: 0 24px 80px rgba(20, 33, 61, 0.12);
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #ef476f;
}

h1 {
  margin: 0;
  font-size: clamp(36px, 6vw, 64px);
  line-height: 0.95;
}

.lead {
  margin: 18px 0 0;
  max-width: 52ch;
  font-size: 18px;
  line-height: 1.6;
}

.actions {
  margin-top: 24px;
}

button {
  padding: 12px 18px;
  border: 0;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  cursor: pointer;
  background: linear-gradient(135deg, #ef476f 0%, #f78c6b 100%);
  box-shadow: 0 12px 30px rgba(239, 71, 111, 0.28);
}

button:disabled {
  cursor: wait;
  opacity: 0.8;
}

code {
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.payload,
.empty,
.error {
  margin: 24px 0 0;
  padding: 18px;
  border-radius: 16px;
}

.payload {
  overflow: auto;
  font-size: 14px;
  line-height: 1.5;
  color: #f1faee;
  background: #1d3557;
}

.empty {
  color: #5c677d;
  background: rgba(255, 255, 255, 0.6);
}

.error {
  color: #8d0801;
  background: rgba(255, 209, 220, 0.75);
}
</style>
