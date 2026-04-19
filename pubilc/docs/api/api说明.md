# ELEVEN Blog Tuner - API 说明文档

## 1. API 概述

### 1.1 基本信息

| 项目 | 说明 |
|-----|------|
| 基础URL | `http://localhost:8000` |
| API 版本 | v1 |
| 数据格式 | JSON |
| 认证方式 | JWT (待实现) |

### 1.2 路由结构

```
/api/v1/
├── /config/          # 系统配置 API
├── /agent/          # Agent 任务 API
├── /knowledge/      # 知识库管理 API
├── /notes/          # 笔记管理 API
├── /categories/     # 分类管理 API
├── /styles/         # 风格学习 API
├── /articles/       # 文章生成 API
├── /file-tree/      # 文件树 API
└── /gateway/        # 网关任务管理 API
```

### 1.3 通用响应格式

所有 API 响应统一使用以下格式：

```json
{
  "code": "200",
  "data": {},
  "message": "操作成功"
}
```

| 字段 | 类型 | 说明 |
|-----|------|-----|
| code | string | 状态码，"200"表示成功，其他表示错误 |
| data | any | 响应数据，类型取决于具体 API |
| message | string | 提示信息（成功信息或错误信息） |

### 1.4 响应码说明

| 响应码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 数据验证错误 |
| 500 | 服务器内部错误 |

### 1.5 通用错误响应

```json
{
  "code": "404",
  "data": null,
  "message": "资源不存在"
}
```

---

## 2. 配置相关 API

### 2.1 健康检查

**GET** `/api/v1/config/health`

检查系统健康状态

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "status": "healthy",
    "version": "0.1.0"
  },
  "message": "健康检查成功"
}
```

### 2.2 获取系统配置

**GET** `/api/v1/config/settings`

获取当前系统配置

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "api_base_url": "http://localhost:8000",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "embedding_model": "text-embedding-3-small"
  },
  "message": "获取系统配置成功"
}
```

---

## 3. Agent 任务 API

### 3.1 创建任务

**POST** `/api/v1/agent/tasks`

创建新的 Agent 任务

**请求体:**
```json
{
  "user_input": "请帮我写一篇关于人工智能的文章",
  "metadata": {}
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  },
  "message": "任务创建成功"
}
```

### 3.2 获取任务状态

**GET** `/api/v1/agent/tasks/{task_id}`

获取指定任务的状态

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed"
  },
  "message": "获取任务状态成功"
}
```

### 3.3 获取任务结果

**GET** `/api/v1/agent/tasks/{task_id}/result`

获取任务执行结果

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": "生成的文章内容...",
    "error": null
  },
  "message": "获取任务结果成功"
}
```

### 3.4 取消任务

**DELETE** `/api/v1/agent/tasks/{task_id}`

取消正在执行的任务

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled"
  },
  "message": "任务取消成功"
}
```

### 3.5 列出所有任务

**GET** `/api/v1/agent/tasks`

列出所有任务

**响应示例:**
```json
{
  "code": "200",
  "data": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed"
    }
  ],
  "message": "获取任务列表成功"
}
```

---

## 4. 知识库管理 API

### 4.1 导入知识

**POST** `/api/v1/knowledge/import`

导入笔记到知识库

**请求体:**
- `file`: 上传的文件 (Markdown/TXT/PDF)
- `metadata`: 可选的元数据 (JSON 字符串)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true
  },
  "message": "知识导入成功"
}
```

### 4.2 搜索知识

**GET** `/api/v1/knowledge/search`

语义搜索知识库

**查询参数:**
- `query`: 搜索查询文本
- `top_k`: 返回结果数量 (默认 5)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true,
    "results": [
      {
        "content": "相关知识内容...",
        "score": 0.95,
        "metadata": {}
      }
    ]
  },
  "message": "搜索成功"
}
```

### 4.3 获取知识统计

**GET** `/api/v1/knowledge/stats`

获取知识库统计信息

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true,
    "stats": {
      "document_count": 100,
      "collection_count": 1,
      "vector_size": 1536
    }
  },
  "message": "获取知识统计成功"
}
```

### 4.4 从笔记学习风格

**POST** `/api/v1/knowledge/learn-style`

从上传的笔记文件学习写作风格

**请求体:**
- `file`: 上传的文本文件

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true,
    "style": {
      "name": "风格名称",
      "features": {},
      "vector": []
    }
  },
  "message": "风格学习成功"
}
```

---

## 5. 笔记管理 API

### 5.1 获取笔记列表

**GET** `/api/v1/notes`

获取当前用户的笔记列表（分页）

**查询参数:**
- `skip`: 跳过数量 (默认 0)
- `limit`: 返回数量 (默认 10)
- `category_id`: 按分类筛选 (可选)
- `keyword`: 按标题关键词搜索 (可选)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "notes": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "我的笔记",
        "word_count": 1500,
        "source_type": "markdown",
        "category_id": null,
        "status": "active",
        "is_vectorized": false,
        "created_at": "2026-04-18T12:00:00",
        "updated_at": "2026-04-18T12:00:00"
      }
    ],
    "total": 25,
    "skip": 0,
    "limit": 10
  },
  "message": "获取笔记列表成功"
}
```

### 5.2 获取笔记详情

**GET** `/api/v1/notes/{note_id}`

获取指定笔记的详细信息

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "我的笔记",
    "content": "笔记内容...",
    "category_id": null,
    "word_count": 1500,
    "source_type": "markdown",
    "created_at": "2026-04-18T12:00:00",
    "updated_at": "2026-04-18T12:00:00"
  },
  "message": "获取笔记详情成功"
}
```

### 5.3 创建笔记

**POST** `/api/v1/notes`

创建新笔记

**请求体:**
```json
{
  "title": "新建笔记",
  "content": "笔记内容...",
  "category_id": "可选的分类ID"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "新建笔记",
    "category_id": null
  },
  "message": "创建笔记成功"
}
```

### 5.4 更新笔记

**PUT** `/api/v1/notes/{note_id}`

更新笔记（重命名、编辑内容、移动分类）

**请求体:**
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容...",
  "category_id": "新的分类ID"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "更新后的标题",
    "category_id": "新的分类ID"
  },
  "message": "笔记更新成功"
}
```

### 5.5 删除笔记

**DELETE** `/api/v1/notes/{note_id}`

删除指定笔记（软删除）

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "message": "笔记删除成功"
  },
  "message": "笔记删除成功"
}
```

### 5.6 上传笔记文件

**POST** `/api/v1/notes/upload`

上传笔记文件（支持 Markdown/TXT/PDF）

**请求体 (FormData):**
- `file`: 上传的文件 (必填)
- `category_id`: 所属分类ID (可选)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "上传的文件名",
    "word_count": 1500
  },
  "message": "笔记上传成功"
}
```

### 5.7 批量导入笔记

**POST** `/api/v1/notes/import`

批量导入笔记（支持 Obsidian 目录结构，自动根据路径创建分类）

**请求体:**
```json
{
  "files": [
    {
      "path": "/编程/Python基础.md",
      "content": "笔记内容...",
      "category_id": "可选的分类ID"
    }
  ],
  "auto_create_folders": true
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true,
    "imported_count": 3,
    "notes": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Python基础"
      }
    ]
  },
  "message": "成功导入 3 条笔记"
}
```

### 5.8 笔记来源类型说明

| 来源类型 | 说明 |
|---------|------|
| markdown | Markdown 文件 |
| txt | 纯文本文件 |
| pdf | PDF 文件 |

---

## 6. 分类管理 API

### 6.1 创建分类

**POST** `/api/v1/categories`

创建文件夹/分类

**请求体:**
```json
{
  "name": "分类名称",
  "type": "note",
  "parent_id": "可选的父分类ID"
}
```

| type 值 | 说明 |
|---------|------|
| all | 通用分类 |
| note | 笔记分类 |
| article | 文章分类 |

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "分类名称",
    "type": "note",
    "parent_id": null
  },
  "message": "创建分类成功"
}
```

### 6.2 更新分类

**PUT** `/api/v1/categories/{category_id}`

更新分类（重命名、移动、排序）

**请求体:**
```json
{
  "name": "新名称",
  "parent_id": "新的父分类ID",
  "sort_order": 1
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "新名称",
    "parent_id": "新的父分类ID"
  },
  "message": "分类更新成功"
}
```

### 6.3 删除分类

**DELETE** `/api/v1/categories/{category_id}`

删除分类（分类下不能有子分类和文件）

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "message": "分类删除成功"
  },
  "message": "分类删除成功"
}
```

---

## 7. 文件树 API

### 7.1 获取文件树

**GET** `/api/v1/file-tree`

获取用户的完整文件树（笔记和文章的联合树形结构）

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "tree": [
      {
        "id": "notes-root",
        "label": "笔记",
        "type": "folder",
        "children": [
          {
            "id": "category-id",
            "label": "分类名称",
            "type": "folder",
            "children": [
              {
                "id": "note-note-id",
                "label": "笔记标题",
                "type": "note",
                "data": {
                  "id": "note-id",
                  "title": "笔记标题",
                  "content": "笔记内容...",
                  "created_at": "2026-04-18T12:00:00"
                }
              }
            ]
          }
        ]
      }
    ]
  },
  "message": "获取文件树成功"
}
```

### 7.2 移动节点

**POST** `/api/v1/file-tree/move`

移动节点（分类/笔记/文章）

**请求体:**
```json
{
  "node_id": "节点ID",
  "node_type": "category",
  "target_parent_id": "目标父节点ID",
  "position": 0
}
```

| node_type 值 | 说明 |
|-------------|------|
| category | 分类节点 |
| note | 笔记节点 |
| article | 文章节点 |

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "message": "节点移动成功"
  },
  "message": "节点移动成功"
}
```

---

## 8. 风格学习 API

### 8.1 从文本学习风格

**POST** `/api/v1/styles/learn`

从文本内容学习写作风格（直接调用 StyleManager，不通过 Gateway 层）

**请求体:**
```json
{
  "text": "这是示例文本内容...",
  "style_name": "my_style",
  "metadata": {
    "source": "user_note"
  }
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "name": "my_style",
    "features": {
      "vocabulary_diversity": 0.75,
      "average_word_length": 4.2,
      "unique_words_ratio": 0.65,
      "average_sentence_length": 25.3,
      "sentence_complexity": 1.8,
      "punctuation_density": 0.12,
      "paragraph_average_length": 150.5,
      "transition_words_ratio": 0.08,
      "passive_voice_ratio": 0.15,
      "first_person_ratio": 0.20,
      "emoji_usage": 0.02
    },
    "vector": [0.1, 0.2, ...],
    "metadata": {
      "source": "user_note"
    }
  },
  "message": "风格学习成功"
}
```

### 8.2 从文件学习风格

**POST** `/api/v1/styles/learn-from-file`

从上传的文件学习写作风格

**请求体 (FormData):**
- `file`: 上传的文本文件
- `style_name`: 风格名称

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "style_name": "my_style"
  },
  "message": "风格 'my_style' 学习成功"
}
```

### 8.3 从笔记提取风格

**POST** `/api/v1/styles/extract-from-note`

从指定笔记的内容提取并学习写作风格

**请求体:**
```json
{
  "note_id": "550e8400-e29b-41d4-a716-446655440000",
  "style_name": "my_style"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "name": "my_style",
    "features": {
      "vocabulary_diversity": 0.75,
      "average_word_length": 4.2,
      "unique_words_ratio": 0.65,
      "average_sentence_length": 25.3,
      "sentence_complexity": 1.8,
      "punctuation_density": 0.12,
      "paragraph_average_length": 150.5,
      "transition_words_ratio": 0.08,
      "passive_voice_ratio": 0.15,
      "first_person_ratio": 0.20,
      "emoji_usage": 0.02
    },
    "vector": [0.1, 0.2, ...],
    "metadata": {
      "source": "note",
      "note_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  },
  "message": "从笔记提取风格成功"
}
```

### 8.4 从文章提取风格

**POST** `/api/v1/styles/extract-from-article`

从指定文章的内容提取并学习写作风格

**请求体:**
```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "style_name": "my_style"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "name": "my_style",
    "features": {
      "vocabulary_diversity": 0.75,
      "average_word_length": 4.2,
      "unique_words_ratio": 0.65,
      "average_sentence_length": 25.3,
      "sentence_complexity": 1.8,
      "punctuation_density": 0.12,
      "paragraph_average_length": 150.5,
      "transition_words_ratio": 0.08,
      "passive_voice_ratio": 0.15,
      "first_person_ratio": 0.20,
      "emoji_usage": 0.02
    },
    "vector": [0.1, 0.2, ...],
    "metadata": {
      "source": "article",
      "article_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  },
  "message": "从文章提取风格成功"
}
```

### 8.5 获取风格列表

**GET** `/api/v1/styles/list`

获取所有已学习的风格

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "styles": [
      {
        "name": "my_style",
        "created_at": "2026-04-19T12:00:00",
        "updated_at": "2026-04-19T12:00:00",
        "sample_count": 3,
        "total_chars": 5000
      }
    ]
  },
  "message": "获取风格列表成功"
}
```

### 8.6 获取风格详情

**GET** `/api/v1/styles/{style_name}`

获取指定风格的详细信息

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "name": "my_style",
    "features": {
      "vocabulary_diversity": 0.75,
      "average_word_length": 4.2,
      ...
    },
    "vector": [0.1, 0.2, ...],
    "metadata": {}
  },
  "message": "获取风格详情成功"
}
```

### 8.7 删除风格

**DELETE** `/api/v1/styles/{style_name}`

删除指定的风格

**响应示例:**
```json
{
  "code": "200",
  "data": {},
  "message": "风格 'my_style' 已删除"
}
```

### 8.8 获取风格参考段落

**GET** `/api/v1/styles/{style_name}/references`

获取与指定风格相关的参考段落

**查询参数:**
- `top_k`: 返回数量 (默认 5)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "references": [
      {
        "content": "参考段落内容...",
        "char_count": 200,
        "added_at": "2026-04-19T12:00:00"
      }
    ]
  },
  "message": "获取风格参考段落成功"
}
```

### 8.9 预览风格特征

**POST** `/api/v1/styles/preview`

预览文本的风格特征（不保存）

**请求体 (FormData):**
- `file`: 上传的文本文件
- `style_name`: 可选的风格名称，用于对比

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "features": {
      "vocabulary_diversity": 0.75,
      ...
    },
    "vector_length": 1536,
    "similarity": 0.85
  },
  "message": "风格预览成功"
}
```

### 8.10 添加风格样本

**POST** `/api/v1/styles/{style_name}/add-sample`

为已有风格添加新的样本，系统会自动进行增量学习更新风格特征

**请求体:**
```json
{
  "text": "这是新的写作样本..."
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "sample_count": 4
  },
  "message": "样本添加成功"
}
```

### 8.11 比较风格相似度

**GET** `/api/v1/styles/{style_name1}/compare/{style_name2}`

比较两种风格的相似度，返回余弦相似度分数

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "similarity": 0.85
  },
  "message": "风格比较成功"
}
```

---

## 9. 文章生成 API

### 9.1 生成文章

**POST** `/api/v1/articles/generate`

生成文章（异步任务，通过 Gateway 层处理）

**请求体:**
```json
{
  "topic": "人工智能在教育中的应用",
  "style_name": "my_style",
  "outline": [
    {
      "title": "引言",
      "description": "介绍AI背景",
      "word_count": "200字"
    }
  ],
  "target_length": 1000,
  "metadata": {}
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "generating"
  },
  "message": "文章生成任务已创建，主题：人工智能在教育中的应用"
}
```

### 9.2 获取文章详情

**GET** `/api/v1/articles/{article_id}`

获取指定文章的详细信息

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "人工智能在教育中的应用",
    "content": "生成的文章内容...",
    "topic": "人工智能在教育中的应用",
    "style_name": "my_style",
    "status": "approved",
    "outline": [...],
    "metadata": {},
    "created_at": 1717564800.0,
    "updated_at": 1717564800.0,
    "version": 1
  },
  "message": "获取文章详情成功"
}
```

### 9.3 获取文章列表

**GET** `/api/v1/articles`

获取文章列表

**查询参数:**
- `status`: 按状态筛选 (draft/generating/reviewing/approved/rejected/published)
- `style_name`: 按风格筛选
- `skip`: 跳过数量 (默认 0)
- `limit`: 返回数量 (默认 10)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "articles": [...],
    "total": 25
  },
  "message": "获取文章列表成功"
}
```

### 9.4 更新文章

**PUT** `/api/v1/articles/{article_id}`

更新文章内容

**请求体:**
```json
{
  "content": "更新后的文章内容...",
  "reason": "修改第二段论述"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "人工智能在教育中的应用",
    "content": "更新后的文章内容...",
    ...
    "version": 2
  },
  "message": "文章已更新，新版本：2"
}
```

### 9.5 删除文章

**DELETE** `/api/v1/articles/{article_id}`

删除指定文章

**响应示例:**
```json
{
  "code": "200",
  "data": {},
  "message": "文章已删除"
}
```

### 9.6 生成大纲

**POST** `/api/v1/articles/{article_id}/outline`

为文章生成或更新大纲（通过 Gateway 层处理）

**请求体:**
```json
{
  "topic": "人工智能在教育中的应用",
  "style_name": "my_style"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "outline": [
      {
        "title": "引言",
        "description": "介绍主题背景",
        "word_count": "200字"
      }
    ],
    ...
  },
  "message": "大纲生成成功"
}
```

### 9.7 润色文章

**POST** `/api/v1/articles/{article_id}/polish`

润色文章内容（通过 Gateway 层处理）

**请求参数 (可选):**
- `style_name`: 新的风格名称

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "润色后的文章内容...",
    ...
  },
  "message": "文章润色成功"
}
```

### 9.8 提交审核

**POST** `/api/v1/articles/{article_id}/review`

提交文章进行审核

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "status": "reviewing"
  },
  "message": "文章已提交审核"
}
```

### 9.9 审核通过

**POST** `/api/v1/articles/{article_id}/approve`

审核通过文章

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "status": "approved"
  },
  "message": "文章已通过审核"
}
```

### 9.10 拒绝文章

**POST** `/api/v1/articles/{article_id}/reject`

拒绝文章

**请求参数:**
- `reason`: 拒绝原因 (可选)

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "status": "rejected",
    "reason": "内容需要进一步核实"
  },
  "message": "文章已拒绝"
}
```

---

## 10. 文章版本管理 API

### 10.1 获取版本历史

**GET** `/api/v1/articles/{article_id}/versions`

获取文章的版本历史

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "versions": [
      {
        "version": 1,
        "content": "第一版内容...",
        "created_at": 1717564800.0,
        "reason": null
      },
      {
        "version": 2,
        "content": "第二版内容...",
        "created_at": 1717564900.0,
        "reason": "修改第二段论述"
      }
    ]
  },
  "message": "获取版本历史成功"
}
```

---

## 11. 网关任务管理 API

### 11.1 创建网关任务

**POST** `/api/v1/gateway/tasks`

创建新的网关任务

**请求体:**
```json
{
  "task_type": "article_generation",
  "input_data": "{\"topic\": \"人工智能的未来\", \"style_name\": \"my_style\"}",
  "user_id": "default"
}
```

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "created",
    "message": "任务创建成功"
  },
  "message": "任务创建成功"
}
```

### 11.2 获取任务状态

**GET** `/api/v1/gateway/tasks/{task_id}`

获取指定任务的状态

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "data": {
      "status": "completed",
      "progress": 100,
      "updated_at": "2026-04-18T12:00:00Z",
      "steps": [
        {
          "step": "开始处理任务",
          "timestamp": "2026-04-18T11:59:00Z"
        }
      ]
    }
  },
  "message": "获取任务状态成功"
}
```

### 11.3 获取任务结果

**GET** `/api/v1/gateway/tasks/{task_id}/result`

获取任务执行结果

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "data": {
      "result": "生成的文章内容..."
    }
  },
  "message": "获取任务结果成功"
}
```

### 11.4 取消任务

**DELETE** `/api/v1/gateway/tasks/{task_id}`

取消正在执行的任务

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled"
  },
  "message": "任务取消成功"
}
```

### 11.5 列出任务

**GET** `/api/v1/gateway/tasks`

列出所有任务

**查询参数:**
- `user_id`: 可选的用户 ID

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "tasks": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "task_type": "article_generation",
        "status": "completed",
        "created_at": "2026-04-18T11:59:00Z",
        "updated_at": "2026-04-18T12:00:00Z"
      }
    ],
    "total": 1
  },
  "message": "获取任务列表成功"
}
```

### 11.6 健康检查

**GET** `/api/v1/gateway/health`

检查网关健康状态

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "success": true,
    "status": "healthy",
    "components": {
      "task_manager": "running",
      "agent_protocol": "available"
    }
  },
  "message": "健康检查成功"
}
```

### 11.7 支持的任务类型

| 任务类型 | 说明 |
|---------|------|
| article_generation | 文章生成 |
| style_analysis | 风格分析 |
| article_review | 文章审查 |
| system_status | 系统状态查询 |

---

## 12. 文章版本管理 API

### 12.1 获取版本历史

**GET** `/api/v1/articles/{article_id}/versions`

获取文章的版本历史

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "versions": [
      {
        "version": 1,
        "content": "第一版内容...",
        "created_at": 1717564800.0,
        "reason": null
      },
      {
        "version": 2,
        "content": "第二版内容...",
        "created_at": 1717564900.0,
        "reason": "修改第二段论述"
      }
    ]
  },
  "message": "获取版本历史成功"
}
```

### 12.2 获取特定版本

**GET** `/api/v1/articles/{article_id}/versions/{version}`

获取文章的特定版本

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "version": 1,
    "content": "第一版内容...",
    "created_at": 1717564800.0,
    "reason": null
  },
  "message": "获取版本 1 成功"
}
```

### 12.3 恢复版本

**POST** `/api/v1/articles/{article_id}/versions/{version}/restore`

恢复到指定版本

**响应示例:**
```json
{
  "code": "200",
  "data": {
    "current_version": 3
  },
  "message": "已恢复到版本 1"
}
```

---

## 13. 文章状态说明

| 状态 | 说明 |
|-----|------|
| draft | 草稿 |
| generating | 生成中 |
| reviewing | 审核中 |
| approved | 已通过 |
| rejected | 已拒绝 |
| published | 已发布 |

---

## 14. 响应码说明

| 响应码 | HTTP 状态码 | 说明 |
|-------|------------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权 |
| 403 | 403 | 禁止访问 |
| 404 | 404 | 资源不存在 |
| 422 | 422 | 数据验证错误 |
| 500 | 500 | 服务器内部错误 |

---

## 15. 使用示例

### 15.1 完整文章生成流程

```bash
# 1. 学习风格
curl -X POST http://localhost:8000/api/v1/styles/learn \
  -H "Content-Type: application/json" \
  -d '{"text": "你的写作样本...", "style_name": "my_style"}'

# 2. 生成文章
curl -X POST http://localhost:8000/api/v1/articles/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能的未来", "style_name": "my_style"}'

# 3. 等待生成完成，然后获取文章
curl http://localhost:8000/api/v1/articles/{article_id}

# 4. 提交审核
curl -X POST http://localhost:8000/api/v1/articles/{article_id}/review

# 5. 审核通过
curl -X POST http://localhost:8000/api/v1/articles/{article_id}/approve
```

### 15.2 版本管理流程

```bash
# 1. 更新文章
curl -X PUT http://localhost:8000/api/v1/articles/{article_id} \
  -H "Content-Type: application/json" \
  -d '{"content": "新内容...", "reason": "修改错误"}'

# 2. 查看版本历史
curl http://localhost:8000/api/v1/articles/{article_id}/versions

# 3. 恢复到旧版本
curl -X POST http://localhost:8000/api/v1/articles/{article_id}/versions/1/restore
```

### 15.3 Gateway 任务管理示例

```bash
# 1. 直接通过 Gateway 创建文章生成任务
curl -X POST http://localhost:8000/api/v1/gateway/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type": "article_generation", "input_data": "{\"topic\": \"人工智能的未来\", \"style_name\": \"my_style\"}", "user_id": "default"}'

# 2. 获取任务状态
curl http://localhost:8000/api/v1/gateway/tasks/{task_id}

# 3. 获取任务结果
curl http://localhost:8000/api/v1/gateway/tasks/{task_id}/result

# 4. 列出所有任务
curl http://localhost:8000/api/v1/gateway/tasks
```

---

**文档版本**: 1.2
**最后更新**: 2026/4/19