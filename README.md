# AI 智能销售 ERP 系统

一个面向销售业务场景的 **AI-ERP 演示项目**。项目将 AI 能力嵌入到客户、订单、看板、知识检索等业务页面中，强调“业务闭环 + 数据展示 + AI 辅助决策”，而不是只做一个聊天窗口。

---

## 项目简介

本项目是一个基于 `Vue3 + TypeScript + Naive UI + FastAPI` 的后台管理系统，围绕销售流程搭建了客户管理、商品管理、订单管理、经营看板和知识库助手。

相比普通 CRUD 后台，当前版本的重点是：
- AI 结果以结构化卡片方式落在业务页面中（客户、订单、看板）
- 支持订单状态流转、客户跟进闭环、库存风险识别等业务语义
- 提供独立的知识库助手页面，并落地最小可用 RAG 检索问答链路

---

## 项目亮点

1. **AI 嵌入业务页面**：客户详情、订单详情、Dashboard 内均有结构化 AI 分析入口与结果展示。  
2. **Dashboard 经营看板**：包含指标卡、趋势图、分布图、Top 商品、风险/待办提醒。  
3. **客户跟进闭环**：客户列表 -> 客户详情 -> 跟进记录 CRUD -> AI 建议/总结 -> 操作记录。  
4. **订单状态流转 + 业务操作**：支持确认付款/发货/完成/取消等条件化操作。  
5. **商品库存业务表达**：库存状态（缺货/低库存/正常）与上下架、库存调整联动。  
6. **结构化 AI 输出**：不是长文本聊天，支持摘要、分项、状态、时间、复制。  
7. **本地持久化增强演示完整性**：Dashboard、客户详情、订单详情的 AI 结果与操作记录支持刷新后回显。  
8. **多模块联动**：看板可跳转客户/订单/商品；列表与详情关键字段和状态保持联动展示。  
9. **独立知识库助手模块**：不是聊天窗口，保留“问答 + 依据 + 命中文档 + 命中片段”的知识工作台形态。  
10. **最小可用 RAG 链路**：文档读取、切分、向量化、检索、生成、证据返回全链路可运行。

---

## 功能模块

## 1) Dashboard（经营看板）
- 核心指标卡：客户总数、商品总数、订单总数、销售总额、范围新增客户、待处理订单。  
- 时间范围切换：近 7 天 / 近 30 天 / 本月。  
- 图表分析：销售趋势、订单状态分布、客户等级分布、热销商品 Top5（ECharts）。  
- 业务提醒：低库存商品、风险订单、待跟进客户。  
- AI 经营助手：销售分析、风险概览、客户经营建议、库存建议（结构化卡片）。  
- 支持刷新聚合数据与 AI 结果按时间范围本地持久化。

## 2) 客户管理
- 客户列表：关键词、等级、状态、来源、负责人、时间范围等筛选。  
- 客户维护：新增/编辑/删除，表单分组与校验增强。  
- 客户详情：概览卡（等级、状态、最近跟进、跟进次数等）+ 基础信息。  
- 跟进记录：列表/筛选/分页 + 新增/编辑/删除。  
- AI 能力：AI 跟进建议、AI 跟进总结，支持生成/重生成/复制。  
- 关联订单：轻量统计 + 最近订单列表。  
- 操作记录：记录关键操作并支持本地持久化回显。

## 3) 商品管理
- 商品列表：关键词、分类、状态、库存状态、创建时间、价格区间筛选。  
- 字段表达增强：库存数量 + 库存状态（缺货/低库存/正常）。  
- 行内操作：详情、编辑、上架/下架、调整库存、删除。  
- 批量能力：批量上架、批量下架、批量删除。  
- 新增/编辑弹窗：字段分组、校验规则（编码、价格、库存、单位、状态等）。  
- 详情弹窗：核心信息突出 + 库存风险提示 + 轻量业务信息（演示聚合）。

## 4) 订单管理
- 列表筛选：订单状态、时间范围、客户/订单号、金额区间等。  
- 列表字段增强：支付状态、发货状态、商品总件数、更新时间、风险标记。  
- 操作区增强：详情、编辑、删除、更多操作（确认付款/发货/完成/取消/AI 分析）。  
- 批量能力：多选、批量删除、批量导出（前端 CSV）、批量 AI 分析。  
- 详情页：状态流转、支付/发货/收货信息、AI 分析模块、金额汇总、操作记录。  
- 与运行态联动：订单运行态（支付/发货/风险）在列表与详情展示保持一致。

## 5) 知识库助手（RAG）
- 独立页面（非聊天窗口）：问题输入、TopK、提问、重建索引。  
- 回答区：简要答案 + 依据说明（核心依据文档/其他命中文档/相关度信息）。  
- 证据区：命中文档、命中知识片段（支持轻量 Markdown、折叠展开）。  
- 联动交互：点击命中文档可筛选片段。  
- 文档区：展示知识库文档列表及更新时间。  
- 后端接口：`/api/knowledge-base/documents`、`/rebuild`、`/ask`。

---

## AI 能力说明

当前 AI 能力均以“**结构化结果卡片**”方式呈现，不是普通聊天窗口。

- 客户详情：
  - AI 跟进建议（客户状态、下一步动作、推荐话术、风险提醒）
  - AI 跟进总结（历史摘要、关注点、成交可能性、阻塞点、后续建议）
- 订单详情：
  - AI 分析订单
  - AI 风险检测
  - AI 销售建议
- Dashboard：
  - AI 销售分析
  - AI 风险概览
  - AI 客户经营建议
  - AI 库存建议
- 知识库助手：
  - RAG 问答（answer + basis + sources + retrieved_chunks）

说明：
- 客户/订单 AI 后端调用 `DeepSeekService`，失败时有规则回退（fallback）。  
- Dashboard AI 目前为前端结构化演示生成逻辑（用于看板演示）。

---

## AI 工程化能力

当前项目不仅展示 AI 调用结果，也补充了围绕 AI 调用链路的观测、复盘、模板管理和业务闭环能力，便于在面试中说明 AI 功能如何从 Demo 走向可维护的业务系统。

### 1) AI 调用可观测

- 后端新增 `ai_call_logs` 表，用于记录每次 AI 调用的模块、任务类型、状态、耗时、错误信息、模型名称、Prompt 模板 key 和 Prompt 版本。  
- `DeepSeekService.chat_json` 和 `LLMService.chat_json` 已统一接入 AI 调用日志，成功写入 `success`，失败写入 `failed`，并保留原异常抛出行为。  
- 业务调用点已补充 `module` / `task_type`，例如客户跟进建议、客户跟进总结、订单分析、知识库问答等。

### 2) AI 调用日志页面

- 前端新增“AI 调用日志”页面，用于查看 AI 调用记录。  
- 支持按模块、状态、关键词筛选，支持分页、刷新和详情查看。  
- 详情弹窗展示完整 `prompt`、`response`、`error_message`，并展示 `prompt_template_key` / `prompt_version`，方便追踪一次调用使用了哪个 Prompt 模板。

### 3) AI 效果统计

- AI 调用日志页面顶部提供统计卡片，展示 AI 调用总次数、成功率、失败次数、平均耗时、客户 AI 采纳次数和客户 AI 采纳率。  
- 后端统计口径基于真实日志与跟进记录来源字段计算，包括 `ai_call_logs` 和 `customer_follow_records.source_type='ai_adopted'`。

### 4) AI 调用复盘

- AI 调用日志详情弹窗中增加“调用复盘”区域。  
- 前端根据 `status`、`error_message`、`response` 做轻量规则诊断，例如 API Key 未配置、JSON 格式异常、超时、限流、无有效响应等。  
- 复盘内容包括结论、可能原因和建议处理，便于快速定位常见 AI 调用问题。

### 5) Prompt 模板管理

- 后端新增 `PromptTemplateService`，当前使用 Python 字典维护模板，不依赖数据库。  
- 模板包含 `template_key`、模块、任务类型、名称、描述、版本、`system_prompt` 和 `user_prompt_template`。  
- 已注册模板包括：
  - `customer_follow_advice`
  - `customer_follow_summary`
  - `order_analysis`
  - `knowledge_base_rag_answer`
  - `supervisor_plan`
- 服务支持模板列表、模板详情和变量渲染，缺少变量时返回清晰错误，便于定位 Prompt 维护问题。

### 6) Prompt 模板查看页

- 前端新增“Prompt 模板”只读页面。  
- 支持按模块、任务类型和关键词筛选模板列表。  
- 详情弹窗展示 `system_prompt` 和 `user_prompt_template`，并保留换行代码块样式，方便查看和复制。

### 7) Prompt 版本追踪与模板效果统计

- 每次 AI 调用日志可记录 `prompt_template_key` 和 `prompt_version`，用于追踪调用结果与 Prompt 版本的关系。  
- 后端提供按 Prompt 模板维度的效果统计，按模板 key、版本、模块、任务类型聚合调用次数、成功次数、失败次数、成功率和平均耗时。  
- 前端在 Prompt 模板页面展示“模板效果统计”表格，便于比较不同模板和版本的调用表现。

### 8) AI 建议采纳闭环

- 客户详情页的 AI 跟进建议支持一键“采纳为跟进记录”。  
- 采纳后会复用客户跟进记录创建接口，将 AI 建议转为正式跟进记录，并刷新跟进记录列表。  
- 跟进记录新增来源追踪字段：`source_type`、`source_module`、`source_ref_id`。AI 采纳生成的记录会标记 `source_type='ai_adopted'`，并在列表中展示“AI采纳”标签。

### 面试展示重点

- 这个项目不只是调用大模型返回文本，而是将 AI 调用纳入可查询、可统计、可复盘的工程化链路。  
- AI 结果可以进入客户跟进业务闭环，形成“AI 建议 -> 人工采纳 -> 业务记录”的可追踪流程。  
- Prompt 不再完全散落在业务代码中，已通过 `PromptTemplateService` 开始按模板 key、任务类型和版本统一管理。  
- AI 调用日志和 Prompt 版本关联后，可以按模板维度观察成功率、失败次数和平均耗时，为后续 Prompt 优化提供依据。  
- 当前实现保持最小可用，不夸大为完整 MLOps 平台，但已经覆盖了业务 AI 落地中常见的日志、统计、复盘、模板和采纳闭环。

---

## 技术栈

### 前端
- Vue 3
- TypeScript
- Naive UI
- Vue Router
- Pinia
- Axios
- ECharts（npm 方式引入）

### 后端
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT（登录 + refresh token）
- OpenAI SDK（用于 DeepSeek 兼容调用）
- RAG 相关：
  - `langchain-text-splitters`
  - `faiss-cpu`（可用时）
  - `scikit-learn`（HashingVectorizer）

---

## 项目结构

```text
ai-erp/
├─ frontend/                 # Vue3 前端
│  ├─ src/
│  │  ├─ views/              # 页面（dashboard/customer/product/order/knowledge-base/login）
│  │  ├─ api/                # 前端接口封装
│  │  ├─ router/             # 路由与守卫
│  │  ├─ components/         # 通用组件（如侧边栏）
│  │  └─ utils/              # 工具（如订单运行态本地存储）
├─ backend/                  # FastAPI 后端
│  ├─ app/
│  │  ├─ api/routes/         # 路由
│  │  ├─ models/             # SQLAlchemy 模型
│  │  ├─ schemas/            # Pydantic 模型
│  │  ├─ services/           # 业务服务（含 AI 与知识库服务）
│  │  └─ core/               # 配置、鉴权、响应工具
│  ├─ knowledge_base/        # 知识库文档目录（.md/.txt）
│  ├─ erp.db                 # SQLite 数据库文件
│  └─ run.py                 # 启动脚本
└─ README.md
```

---

## 环境变量配置

项目提供后端和前端两份 `.env.example`，用于统一管理本地启动配置。首次启动前建议复制示例文件：

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

后端配置文件：`backend/.env`

- `BACKEND_HOST`：后端监听地址，默认 `0.0.0.0`。
- `BACKEND_PORT`：后端监听端口，默认 `8000`。
- `DATABASE_URL`：数据库连接地址，默认 `sqlite:///./erp.db`。
- `JWT_SECRET_KEY`：JWT 签名密钥，本地可使用默认值，正式演示或部署前应修改。
- `JWT_ALGORITHM`：JWT 签名算法，默认 `HS256`。
- `ACCESS_TOKEN_EXPIRE_MINUTES`：访问令牌有效期，单位分钟。
- `REFRESH_TOKEN_EXPIRE_DAYS`：刷新令牌有效期，单位天。
- `DEEPSEEK_API_KEY`：DeepSeek API Key，属于敏感信息，不要提交到 Git。
- `DEEPSEEK_BASE_URL`：DeepSeek OpenAI 兼容接口地址。
- `DEEPSEEK_MODEL`：DeepSeek 模型名称，默认 `deepseek-v4-flash`。

前端配置文件：`frontend/.env`

- `VITE_API_BASE_URL`：前端 Axios 基础路径，默认 `/api`。
- `VITE_API_PROXY_TARGET`：Vite 本地代理目标地址，默认 `http://127.0.0.1:8000`。

说明：
- 如果没有创建 `.env`，项目仍会使用代码中的默认配置启动。
- `.env`、`backend/.env`、`frontend/.env` 已加入忽略规则，示例文件 `.env.example` 会保留在 Git 中。
- `DEEPSEEK_API_KEY`、真实 JWT 密钥等敏感信息只写入本地 `.env`，不要提交到仓库。

---

## 本地启动方式

## 1) 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端会读取 `backend/.env`。如果端口冲突，可修改 `BACKEND_PORT`；使用客户/订单 AI 与知识库回答生成时建议配置 `DEEPSEEK_API_KEY`。

也可以临时通过 Windows PowerShell 环境变量覆盖：

```powershell
cd backend
$env:BACKEND_PORT='8001'
$env:DEEPSEEK_API_KEY='你的key'
python run.py
```

## 2) 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认通过 Vite 代理访问后端 `/api`。若后端端口不是 `8000`，可调整 `frontend/.env` 中的 `VITE_API_PROXY_TARGET`。

## 3) 登录账号
- 默认管理员账号会在后端启动时自动初始化：
  - 用户名：`admin`
  - 密码：`123456`

## 4) 知识库文档目录
- 目录：`backend/knowledge_base/`
- 当前支持格式：`.md` / `.txt`
- 建议在新增或修改文档后，进入知识库助手页面点击“重建索引”。

---

## 项目现状说明（真实）

### 已完成
- 客户、商品、订单、看板、知识库助手等核心业务页面。  
- 登录鉴权（JWT + refresh）。  
- 客户/订单 AI 结构化分析接口（含 fallback）。  
- 知识库助手最小 RAG 链路（文档读取、切分、检索、答案与证据返回）。  
- AI 调用日志、日志查询页面、效果统计、调用复盘和 Prompt 模板只读管理。  
- 客户 AI 跟进建议采纳为跟进记录，并通过 `source_type='ai_adopted'` 追踪来源。  
- Prompt 模板 key / version 已写入 AI 调用日志，并支持按模板维度统计调用效果。  
- 多处业务联动和状态展示增强。  

### 演示/本地持久化/前端聚合部分
- Dashboard AI 结果为前端结构化演示逻辑（非后端模型生成）。  
- Dashboard 的部分经营指标与 Top 商品为前端聚合计算。  
- 客户详情、订单详情、Dashboard 的 AI 结果与操作记录存在本地持久化（localStorage）逻辑。  
- 订单支付/发货/风险运行态有前端演示层状态缓存逻辑（`order-runtime-state`）。  

### 知识库助手（RAG）当前技术边界
- 已实现最小可用 RAG，但 embedding 方案是 `HashingVectorizer`（scikit-learn）演示实现。  
- 检索层支持 `faiss-cpu`（可用时走 FAISS，否则回退 NumPy 点积）。  
- 生成层调用 DeepSeek（OpenAI 兼容方式）；失败时回退规则化答复。

### 后续可扩展方向
- 标准 embedding 模型接入（如 bge / text-embedding-3-*）与向量库规范化。  
- 知识库文档上传、版本管理、权限控制、增量索引。  
- 商品库存独立模块（入库/出库/盘点）与订单/采购联动。  
- 更完整 RBAC（角色-菜单-按钮-数据权限）与后台权限配置页。  
- 统一操作审计日志落库（替换前端轻量日志）。
