### 技术选型更新

1.  **后端 (Python):**
    *   **框架:** **Django** (包含 Django Channels 用于 WebSocket 支持)。
        *   **Django:** 用于处理用户认证、笔记管理（CRUD）、数据库模型等核心业务逻辑。它自带 admin 后台，方便管理。
        *   **Django Channels:** Django 的扩展，用于处理 WebSocket 连接，实现实时通信功能（例如实时同步编辑状态、通知等）。
    *   **数据库:** **SQLite** (非常适合 MVP 阶段，易于部署和管理)。
    *   **用户认证:** Django 内置的用户认证系统 (`django.contrib.auth`)。
    *   **异步任务 (可选):** 对于 MVP，如果需要后台任务（如稍后读抓取），可以使用 Django 的 `django-celery-beat` 配合 Celery 和 Redis/RabbitMQ。但在初期，可以考虑直接在视图中同步处理简单任务，或者使用 `threading` 简单异步处理。
    *   **AI 集成:** `openai` Python SDK 或 `langchain`。

2.  **前端:**
    *   **笔记编辑器:** 寻找支持双向链接的开源 Markdown 编辑器，或者基于现有库（如 CodeMirror, Monaco Editor）定制开发。需要考虑与后端的交互以及 WebSocket 实时同步。
    *   **Web 应用:** 可以使用 Django 模板渲染基础页面，结合 JavaScript (ES6+) 和现代前端库（如 React/Vue 的部分组件）来增强交互性，或者完全采用前后端分离模式。
    *   **移动端:** React Native / Flutter (跨平台) 或后续考虑原生开发。
    *   **WebSocket 客户端:** JavaScript 原生 WebSocket API 或更高级的库（如 Socket.IO client）。

3.  **其他工具:**
    *   **部署:** Docker + Docker Compose。
    *   **搜索引擎 (未来):** 如果笔记增长，集成 Elasticsearch。

### 执行计划更新 (聚焦 Django 和 SQLite)

1.  **环境搭建:**
    *   安装 Python (推荐 3.9+)。
    *   创建项目虚拟环境并激活。
    *   安装 Django, Django Channels, daphne (ASGI 服务器), `openai`, `requests` 等必要库。

2.  **项目结构设计 (Django):**
    *   创建 Django 项目 (`django-admin startproject DiaryInfoRealizeSystem`)。
    *   规划应用模块:
        *   `users`: 用户管理（注册、登录、权限）。
        *   `notes`: 核心笔记功能（模型、视图、序列化器、URLs）。
        *   `capture`: 处理各种捕获渠道的逻辑（如果复杂的话，可以拆分，如 `browser_extension`, `mobile_share`）。
        *   `ai_integration`: AI 功能接口（摘要、问答）。
        *   `common` (可选): 存放公共的 utils, middleware 等。

3.  **Phase 0 (MVP) 核心功能实现:**
    *   **数据库模型 (models.py):**
        *   `User`: 利用 Django 内置 `AbstractUser`。
        *   `Note`: 包含标题、内容（Markdown）、创建时间、更新时间等字段。可以预留字段用于双向链接关系。
    *   **用户系统 (users app):**
        *   配置 Django settings 中的认证后端。
        *   实现注册、登录、登出视图和 URL。
        *   使用 Django 内置 admin 管理用户（可选）。
    *   **笔记系统 (notes app):**
        *   实现 `Note` 模型的 CRUD 视图（基于 Django Class-Based Views 或 Function-Based Views）。
        *   创建基础的笔记列表和详情页面模板。
        *   **Markdown 编辑器:** 集成一个基础的 Markdown 编辑器到笔记编辑页面。
        *   **双向链接:** 在笔记保存时解析 `[[...]]` 语法，建立笔记间的关联关系，并在展示时渲染为链接。
    *   **WebSocket 实时功能 (Django Channels):**
        *   配置 `settings.py` 和 `asgi.py` 以启用 Channels。
        *   创建 `consumers.py` 来处理 WebSocket 连接（例如，在笔记编辑页面实时同步编辑状态）。
        *   定义 `routing.py` 路由 WebSocket 连接。
        *   在前端页面中实现 WebSocket 客户端连接和消息处理。
    *   **快速捕获 - MVP 版本:**
        *   实现一个简单的 API 端点，允许通过 POST 请求（例如来自浏览器插件或移动应用）创建笔记。
        *   开发一个非常基础的浏览器插件或移动分享入口原型，验证数据能成功发送到后端。

4.  **Phase 1 功能实现 (迭代):**
    *   **RSS 订阅与管理:** 在 `notes` 或新建 `rss` app 中实现订阅源管理、定时抓取（可能需要集成 Celery）。
    *   **稍后读队列:** 设计模型存储待读文章链接和元数据，提供展示和管理界面。
    *   **AI 集成:** 在 `ai_integration` app 中封装 OpenAI API 调用，为笔记或文章提供摘要和问答功能。

5.  **开发与测试:**
    *   编写单元测试和集成测试。
    *   使用 Django 的 Debug Toolbar 辅助开发调试。
    *   遵循 PEP8 代码规范。

6.  **部署准备:**
    *   配置生产环境 settings (数据库、静态文件、安全设置等)。
    *   使用 Gunicorn + Nginx 或 Daphne 部署（注意 Daphne 支持 ASGI，适合包含 WebSocket 的应用）。
    *   编写 Dockerfile 和 docker-compose.yml。