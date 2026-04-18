# RAG 与知识库模块说明

## 1. 模块概述

RAG（Retrieval-Augmented Generation）层是系统的核心组件，负责文档处理、向量存储、风格学习和知识检索功能。

### 1.1 核心功能

- **文档处理**：支持多种格式（Markdown、TXT、PDF）的清洗和分块
- **向量存储**：基于 ChromaDB 的本地向量数据库
- **风格学习**：从笔记中提取写作风格特征
- **知识检索**：语义相似度搜索和重排序

### 1.2 目录结构

```
rag/
├── __init__.py              # 模块导出
├── document_washer.py       # 文档清洗
├── chunker.py              # 文档分块
├── embedding.py             # 向量化服务
├── searcher.py             # 向量检索
├── reranker.py             # 结果重排序
├── pipeline.py              # RAG 处理管道
├── note_importer.py        # 笔记导入
├── style_learner.py        # 风格学习
├── style_manager.py        # 风格管理
└── vector_db_optimize.py   # 向量数据库优化
```

## 2. 核心组件

### 2.1 DocumentWasher（文档清洗器）

负责清洗原始文档，保留文本内容。

**功能特性**：

- 去除多余空白
- 标准化换行
- 去除特殊字符
- Markdown 标记去除
- PDF 页眉页脚处理

**使用示例**：

```python
from eleven_blog_tunner.rag import DocumentWasher

washer = DocumentWasher()
clean_text = washer.wash(raw_text, file_type="markdown")
```

### 2.2 Chunker（文档分块器）

将长文档分割成小块，支持语义边界分块。

**分块策略**：

- `semantic`：语义分块（默认）- 基于段落和句子边界
- `recursive`：递归分块 - 多层次递归分割
- `fixed`：固定长度分块

**元数据**：

- `chunk_index`：块索引
- `start_pos`：起始位置
- `end_pos`：结束位置
- `paragraph_index`：段落索引
- `sentence_index`：句子索引

**使用示例**：

```python
from eleven_blog_tunner.rag import Chunker

chunker = Chunker(chunk_size=1000, chunk_overlap=200)
chunks_with_metadata = chunker.split(
    text,
    strategy="semantic",
    metadata={"source": "my_note.md", "category": "tech"}
)
```

### 2.3 EmbeddingService（向量化服务）

将文本转换为向量表示。

**支持模型**：

- OpenAI：`text-embedding-3-small`
- 本地 Ollama：`dengcao/bge-large-zh-v1.5:latest`

**配置项**：

- `use_local_embedding`：是否使用本地模型
- `embedding_model`：OpenAI embedding 模型
- `local_embedding_model`：本地 embedding 模型

**使用示例**：

```python
from eleven_blog_tunner.rag import EmbeddingService

embedder = EmbeddingService(model_name="text-embedding-3-small")
vector = await embedder.embed("要向量化的文本")
vectors = await embedder.embed_batch(["文本1", "文本2"])
```

### 2.4 Searcher（向量检索器）

基于 ChromaDB 的向量检索实现。

**功能**：

- 向量索引构建
- 相似度搜索
- 元数据过滤

**使用示例**：

```python
from eleven_blog_tunner.rag import Searcher

searcher = Searcher()
await searcher.index(chunks, embeddings, metadatas)
results = await searcher.search(query_vector, top_k=10)
```

### 2.5 Reranker（重排序器）

对检索结果进行精细排序。

**支持方式**：

- Cross-encoder：使用 `sentence-transformers` 的 Cross-Encoder 模型
- 简单排序：基于关键词匹配的降级方案

**默认模型**：`cross-encoder/ms-marco-MiniLM-L-6-v2`

**使用示例**：

```python
from eleven_blog_tunner.rag import Reranker

reranker = Reranker()
ranked_results = await reranker.rerank(query, candidates, top_k=5)
```

### 2.6 RAGPipeline（RAG 处理管道）

整合所有 RAG 组件，提供端到端的文档处理和检索流程。

**流程**：

```
文档 → 清洗 → 分块 → 向量化 → 存储
查询 → 向量化 → 检索 → 重排序 → 结果
```

**使用示例**：

```python
from eleven_blog_tunner.rag import RAGPipeline

pipeline = RAGPipeline()

# 处理文档
await pipeline.process_document(
    doc=content,
    metadata={"source": "note.md"},
    file_type="markdown",
    chunk_strategy="semantic"
)

# 检索
results = await pipeline.search("查询内容", top_k=5)
```

### 2.7 NoteImporter（笔记导入器）

批量导入笔记文件到知识库。

**支持格式**：

- Markdown (.md, .markdown)
- 文本 (.txt)
- PDF (.pdf)

**使用示例**：

```python
from eleven_blog_tunner.rag import NoteImporter

importer = NoteImporter()

# 导入单个文件
await importer.import_note("path/to/note.md", metadata={"category": "tech"})

# 批量导入目录
results = await importer.import_directory("path/to/notes")
```

### 2.8 StyleLearner（风格学习器）

从文本中提取写作风格特征。

**风格特征维度**：

- **词汇特征**：`vocabulary_diversity`、`average_word_length`、`unique_words_ratio`
- **句式特征**：`average_sentence_length`、`sentence_complexity`、`punctuation_density`
- **结构特征**：`paragraph_average_length`、`transition_words_ratio`
- **写作习惯**：`passive_voice_ratio`、`first_person_ratio`、`emoji_usage`

**使用示例**：

```python
from eleven_blog_tunner.rag import StyleLearner

learner = StyleLearner()
style = await learner.learn_style(text)
```

### 2.9 StyleManager（风格管理器）

管理和持久化风格数据，将风格注册为 Agent 可用的技能。

**功能**：

- 风格提取和存储
- 风格列表管理
- 风格技能化

**使用示例**：

```python
from eleven_blog_tunner.rag import StyleManager

manager = StyleManager()

# 从文本提取风格
style = await manager.extract_style(text, "my_style")

# 从笔记目录提取风格
style = await manager.extract_style_from_notes("/path/to/notes", "my_style")

# 列出所有风格
styles = manager.list_styles()
```

### 2.10 VectorDBOptimizer（向量数据库优化器）

管理和优化 ChromaDB 向量数据库。

**功能**：

- 数据库优化和压缩
- 集合管理
- 备份和恢复

**使用示例**：

```python
from eleven_blog_tunner.rag import VectorDBOptimizer

optimizer = VectorDBOptimizer()
optimizer.optimize()
stats = optimizer.get_statistics()
optimizer.backup("./backup")
```

## 3. 元数据设计

### 3.1 文档级元数据

```json
{
    "source": "note.md",
    "file_name": "note.md",
    "file_path": "/path/to/note.md",
    "file_size": 1024,
    "file_type": "markdown",
    "category": "tech",
    "tags": ["AI", "机器学习"]
}
```

### 3.2 块级元数据

```json
{
    "chunk_index": 0,
    "start_pos": 0,
    "end_pos": 500,
    "chunk_length": 500,
    "paragraph_index": 0,
    "sentence_index": null,
    "chunk_strategy": "semantic",
    "is_style_reference": true,
    "source": "note.md",
    "file_type": "markdown"
}
```

## 4. 检索流程

### 4.1 向量检索

1. 用户输入查询文本
2. 查询文本通过 EmbeddingService 向量化
3. Searcher 执行相似度搜索（Top-K\*2）
4. Reranker 对候选结果进行重排序
5. 返回最终 Top-K 结果

### 4.2 风格检索

1. 用户请求特定风格
2. 从 StyleManager 加载风格数据
3. 根据风格向量检索相关段落
4. 返回风格参考段落列表

## 5. 大规模数据处理

### 5.1 性能优化策略

- **集合分割**：按类别（笔记/文章）分割到不同集合
- **批量处理**：使用 `embed_batch` 批量向量化
- **缓存机制**：复用 Embedding 结果
- **数据库优化**：定期优化和压缩向量数据库

### 5.2 数据规模建议

| 数据类型 | 建议规模       | 存储方式      |
| ---- | ---------- | --------- |
| 笔记   | 100-1000 个 | 按时间/类别分集合 |
| 文章   | 10-100 篇   | 单独集合      |
| 风格   | 5-20 个     | JSON 文件   |

## 6. API 接口

### 6.1 知识导入

```
POST /api/v1/knowledge/import
```

**参数**：

- `file`：上传文件
- `metadata`：元数据（可选，JSON 字符串）

### 6.2 知识搜索

```
GET /api/v1/knowledge/search?query=关键词&top_k=5
```

**响应**：

```json
{
    "success": true,
    "results": [
        {
            "content": "检索到的内容",
            "score": 0.85,
            "metadata": {}
        }
    ]
}
```

### 6.3 风格学习

```
POST /api/v1/knowledge/learn-style
```

**参数**：

- `file`：风格样本文件

**响应**：

```json
{
    "success": true,
    "style": {
        "name": "风格名称",
        "features": {},
        "vector": []
    }
}
```

### 6.4 知识库统计

```
GET /api/v1/knowledge/stats
```

## 7. 与 Agent 的集成

### 7.1 Summary Agent

使用 RAG 检索风格参考段落：

```python
# 检索相关段落
results = await pipeline.search(f"{topic} 风格参考")
```

### 7.2 Writer Agent

使用风格技能生成文章：

```python
# 调用已注册的风格技能
await agent.call_skill(f"style_{style_name}", {"topic": topic})
```

### 7.3 System Agent

获取风格配置和知识库状态：

```python
# 获取用户风格
style = style_manager.load_style(user_id)

# 获取知识库统计
stats = optimizer.get_statistics()
```

## 8. 配置项

### 8.1 环境变量

| 变量名                     | 说明                  | 默认值                                |
| ----------------------- | ------------------- | ---------------------------------- |
| `VECTOR_DB_PATH`        | 向量数据库路径             | `./data/vector_db`                 |
| `EMBEDDING_MODEL`       | OpenAI Embedding 模型 | `text-embedding-3-small`           |
| `LOCAL_EMBEDDING_MODEL` | 本地 Embedding 模型     | `dengcao/bge-large-zh-v1.5:latest` |
| `USE_LOCAL_EMBEDDING`   | 是否使用本地模型            | `False`                            |
| `CHUNK_SIZE`            | 分块大小                | `1000`                             |
| `CHUNK_OVERLAP`         | 分块重叠                | `200`                              |

## 9. 待完善功能

- [ ] PDF 解析优化（使用 PyMuPDF）
- [ ] 增量索引更新
- [ ] 分布式向量数据库支持
- [ ] 高级过滤查询
- [ ] 知识图谱集成

