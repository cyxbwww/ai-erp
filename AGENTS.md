# 项目规则

## 项目名称
AI 智能销售 ERP 系统

## 项目说明
这是一个用于面试展示的 AI 智能销售 ERP 系统，包含客户管理、商品管理、订单管理、销售看板和 AI 助手功能。
系统重点展示后台管理系统开发能力和 AI 在业务系统中的应用能力。

## 技术栈
### 前端
- Vue3
- TypeScript
- Naive UI
- Vue Router
- Pinia
- Axios
- ECharts

### 后端
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT 鉴权

## 项目结构
- `frontend`：前端项目
- `backend`：后端项目

### 前端目录结构
- `views`：页面
- `components`：组件
- `api`：接口请求
- `stores`：状态管理
- `router`：路由
- `layout`：后台布局

### 后端目录结构
- `app/api`：接口
- `app/models`：数据库模型
- `app/schemas`：数据模型
- `app/services`：业务逻辑
- `app/core`：配置与鉴权

## 接口规范
所有接口返回统一格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": any
}
```

接口路径统一以 `/api` 开头，例如：
- `/api/customer/list`
- `/api/customer/create`
- `/api/customer/update`
- `/api/customer/delete`
- `/api/customer/detail`

## 后台页面规范
后台页面必须包含：
1. 搜索区域
2. 操作按钮区
3. 表格列表
4. 分页
5. 新增按钮
6. 编辑按钮
7. 删除按钮
8. 表单校验
9. 错误提示
10. 加载状态

UI 组件统一使用 Naive UI，不混用其他 UI 库。

## ERP 模块
系统包含以下模块：
- 登录与权限
- 用户管理
- 客户管理
- 商品管理
- 订单管理
- 跟进记录
- 销售看板
- AI 助手

## 权限规则
系统需要 RBAC 权限模型：
- 用户（user）
- 角色（role）
- 菜单（menu）
- 按钮权限（button permission）

## AI 功能规则
AI 功能必须嵌入业务页面，而不是只做一个聊天页面，例如：
- 客户详情页：AI 生成跟进建议
- 商品详情页：AI 生成商品文案
- 订单详情页：AI 分析订单
- Dashboard：AI 销售数据分析

## 开发原则
- 优先保证系统结构完整
- 优先保证模块齐全
- 代码结构清晰
- 模块划分明确
- 适合用于面试展示

## 项目上下文（Context）
### 项目背景
这是一个 AI 智能销售 ERP 系统，用于销售业务管理与 AI 辅助分析。

### 系统模块
系统包含以下模块：
- 登录与权限管理（RBAC）
- 客户管理
- 商品管理
- 订单管理
- 跟进记录
- 销售数据看板
- AI 助手

### 技术栈
#### 前端
- Vue3
- TypeScript
- Naive UI
- Pinia
- Vue Router
- Axios
- ECharts

#### 后端
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT 鉴权

### 数据库表
系统包含以下数据表：
- users
- roles
- customers
- customer_follow_records
- products
- orders
- order_items
- ai_records

### AI 功能
系统中的 AI 功能包括：
- AI 生成商品文案
- AI 生成客户跟进建议
- AI 分析订单
- AI 销售数据分析
- 自然语言问数

### 项目目标
该项目用于展示：
- 后台管理系统开发能力
- 前后端联调能力
- 权限系统设计能力
- AI 在业务系统中的落地能力

## 可执行检查清单（开发完成自检）
每次完成一个模块或一次迭代后，按以下清单逐项检查并打勾。

### 1. 项目结构检查
- [ ] 前端代码仅在 `frontend` 下，后端代码仅在 `backend` 下
- [ ] 前端目录遵循 `views/components/api/stores/router/layout`
- [ ] 后端目录遵循 `app/api/models/schemas/services/core`
- [ ] 新增代码文件命名清晰，模块职责单一

### 2. 前端页面规范检查（每个后台页面）
- [ ] 包含搜索区域
- [ ] 包含操作按钮区
- [ ] 包含表格列表
- [ ] 包含分页
- [ ] 包含新增按钮
- [ ] 包含编辑按钮
- [ ] 包含删除按钮
- [ ] 表单具备校验规则与校验提示
- [ ] 请求失败时有错误提示
- [ ] 列表与提交场景有加载状态
- [ ] UI 仅使用 Naive UI（未混用其他 UI 库）

### 3. 接口与后端规范检查
- [ ] 接口路径统一以 `/api` 开头
- [ ] 接口命名符合模块语义（list/create/update/delete/detail）
- [ ] 所有接口返回统一格式：`{ code, message, data }`
- [ ] `code=0` 代表成功，失败场景有明确 `message`
- [ ] Pydantic 请求/响应模型完整定义
- [ ] SQLAlchemy 模型字段、索引与关系定义合理
- [ ] 关键业务逻辑在 `services` 层，不堆在路由层

### 4. 数据库与模型检查
- [ ] 已包含并使用核心表：`users/roles/customers/customer_follow_records/products/orders/order_items/ai_records`
- [ ] 订单与明细（`orders`、`order_items`）关系正确
- [ ] 客户与跟进记录关系正确
- [ ] AI 调用记录可追踪（请求、结果、时间、关联业务对象）

### 5. 权限（RBAC）检查
- [ ] 完成登录鉴权流程（JWT）
- [ ] 用户（user）-角色（role）关系可配置
- [ ] 菜单权限可控制路由可见性
- [ ] 按钮权限可控制页面操作按钮可见/可用
- [ ] 未授权访问被正确拦截（前端路由 + 后端接口）

### 6. AI 功能落地检查
- [ ] AI 功能嵌入业务页面，而非独立聊天页了事
- [ ] 客户详情页支持 AI 跟进建议
- [ ] 商品详情页支持 AI 商品文案生成
- [ ] 订单详情页支持 AI 订单分析
- [ ] Dashboard 支持 AI 销售数据分析
- [ ] 自然语言问数可返回可解释结果（指标口径清晰）

### 7. 联调与稳定性检查
- [ ] 前后端联调通过：列表、详情、新增、编辑、删除全链路可用
- [ ] Axios 请求封装统一，错误处理统一
- [ ] Pinia 状态流转清晰，无明显重复状态
- [ ] 关键页面无阻塞性报错（控制台、接口日志）
- [ ] 空数据、异常数据、慢响应场景已验证

### 8. 面试展示准备检查
- [ ] 模块齐全：登录权限、用户、客户、商品、订单、跟进、看板、AI 助手
- [ ] 至少准备 1 条完整业务演示链路（客户 -> 订单 -> 分析）
- [ ] 能清晰说明技术选型与分层设计
- [ ] 能清晰说明 RBAC 设计与数据权限控制思路
- [ ] 能清晰说明 AI 如何在业务中产生价值（效率/质量/决策）

### 9. 提交前最小验收（Release Gate）
- [ ] `frontend` 可运行，核心页面可访问
- [ ] `backend` 可运行，核心接口可调用
- [ ] 登录后权限生效，越权访问被拦截
- [ ] 关键模块无 P0/P1 级阻塞问题
- [ ] 本次变更点有记录（便于面试讲解）

## 代码注释规范（强制执行）

所有新增代码、修改代码、重构代码，必须同步补充中文注释，不允许生成无注释代码。

### 后端注释要求（FastAPI）
- 每个 Python 文件必须有文件头注释，说明文件作用
- 每个 Model 必须有注释说明表用途
- 每个字段必须有 comment 或中文说明
- 每个 API 接口必须有注释说明用途、主要参数和返回含义
- 每个 Service 必须有注释说明业务逻辑
- 所有复杂逻辑必须有注释说明“为什么这样做”

### 前端注释要求（Vue3 / TypeScript）
- 每个页面文件必须有文件头注释，说明页面作用
- 每个 API 文件必须有注释说明接口用途
- 每个 store 文件必须有注释说明状态用途
- 每个核心状态变量必须有注释说明用途
- 每个核心方法必须有注释说明作用
- 每个复杂交互逻辑必须有注释说明
- 关键样式块必须有注释说明

### 注释语言规范
- 所有注释必须使用中文
- 界面文字使用中文
- 代码命名使用英文

### 开发要求
如果生成的代码缺少注释，视为未完成，不符合项目规范。

## 命名规范

### 后端
- 表名使用复数：users、customers、orders、order_items
- Model 使用单数类名：User、Customer、Order
- Schema 使用：CustomerCreate、CustomerUpdate、CustomerDetail、CustomerListItem
- Router 文件命名：customer.py、order.py
- Service 文件命名：customer_service.py

### 前端
- 页面文件使用小写或 kebab-case：customer-list.vue、customer-detail.vue
- 组件文件使用 PascalCase：CustomerForm.vue
- API 文件：customer.ts、order.ts
- Store 文件：useCustomerStore.ts

### 接口命名
- list：获取列表
- detail：获取详情
- create：新增
- update：更新
- delete：删除

## Git 提交规范

提交信息格式：
- feat：新增功能
- fix：修复问题
- refactor：重构代码
- docs：文档修改
- style：格式修改
- chore：其他修改

示例：
- feat: 新增客户管理模块
- feat: 新增订单管理模块
- feat: 新增 AI 商品文案功能
- fix: 修复订单金额计算错误

## 语言规范（非常重要）

为了保证项目统一性，语言使用规则如下：

### 1. 界面语言
系统为中文后台管理系统，所有界面文字必须使用中文，包括：
- 菜单名称
- 页面标题
- 表格列名
- 按钮文字
- 表单标签
- 提示信息
- 弹窗文字
- 状态名称

禁止出现英文界面（技术名词除外，如 ID、API、URL）。

### 2. 代码语言
- 变量名使用英文
- 函数名使用英文
- 类名使用英文
- 数据库字段使用英文
- 接口路径使用英文

### 3. 注释语言
所有注释必须使用中文，包括：
- Model 注释
- 字段注释
- API 接口注释
- Service 业务逻辑注释
- Vue 页面注释
- 复杂逻辑注释

示例：

后端：
"""
客户表：用于存储客户基本信息
"""

前端：
// 客户管理列表页
// 功能：展示客户列表，支持搜索、新增、编辑、删除

## 枚举字段规范（非常重要）

统一规则：
1. 数据库存储英文枚举值
2. 前端下拉框显示中文 label，value 为英文
3. 列表页使用 Tag + 中文显示
4. 所有枚举统一在 frontend/src/constants/enums.ts 中定义
5. 禁止在页面中写死中文或英文，必须通过枚举映射渲染

原则：存英文，显中文。