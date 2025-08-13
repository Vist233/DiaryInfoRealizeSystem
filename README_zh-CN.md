DiaryInfoRealizeSystem（精简版笔记）

概览
- 单一 Django 应用（notes）承载页面与 API，支持 [[双向链接]]、极简 UI，以及详情页就地编辑（点击标题/内容进入编辑）。
- 开发默认使用 SQLite，自定义用户模型 `users.User`。JSON API 合并在 `notes` 路由下。

快速开始
1) 创建虚拟环境并安装 Django 4.2
2) 迁移数据库并启动开发服务器

```
python -m venv venv
venv\Scripts\activate  # Windows
pip install django==4.2.*
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

可选：更安全的 Markdown 渲染
- 如安装 `markdown` 与 `bleach`，将自动启用更安全的内容渲染（否则使用内置轻量渲染）。

```
pip install markdown bleach
```

关键地址
- 列表：`/`
- 新建：`/create/`
- 详情：`/<id>/`
- API：`api/notes/`（GET/POST），`api/notes/<id>/`（GET/PATCH/DELETE），`api/notes/preview/`（POST 预览渲染）

就地编辑
- 在详情页点击标题或内容即可编辑；Ctrl/Cmd+S 保存，Esc 取消。右侧实时预览通过后端渲染，保证与实际展示一致。

搜索与快捷创建
- 列表页右上角提供搜索框（标题/内容），下方提供“Quick Create”快速创建条。

说明
- 为保持“非必要不增实体”，已移除 Channels/WebSocket、capture、AI 等模块，仅保留 notes + users 核心功能。
- 对 `Note` 强制 `(owner, title)` 唯一；迁移中已加入去重逻辑，避免加约束失败。

