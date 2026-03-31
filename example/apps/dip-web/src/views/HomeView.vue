<script setup lang="ts">
import { computed, onMounted, ref } from "vue";


type MessageResponse = {
  app: string;
  database: string;
  count: number;
  messages: Array<{
    id: number;
    title: string;
    content: string;
    created_at: string;
  }>;
};

type DependencyItem = {
  status: string;
  detail?: string;
  database?: string;
  host?: string;
  port?: number;
  sample_key?: string;
  sample_value?: string | null;
  bootstrap_servers?: string;
  topic?: string;
  partition?: number;
  offset?: number;
  cluster_name?: string;
  version?: string;
  index?: string;
  document_id?: string;
  hit_count?: number;
  sample_document?: {
    app?: string;
    category?: string;
    message?: string;
  };
};

type DependencyResponse = {
  app: string;
  status?: string;
  dependencies: Record<string, DependencyItem>;
};

const loading = ref(false);
const error = ref("");
const messages = ref<MessageResponse | null>(null);
const dependencies = ref<DependencyResponse | null>(null);

const serviceCards = computed(() => {
  const items = dependencies.value?.dependencies ?? {};
  return [
    {
      key: "mysql",
      title: "MySQL",
      subtitle: "业务数据读取",
      lines: items.mysql?.status === "ok"
        ? [
            `数据库: ${items.mysql.database ?? "-"}`,
            `消息数据已接入 /api/dip-api/messages`,
          ]
        : [items.mysql?.detail ?? "等待接口返回"],
      status: items.mysql?.status ?? "unknown",
    },
    {
      key: "redis",
      title: "Redis",
      subtitle: "缓存读写测试",
      lines: items.redis?.status === "ok"
        ? [
            `地址: ${items.redis.host}:${items.redis.port}`,
            `示例 Key: ${items.redis.sample_key ?? "-"}`,
            `示例值: ${items.redis.sample_value ?? "-"}`,
          ]
        : [items.redis?.detail ?? "等待接口返回"],
      status: items.redis?.status ?? "unknown",
    },
    {
      key: "kafka",
      title: "Kafka",
      subtitle: "消息发送测试",
      lines: items.kafka?.status === "ok"
        ? [
            `Broker: ${items.kafka.bootstrap_servers ?? "-"}`,
            `Topic: ${items.kafka.topic ?? "-"}`,
            `分区/偏移: ${items.kafka.partition ?? "-"} / ${items.kafka.offset ?? "-"}`,
          ]
        : [items.kafka?.detail ?? "等待接口返回"],
      status: items.kafka?.status ?? "unknown",
    },
    {
      key: "opensearch",
      title: "OpenSearch",
      subtitle: "写入与检索测试",
      lines: items.opensearch?.status === "ok"
        ? [
            `集群: ${items.opensearch.cluster_name ?? "-"}`,
            `版本: ${items.opensearch.version ?? "-"}`,
            `索引: ${items.opensearch.index ?? "-"}`,
            `文档: ${items.opensearch.document_id ?? "-"}`,
            `命中数: ${items.opensearch.hit_count ?? "-"}`,
            `示例消息: ${items.opensearch.sample_document?.message ?? "-"}`,
          ]
        : [items.opensearch?.detail ?? "等待接口返回"],
      status: items.opensearch?.status ?? "unknown",
    },
  ];
});

const availableCount = computed(
  () => serviceCards.value.filter((item) => item.status === "ok").length,
);

async function loadDemo() {
  loading.value = true;
  error.value = "";

  try {
    const [messageResult, dependencyResult] = await Promise.all([
      fetch("/api/dip-api/messages"),
      fetch("/api/dip-api/dependencies"),
    ]);

    if (!messageResult.ok) {
      throw new Error(`/api/dip-api/messages returned ${messageResult.status}`);
    }

    if (!dependencyResult.ok) {
      throw new Error(`/api/dip-api/dependencies returned ${dependencyResult.status}`);
    }

    messages.value = (await messageResult.json()) as MessageResponse;
    dependencies.value = (await dependencyResult.json()) as DependencyResponse;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unknown error";
  } finally {
    loading.value = false;
  }
}

function statusLabel(status: string): string {
  if (status === "ok") {
    return "可用";
  }

  if (status === "error") {
    return "异常";
  }

  return "未知";
}

onMounted(() => {
  void loadDemo();
});
</script>

<template>
  <main class="page-shell">
    <section class="hero-card">
      <div class="hero-top">
        <div>
          <p class="eyebrow">Vue 3 + Vite + TypeScript</p>
          <h1>DIP Frontend Demo</h1>
        </div>

        <div class="summary-chip">
          <strong>{{ availableCount }}/4</strong>
          <span>依赖服务可用</span>
        </div>
      </div>

      <p class="lead">
        页面会同时请求 <code>/api/dip-api/messages</code> 和
        <code>/api/dip-api/dependencies</code>，把 MySQL、Redis、Kafka、
        OpenSearch 的实际连通结果直接展示出来。
      </p>

      <div class="actions">
        <button type="button" @click="loadDemo" :disabled="loading">
          {{ loading ? "正在检测..." : "重新检测服务" }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <section v-else class="panel-stack">
        <div class="service-grid">
          <article
            v-for="card in serviceCards"
            :key="card.key"
            class="service-card"
            :class="`service-card--${card.status}`"
          >
            <div class="service-header">
              <div>
                <h2>{{ card.title }}</h2>
                <p>{{ card.subtitle }}</p>
              </div>
              <span class="status-pill" :class="`status-pill--${card.status}`">
                {{ statusLabel(card.status) }}
              </span>
            </div>

            <ul class="service-lines">
              <li v-for="line in card.lines" :key="line">{{ line }}</li>
            </ul>
          </article>
        </div>

        <section class="payload-card">
          <div class="payload-header">
            <div>
              <p class="payload-kicker">MySQL Demo Data</p>
              <h2>初始化数据验证</h2>
            </div>
            <span v-if="messages" class="message-count">
              {{ messages.count }} 条记录
            </span>
          </div>

          <p v-if="!messages" class="empty">等待接口返回...</p>

          <div v-else class="message-list">
            <article
              v-for="message in messages.messages"
              :key="message.id"
              class="message-card"
            >
              <div class="message-meta">
                <strong>#{{ message.id }}</strong>
                <time>{{ message.created_at }}</time>
              </div>
              <h3>{{ message.title }}</h3>
              <p>{{ message.content }}</p>
            </article>
          </div>
        </section>
      </section>
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
  padding: 24px;
}

.hero-card {
  width: min(1180px, 100%);
  margin: 0 auto;
  padding: 32px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  box-shadow: 0 24px 80px rgba(20, 33, 61, 0.12);
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #ef476f;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  font-size: clamp(36px, 6vw, 64px);
  line-height: 0.95;
}

.summary-chip {
  min-width: 140px;
  padding: 16px 18px;
  border-radius: 20px;
  color: #ffffff;
  background: linear-gradient(135deg, #1d3557 0%, #457b9d 100%);
  box-shadow: 0 16px 40px rgba(29, 53, 87, 0.22);
}

.summary-chip strong {
  display: block;
  font-size: 32px;
  line-height: 1;
}

.summary-chip span {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.88;
}

.lead {
  margin-top: 18px;
  max-width: 62ch;
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

.panel-stack {
  margin-top: 28px;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.service-card,
.payload-card,
.error,
.empty {
  border-radius: 20px;
}

.service-card {
  padding: 20px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(255, 255, 255, 0.74);
}

.service-card--ok {
  background: linear-gradient(180deg, rgba(235, 255, 244, 0.96) 0%, rgba(255, 255, 255, 0.92) 100%);
}

.service-card--error {
  background: linear-gradient(180deg, rgba(255, 236, 238, 0.96) 0%, rgba(255, 255, 255, 0.92) 100%);
}

.service-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.service-header h2 {
  font-size: 24px;
}

.service-header p {
  margin-top: 6px;
  color: #5c677d;
}

.status-pill {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}

.status-pill--ok {
  color: #14532d;
  background: rgba(34, 197, 94, 0.16);
}

.status-pill--error {
  color: #991b1b;
  background: rgba(239, 68, 68, 0.14);
}

.status-pill--unknown {
  color: #475569;
  background: rgba(148, 163, 184, 0.16);
}

.service-lines {
  margin: 16px 0 0;
  padding-left: 18px;
  color: #243b53;
  line-height: 1.7;
}

.payload-card {
  margin-top: 20px;
  padding: 24px;
  color: #f1faee;
  background: #1d3557;
}

.payload-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.payload-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #f4a261;
}

.payload-header h2 {
  margin-top: 8px;
  font-size: 28px;
}

.message-count {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
}

.message-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.message-card {
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: rgba(241, 250, 238, 0.72);
  font-size: 13px;
}

.message-card h3 {
  font-size: 20px;
}

.message-card p {
  margin-top: 8px;
  line-height: 1.6;
}

.empty,
.error {
  margin-top: 24px;
  padding: 18px;
}

.empty {
  color: #dbe7f3;
  background: rgba(255, 255, 255, 0.08);
}

.error {
  color: #8d0801;
  background: rgba(255, 209, 220, 0.75);
}

@media (max-width: 900px) {
  .hero-top,
  .payload-header {
    flex-direction: column;
  }

  .service-grid,
  .message-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding: 16px;
  }

  .hero-card {
    padding: 24px;
  }

  h1 {
    line-height: 1.02;
  }
}
</style>
