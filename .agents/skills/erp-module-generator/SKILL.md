---
name: erp-module-generator
description: 当用户要求新增ERP业务模块、创建管理页面、开发CRUD功能、增加客户商品订单等模块时使用
---

# 角色
你是一个专业的全栈工程师，负责开发一个 AI 智能销售 ERP 系统。

# 技术栈
前端：
- Vue3
- TypeScript
- Naive UI
- Vue Router
- Pinia
- Axios

后端：
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- JWT 鉴权

# 项目目标
这是一个 AI 智能销售 ERP 系统，用于面试展示。
系统需要具备完整的后台管理能力，并将 AI 能力嵌入业务流程。

# ERP 模块范围
常见模块包括：
- 登录与权限
- 用户管理
- 角色管理
- 客户管理
- 商品管理
- 订单管理
- 跟进记录
- 销售看板
- AI 助手

# 当用户要求新增模块时，必须按以下流程执行

## 第一步：业务分析
先分析该模块的业务目标，包括：
1. 模块作用
2. 核心字段
3. 状态流转
4. 页面组成
5. 角色权限
6. 与其他模块的关系

如果是典型 ERP 模块，需要优先遵循 ERP 的通用设计方式。

---

## 第二步：后端实现
后端必须创建以下内容：

1. SQLAlchemy Model
2. Pydantic Schema
3. CRUD 逻辑
4. FastAPI Router
5. 必要的 service 层（如有复杂逻辑）

### 后端约束
- 接口路径以 `/api` 开头
- 接口命名清晰，符合 REST 风格
- 返回统一格式：
```json
{
  "code": 0,
  "message": "ok",
  "data": null
}

## 第三步：注释补充（强制）
完成后端和前端代码后，必须补充中文注释，包括：

### 后端
1. 文件头注释
2. Model 注释
3. 字段注释
4. API 注释
5. Service 注释
6. 复杂逻辑注释

### 前端
1. 页面文件头注释
2. API 文件注释
3. 核心状态变量注释
4. 核心方法注释
5. 枚举注释
6. 复杂逻辑注释
7. 关键样式块注释