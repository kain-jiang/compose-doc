# Docker Compose 部署标准说明

## 1. 文档目的

本文档用于在内部统一 Docker Compose 部署的理解与使用方式，明确其目标、边界、目录结构、组织方式和接入规范。

本文档主要面向内部各开发团队，同时可作为协作过程中的统一参考。

## 2. 文档定位

### 2.1 说明目标

本文档的目标如下：

- 建立统一的 Compose 部署标准。
- 支持核心业务服务、基础依赖服务和统一入口组件的模块化编排。
- 支持配置注入、密钥管理、数据持久化、服务互访和外部访问。
- 支持开发、测试、演示和小规模单机交付场景。

### 2.2 非目标范围

本文档不包含以下目标：

- 不追求与其他集群编排平台的能力完全等价。
- 不提供多节点调度、高可用、自动扩缩容和平台级自愈能力。
- 不替代生产级容器平台治理体系。
- 不覆盖服务治理、自动扩缩容、细粒度访问控制等集群能力。

## 3. 统一口径

统一原则如下：

- Compose 部署是独立的目标部署标准，不依赖其他编排平台的资源结构组织交付物。
- 各类服务应适配目标模型，不以历史部署形态反向定义目标结构。
- 优先保证可部署、可运行、可验证。
- 优先建立统一结构、统一规范、统一操作方式，再逐步扩展服务覆盖范围。

## 4. 适用范围

本文档所定义的部署标准适用于以下场景：

- 开发环境
- 测试环境
- 演示环境
- CI 临时验证环境
- 小规模单机交付场景

本文档所定义的部署标准不建议直接用于以下场景：

- 强依赖高可用和自动扩缩容的生产环境
- 多节点部署场景
- 强依赖复杂服务治理能力的场景
- 对隔离性、审计性、发布稳定性要求极高的场景

## 5. 标准架构

### 5.1 架构概述

标准架构为单机多容器部署架构。

服务部分统一分为以下两类：

- `core-services`
- `dip-services`

### 5.2 模块分层

本文档仅约定服务目录分层，不对模块职责做进一步展开说明。

### 5.3 K8s 到 Compose 的落地映射

在标准化过程中，应按目标部署模型重新组织交付物，而不是将 Kubernetes 资源逐条翻译为 Compose 字段。

内部统一按如下口径理解 `k8s -> compose`：

| Kubernetes 常见对象/能力 | Compose 对应落地方式 | 示例 |
| --- | --- | --- |
| `Namespace` | 不单独映射。通过单套 `compose.yml` 及其目录边界组织部署单元 | `example/compose.yml` 聚合整套部署 |
| `Deployment` | 一个长期运行的 `services.<name>` | `dip-services/dip-api.yml` 中的 `dip-api` |
| `StatefulSet` | 一个有状态 `service` 加命名卷或宿主机目录挂载 | `data-services/mysql.yml` 中的 `mysql + db-data` |
| `Job` / `Init Job` | 一次性运行服务，结合 `restart: "no"` 和依赖条件控制 | `dip-services/dip-db-init.yml` 中的 `dip-db-init` |
| `ConfigMap` | 优先映射为 `configs` 或文件挂载；简单键值也可映射为 `environment` / `env_file` | `dip-services/dip-api.yml` 中的 `dip-api-config` |
| `Secret` | 优先映射为宿主机只读文件挂载，或 Compose `secrets` | 本文档第 8 章统一约束 |
| `Service`（集群内访问） | 直接使用 Compose 服务名进行容器间访问 | `dip-api` 通过 `mysql` 访问数据库 |
| `Ingress` | 映射为统一入口代理服务，使用 `ports` 对外暴露 | `example/compose.yml` 中的 `gateway` |
| `readinessProbe` / `livenessProbe` | 优先映射为 `healthcheck`；业务侧仍需保留重试与容错 | `data-services/mysql.yml` 中的 `healthcheck` |
| `dependsOn` 类启动顺序诉求 | 使用 `depends_on`，必要时配合 `service_healthy`、`service_completed_successfully` | `dip-api` 依赖 `mysql` 与 `dip-db-init` |
| `PersistentVolumeClaim` | 命名卷或宿主机目录挂载 | `db-data:/var/lib/mysql` |
| 多副本与滚动发布 | 不作为 Compose 标准能力承诺，需在文档中明确降级处理 | 本文档第 11 章统一说明 |

需要特别强调的转换原则如下：

- Compose 映射的是“部署结果”，不是 Kubernetes 资源清单结构。
- 不保留 `Deployment`、`Service`、`Ingress` 三件套式目录组织。
- 不引入仅为贴近 Kubernetes 命名而存在的中间层抽象。
- 若某项 Kubernetes 能力在 Compose 中无等价能力，应明确降级，而不是伪造等价实现。

基于 `example` 中的示例，推荐按下面方式理解典型转换：

```text
K8s:
  Deployment(dip-api)
  Service(dip-api)
  ConfigMap(dip-api-config)
  Job(dip-db-init)
  Deployment(dip-web)
  Ingress(gateway)

Compose:
  compose.yml                 # 总装配与统一入口
  dip-services/dip-api.yml   # 长期运行业务服务
  dip-services/dip-db-init.yml # 一次性初始化任务
  dip-services/dip-web.yml   # 前端服务
  configs / environment      # 配置注入
  gateway service            # 统一外部入口
```

因此，服务从 Kubernetes 接入 Compose 时，整理顺序应为：

1. 先识别该服务在运行态上属于长期运行服务、一次性初始化任务，还是有状态依赖服务。
2. 再确定其配置注入、数据持久化、健康检查和外部暴露方式。
3. 最后按 `data-services`、`core-services`、`dip-services` 三层目录进行落盘，而不是按 Kubernetes 资源类型拆文件。

## 6. 标准目录结构

内部统一采用如下标准目录结构：

```text
deploy/
  compose.yml
  .env
  .env.example
  nginx.conf
  data-services/
    mysql.yml
    redis.yml
    kafka.yml
    opensearch.yml
  core-services/
    app1.yml
    app2.yml
    app3.yml
  dip-services/
    app1.yml
    app2.yml
  configs/
    common/
    app1/
    app2/
    app3/
  secrets/
    db/
    app/
  scripts/
    up.sh
    down.sh
    restart.sh
  docs/
    deployment.md
```

目录使用要求如下：

- 顶层 `compose.yml` 仅负责总装配，不堆叠全部服务细节。
- 每个子 YAML 文件只负责单个服务或一组强相关服务。
- 配置文件、密钥文件、脚本和文档独立于 Compose 文件管理。
- 目录结构应保持稳定，避免不同团队自行扩展出多套组织方式。

## 7. Compose 组织规范

### 7.1 总装配文件

顶层 `compose.yml` 用于聚合各模块，例如：

```yaml
include:
  - data-services/mysql.yml
  - data-services/redis.yml
  - data-services/kafka.yml
  - core-services/app1.yml
  - core-services/app2.yml
  - core-services/app3.yml
  - dip-services/app1.yml

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

### 7.2 子文件拆分原则

子文件拆分应遵循以下规则：

- 一个服务一个文件，或一组强耦合服务一个文件。
- 数据服务单独维护，不与业务服务混合。
- 业务服务仅区分为 `core-services` 与 `dip-services` 两类目录。
- 每个文件应尽量最小化，只保留本服务必要定义。

### 7.3 服务命名规范

服务命名应遵循以下原则：

- 名称稳定、可读、可用于内部 DNS 访问。
- 同一类服务命名方式保持一致，避免同义词混用。
- 尽量避免使用冗余后缀或含义不清的历史命名。
- 同一服务在配置文件、代理配置和文档中的名称保持一致。

## 8. 配置与密钥规范

### 8.1 配置分层

配置按以下方式分层管理：

- 通用环境变量：`.env`
- 服务级环境变量：`env_file`
- 结构化配置：文件挂载
- 密钥配置：独立文件挂载

### 8.2 配置使用原则

- 非敏感配置优先使用环境变量。
- 结构化配置优先采用挂载文件。
- 敏感配置不直接写入 Compose 文件。
- 配置变更应可追踪、可回滚。

### 8.3 密钥管理原则

密钥管理要求如下：

- 优先使用宿主机只读文件挂载。
- 密钥目录与普通配置目录分离。
- 文件权限应由宿主机操作系统控制。
- 若使用 Compose `secrets`，应将其视为组织方式，而不是平台级密钥管理替代品。

## 9. 网络与访问规范

### 9.1 内部访问

所有服务默认加入同一业务网络，并通过 Compose 服务名互访。

内部访问要求如下：

- 服务调用统一使用 Compose 服务名。
- 不依赖宿主机 IP 或固定容器 IP。
- 不使用额外约定的长域名格式。

### 9.2 外部访问

外部访问分为以下两种模式：

- 简单模式：服务直接通过 `ports` 暴露宿主机端口。
- 标准模式：统一通过 Nginx 作为反向代理入口。

内部默认采用统一入口模式，以减少宿主机暴露端口数量并统一路由规则管理。

### 9.3 启动依赖

启动依赖控制应遵循以下原则：

- `depends_on` 仅用于控制启动顺序。
- `depends_on` 不等价于依赖服务已就绪。
- 数据服务应配置 `healthcheck`。
- 业务服务应保留应用层重试或等待机制。

## 10. 存储规范

### 10.1 存储分类

存储按用途划分为以下两类：

- 命名卷
- 宿主机目录挂载

### 10.2 使用要求

- 数据库、缓存、消息中间件优先使用命名卷。
- 需要便于导入、导出或人工检查的数据，优先使用宿主机目录挂载。
- 所有有状态服务都必须明确数据目录、权限模型和初始化方式。

## 11. 运行约束

Compose 不具备平台级治理能力，因此内部统一按以下约束理解和使用：

- 服务默认按单实例运行
- 无自动扩缩容能力
- 无多节点高可用能力
- 无滚动发布和平台级回滚能力
- 无平台级访问控制和网络策略能力

因此，相关说明和操作规范中必须补足以下内容：

- 启动顺序
- 重启策略
- 发布步骤
- 故障排查入口

## 12. 服务接入规范

### 12.1 接入原则

各类服务接入标准化 Compose 部署时，应遵循以下原则：

- 服务必须归属到明确的分层目录。
- 服务名称、配置名称、挂载路径和入口规则应统一命名。
- 有状态服务必须先明确持久化方案，再进入标准编排。
- 对外暴露规则必须统一收敛，避免随意直接暴露宿主机端口。

### 12.2 服务接入清单

每个服务在接入前至少应补齐以下信息：

- 服务名称
- 镜像及版本
- 启动命令
- 容器端口
- 依赖服务
- 配置来源
- 密钥来源
- 挂载目录
- 健康检查方式
- 外部暴露方式
- 是否有状态
- 是否包含初始化动作

## 13. 落地检查项

标准化 Compose 部署在内部落地时，至少应满足以下检查项：

- 可通过 `docker compose config` 完成静态校验。
- 可通过 `docker compose up -d` 完成服务启动。
- 核心服务之间可正常互访。
- 统一入口可正常访问。
- 环境变量与配置文件注入正确。
- 关键数据目录具备持久化能力。
- 重启后服务可正常运行。
- 有明确的启动、停止和升级说明。

## 14. 输出内容

标准化部署至少应提供以下内容：

- `compose.yml`
- 子模块 Compose 文件
- `.env.example`
- `nginx.conf`
- 配置目录与密钥目录规范
- 启停脚本
- 部署说明文档
- 验证记录

## 15. 结论

本文档的核心是统一内部对 Compose 部署的理解与使用方式，形成清晰、稳定、可复用的部署标准。

在此基础上，系统内各类服务可按统一规则接入，形成适用于开发、测试、演示和单机交付场景的轻量化部署体系。
