# AI驱动固件智能测试系统 — 知识库数据结构设计（KNOWLEDGE_SCHEMA）

> 文档版本：v1.0
>
> 目标：设计完整的知识库数据结构，包含向量存储、知识单元模型、产品线标签体系、数据库Schema和查询示例。

---

## 1. 设计概述

### 1.1 知识库架构

知识库采用混合存储架构：
- **向量数据库（Qdrant）**：存储知识单元的语义向量，支持相似度检索
- **关系数据库（PostgreSQL）**：存储结构化元数据，支持复杂关联查询
- **文件系统**：存储原始文档、代码片段、日志文件等大对象

### 1.2 数据流向

```
代码修改 → TestAgent → 执行结果 → AnalysisAgent → 知识提取 → 
KnowledgeUnit → 向量化 → Qdrant + PostgreSQL
```

---

## 2. KnowledgeUnit 数据模型

### 2.1 核心数据结构

```json
{
  "id": "ku_20241227_001",
  "content": {
    "title": "PCIe初始化时序优化",
    "summary": "针对Intel Tiger Lake平台，PCIe设备在冷启动后未能正确枚举的解决方案",
    "description": "详细描述问题现象、根因分析、解决方案...",
    "code_snippets": [
      {
        "file_path": "drivers/pci/pcie.c",
        "function": "pcie_device_init",
        "language": "c",
        "content": "原始代码片段或修改后代码"
      }
    ],
    "modification_details": {
      "change_type": "timing_fix",
      "files_modified": ["drivers/pci/pcie.c", "include/pci.h"],
      "lines_added": 15,
      "lines_removed": 8
    }
  },
  "metadata": {
    "product_line": {
      "soc_type": "Tiger_Lake",
      "firmware_stack": "UEFI",
      "chipset": "HM570",
      "platform": "Server"
    },
    "test_context": {
      "test_environment": "QEMU",
      "test_board": "TGL-QEMU",
      "test_duration": "45min",
      "pass_criteria": "pci_devices_detected == 4"
    },
    "execution_result": {
      "status": "success",
      "execution_time": "2024-12-27T10:30:00Z",
      "iterations_count": 3,
      "success_rate": 0.85
    },
    "tags": ["PCIe", "initialization", "enumeration", "timing"],
    "priority": "high",
    "author": "agent_code_v1.2",
    "confidence_score": 0.92
  },
  "relationships": {
    "related_units": ["ku_20241226_015", "ku_20241225_032"],
    "parent_issue": "issue_20241227_001",
    "test_executions": ["te_20241227_001", "te_20241227_002"]
  },
  "vector_embedding": {
    "model": "text-embedding-ada-002",
    "dimension": 1536,
    "vector": [0.1, -0.2, 0.3, ...]
  },
  "audit": {
    "created_at": "2024-12-27T10:35:00Z",
    "updated_at": "2024-12-27T11:20:00Z",
    "version": "1.0",
    "source": "automated_extraction"
  }
}
```

### 2.2 JSON Schema 定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "KnowledgeUnit",
  "type": "object",
  "required": ["id", "content", "metadata", "vector_embedding", "audit"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^ku_[0-9]{8}_[0-9]{3}$",
      "description": "知识单元唯一标识符：ku_YYYYMMDD_NNN"
    },
    "content": {
      "type": "object",
      "required": ["title", "summary", "description"],
      "properties": {
        "title": {"type": "string", "maxLength": 200},
        "summary": {"type": "string", "maxLength": 500},
        "description": {"type": "string"},
        "code_snippets": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["file_path", "language", "content"],
            "properties": {
              "file_path": {"type": "string"},
              "function": {"type": "string"},
              "language": {"type": "string", "enum": ["c", "cpp", "assembly", "python", "shell"]},
              "content": {"type": "string"}
            }
          }
        },
        "modification_details": {
          "type": "object",
          "properties": {
            "change_type": {
              "type": "string",
              "enum": ["bug_fix", "feature_add", "performance", "timing_fix", "refactor"]
            },
            "files_modified": {"type": "array", "items": {"type": "string"}},
            "lines_added": {"type": "integer", "minimum": 0},
            "lines_removed": {"type": "integer", "minimum": 0}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["product_line", "test_context", "execution_result", "tags"],
      "properties": {
        "product_line": {
          "type": "object",
          "required": ["soc_type", "firmware_stack"],
          "properties": {
            "soc_type": {"type": "string"},
            "firmware_stack": {"type": "string"},
            "chipset": {"type": "string"},
            "platform": {"type": "string", "enum": ["Server", "Desktop", "Embedded", "Mobile"]}
          }
        },
        "test_context": {
          "type": "object",
          "properties": {
            "test_environment": {"type": "string"},
            "test_board": {"type": "string"},
            "test_duration": {"type": "string"},
            "pass_criteria": {"type": "string"}
          }
        },
        "execution_result": {
          "type": "object",
          "required": ["status", "execution_time"],
          "properties": {
            "status": {"type": "string", "enum": ["success", "failure", "timeout", "error"]},
            "execution_time": {"type": "string", "format": "date-time"},
            "iterations_count": {"type": "integer", "minimum": 1},
            "success_rate": {"type": "number", "minimum": 0, "maximum": 1}
          }
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1
        },
        "priority": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"],
          "default": "medium"
        },
        "author": {"type": "string"},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
      }
    },
    "relationships": {
      "type": "object",
      "properties": {
        "related_units": {
          "type": "array",
          "items": {"type": "string", "pattern": "^ku_[0-9]{8}_[0-9]{3}$"}
        },
        "parent_issue": {"type": "string"},
        "test_executions": {
          "type": "array",
          "items": {"type": "string", "pattern": "^te_[0-9]{8}_[0-9]{3}$"}
        }
      }
    },
    "vector_embedding": {
      "type": "object",
      "required": ["model", "dimension", "vector"],
      "properties": {
        "model": {"type": "string"},
        "dimension": {"type": "integer", "minimum": 1},
        "vector": {
          "type": "array",
          "items": {"type": "number"},
          "minItems": 1
        }
      }
    },
    "audit": {
      "type": "object",
      "required": ["created_at", "version", "source"],
      "properties": {
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "version": {"type": "string"},
        "source": {"type": "string", "enum": ["manual", "automated_extraction", "import"]}
      }
    }
  }
}
```

---

## 3. 产品线标签体系

### 3.1 SoC Type 标签定义

```yaml
soc_types:
  Intel:
    - "Tiger_Lake"
    - "Alder_Lake" 
    - "Raptor_Lake"
    - "Meteor_Lake"
    - "Arrow_Lake"
    - "Ice_Lake"
    - "Coffee_Lake"
    - "Kaby_Lake"
    - "Broadwell"
    - "Haswell"
    
  AMD:
    - "EPYC_Milan"
    - "EPYC_Genoa"
    - "EPYC_Bergamo"
    - "Ryzen_7000"
    - "Ryzen_5000"
    - "Ryzen_3000"
    
  ARM:
    - "Cortex_A78"
    - "Cortex_A77"
    - "Cortex_A76"
    - "Neoverse_N1"
    - "Neoverse_V1"
    
  Qualcomm:
    - "Snapdragon_8Gen2"
    - "Snapdragon_7Gen1"
    - "Snapdragon_6Gen1"
    
  Other:
    - "Generic_x86_64"
    - "Generic_AArch64"
    - "RISC_V"
```

### 3.2 Firmware Stack 标签定义

```yaml
firmware_stacks:
  UEFI:
    - "UEFI_2.8"
    - "UEFI_2.9"
    - "UEFI_3.0"
    - "EDK2"
    - "Aptio"
    
  Legacy_BIOS:
    - "Legacy_BIOS"
    - "Coreboot"
    
  BMC_Firmware:
    - "OpenBMC"
    - "IPMI"
    - "Redfish"
    - "AMI_BMC"
    
  Operating_System:
    - "Linux"
    - "FreeRTOS"
    - "Zephyr"
    - "Bare_Metal"
    
  Bootloader:
    - "GRUB"
    - "U-Boot"
    - "SPL"
    - "Bootloader"
```

### 3.3 标签体系 JSON Schema

```json
{
  "type": "object",
  "properties": {
    "soc_type": {
      "type": "string",
      "enum": [
        "Tiger_Lake", "Alder_Lake", "Raptor_Lake", "Meteor_Lake",
        "EPYC_Milan", "EPYC_Genoa", "Ryzen_7000", "Cortex_A78",
        "Snapdragon_8Gen2", "Generic_x86_64", "Generic_AArch64"
      ]
    },
    "firmware_stack": {
      "type": "string", 
      "enum": [
        "UEFI_2.8", "UEFI_2.9", "UEFI_3.0", "EDK2", "Aptio",
        "Legacy_BIOS", "Coreboot", "OpenBMC", "IPMI", "Redfish",
        "Linux", "FreeRTOS", "Zephyr", "GRUB", "U-Boot"
      ]
    },
    "chipset": {
      "type": "string",
      "examples": ["HM570", "WM590", "TRX40", "X570", "B450"]
    },
    "platform": {
      "type": "string",
      "enum": ["Server", "Desktop", "Embedded", "Mobile"]
    }
  },
  "required": ["soc_type", "firmware_stack"]
}
```

---

## 4. Qdrant 向量数据库 Schema

### 4.1 Collection 配置

```json
{
  "collection_name": "knowledge_units",
  "vectors": {
    "size": 1536,
    "distance": "Cosine",
    "on_disk_payload": true
  },
  "optimizers_config": {
    "default_segment_number": 2,
    "max_search_threads": 4,
    "indexing_threshold": 20000
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100,
    "full_scan_threshold": 10000
  },
  "wal_config": {
    "wal_capacity_mb": 32,
    "wal_segments_ahead": 4
  }
}
```

### 4.2 Payload Schema 定义

```json
{
  "key": "metadata",
  "fields": {
    "product_line": {
      "type": "keyword",
      "fields": {
        "soc_type": {"type": "keyword"},
        "firmware_stack": {"type": "keyword"},
        "chipset": {"type": "keyword"},
        "platform": {"type": "keyword"}
      }
    },
    "test_context": {
      "type": "object",
      "fields": {
        "test_environment": {"type": "keyword"},
        "test_board": {"type": "keyword"},
        "test_duration": {"type": "keyword"}
      }
    },
    "execution_result": {
      "type": "object", 
      "fields": {
        "status": {"type": "keyword"},
        "execution_time": {"type": "datetime"},
        "iterations_count": {"type": "integer"},
        "success_rate": {"type": "float"}
      }
    },
    "tags": {
      "type": "keyword",
      "is_array": true
    },
    "priority": {"type": "keyword"},
    "confidence_score": {"type": "float"}
  }
}
```

### 4.3 创建 Collection 的 Python 代码

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

def create_knowledge_units_collection(client: QdrantClient):
    """创建知识单元集合"""
    
    collection_config = models.CreateCollection(
        collection_name="knowledge_units",
        vectors_config=models.VectorParams(
            size=1536,
            distance=models.Distance.COSINE,
            on_disk_payload=True
        ),
        optimizers_config=models.OptimizersConfig(
            default_segment_number=2,
            max_search_threads=4,
            indexing_threshold=20000
        ),
        hnsw_config=models.HnswConfig(
            m=16,
            ef_construct=100,
            full_scan_threshold=10000
        ),
        wal_config=models.WalConfig(
            wal_capacity_mb=32,
            wal_segments_ahead=4
        ),
        payload_schema={
            "metadata.product_line.soc_type": models.KeywordIndex(),
            "metadata.product_line.firmware_stack": models.KeywordIndex(),
            "metadata.product_line.chipset": models.KeywordIndex(),
            "metadata.product_line.platform": models.KeywordIndex(),
            "metadata.test_context.test_environment": models.KeywordIndex(),
            "metadata.execution_result.status": models.KeywordIndex(),
            "metadata.tags": models.KeywordIndex(),
            "metadata.priority": models.KeywordIndex(),
            "metadata.execution_result.execution_time": models.DatetimeIndex(),
            "metadata.confidence_score": models.FloatIndex()
        }
    )
    
    client.create_collection(collection_config)
    
# 使用示例
# client = QdrantClient(host="localhost", port=6333)
# create_knowledge_units_collection(client)
```

---

## 5. PostgreSQL 关系表结构

### 5.1 建表SQL

```sql
-- 知识单元主表
CREATE TABLE knowledge_units (
    id VARCHAR(20) PRIMARY KEY,  -- ku_YYYYMMDD_NNN
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    description TEXT NOT NULL,
    change_type VARCHAR(50),
    files_modified TEXT[],
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    content_vector VECTOR(1536),  -- 使用 pgvector 扩展
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(10) DEFAULT '1.0',
    source VARCHAR(50) DEFAULT 'automated_extraction',
    author VARCHAR(100),
    confidence_score DECIMAL(3,2),
    metadata JSONB,
    CONSTRAINT ku_id_format CHECK (id ~ '^ku_[0-9]{8}_[0-9]{3}$')
);

-- 产品线信息表
CREATE TABLE product_lines (
    id SERIAL PRIMARY KEY,
    soc_type VARCHAR(100) NOT NULL,
    firmware_stack VARCHAR(100) NOT NULL,
    chipset VARCHAR(100),
    platform VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    launch_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(soc_type, firmware_stack, platform)
);

-- 代码片段表
CREATE TABLE code_snippets (
    id SERIAL PRIMARY KEY,
    knowledge_unit_id VARCHAR(20) REFERENCES knowledge_units(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    function_name VARCHAR(200),
    language VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 测试执行记录表
CREATE TABLE test_executions (
    id VARCHAR(20) PRIMARY KEY,  -- te_YYYYMMDD_NNN
    knowledge_unit_id VARCHAR(20) REFERENCES knowledge_units(id),
    test_environment VARCHAR(100) NOT NULL,
    test_board VARCHAR(100),
    test_duration VARCHAR(50),
    pass_criteria TEXT,
    execution_status VARCHAR(20) NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE,
    iterations_count INTEGER DEFAULT 1,
    success_rate DECIMAL(5,4),
    test_results JSONB,
    artifacts_path TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT te_id_format CHECK (id ~ '^te_[0-9]{8}_[0-9]{3}$'),
    CONSTRAINT valid_status CHECK (execution_status IN ('success', 'failure', 'timeout', 'error'))
);

-- 迭代记录表
CREATE TABLE iteration_records (
    id SERIAL PRIMARY KEY,
    knowledge_unit_id VARCHAR(20) REFERENCES knowledge_units(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    modification_summary TEXT,
    test_result_status VARCHAR(20),
    analysis_conclusion TEXT,
    decision_made VARCHAR(50),
    execution_duration INTERVAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 标签表
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),  -- domain, component, priority, etc.
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 知识单元标签关联表
CREATE TABLE knowledge_unit_tags (
    knowledge_unit_id VARCHAR(20) REFERENCES knowledge_units(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (knowledge_unit_id, tag_id)
);

-- 知识单元关联表
CREATE TABLE knowledge_unit_relations (
    id SERIAL PRIMARY KEY,
    source_unit_id VARCHAR(20) REFERENCES knowledge_units(id) ON DELETE CASCADE,
    target_unit_id VARCHAR(20) REFERENCES knowledge_units(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,  -- similar, derived,来解决, related
    similarity_score DECIMAL(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_relation_type CHECK (relation_type IN ('similar', 'derived', 'solves', 'related', 'depends_on'))
);

-- 外部问题跟踪表
CREATE TABLE external_issues (
    id VARCHAR(20) PRIMARY KEY,  -- issue_YYYYMMDD_NNN
    knowledge_unit_id VARCHAR(20) REFERENCES knowledge_units(id),
    issue_type VARCHAR(50),  -- bug, feature, enhancement
    priority VARCHAR(20),
    status VARCHAR(20),
    redmine_id INTEGER,  -- Redmine集成ID
    jira_key VARCHAR(50),  # Jira集成key
    title VARCHAR(200),
    description TEXT,
    reported_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT issue_id_format CHECK (id ~ '^issue_[0-9]{8}_[0-9]{3}$')
);
```

### 5.2 索引创建

```sql
-- 向量搜索索引
CREATE INDEX ON knowledge_units USING ivfflat (content_vector vector_cosine_ops)
    WITH (lists = 100);

-- 产品线组合索引
CREATE INDEX idx_ku_product_line ON knowledge_units 
    USING GIN ((metadata->'product_line'));

-- 测试状态索引
CREATE INDEX idx_test_executions_status ON test_executions (execution_status);
CREATE INDEX idx_test_executions_time ON test_executions (execution_time);

-- 标签索引
CREATE INDEX idx_ku_tags ON knowledge_unit_tags (tag_id);
CREATE INDEX idx_tags_category ON tags (category);

-- 时间范围索引
CREATE INDEX idx_ku_created_time ON knowledge_units (created_at);
CREATE INDEX idx_relations_created ON knowledge_unit_relations (created_at);

-- 全文搜索索引
CREATE INDEX idx_ku_search ON knowledge_units 
    USING GIN (to_tsvector('english', title || ' ' || description));

-- JSONB字段索引
CREATE INDEX idx_ku_metadata ON knowledge_units USING GIN (metadata);
CREATE INDEX idx_test_results ON test_executions USING GIN (test_results);
```

### 5.3 视图创建

```sql
-- 知识单元详细视图
CREATE VIEW knowledge_units_detailed AS
SELECT 
    ku.id,
    ku.title,
    ku.summary,
    ku.description,
    ku.change_type,
    ku.files_modified,
    ku.lines_added,
    ku.lines_removed,
    ku.author,
    ku.confidence_score,
    ku.metadata,
    ku.created_at,
    pl.soc_type,
    pl.firmware_stack,
    pl.chipset,
    pl.platform,
    ku.execution_status,
    ku.success_rate,
    array_agg(DISTINCT t.name) as tags
FROM knowledge_units ku
LEFT JOIN product_lines pl ON pl.id = ku.product_line_id
LEFT JOIN knowledge_unit_tags kut ON kut.knowledge_unit_id = ku.id
LEFT JOIN tags t ON t.id = kut.tag_id
GROUP BY ku.id, pl.soc_type, pl.firmware_stack, pl.chipset, pl.platform;

-- 测试执行统计视图
CREATE VIEW test_execution_stats AS
SELECT 
    DATE_TRUNC('day', execution_time) as date,
    test_environment,
    execution_status,
    COUNT(*) as count,
    AVG(iterations_count) as avg_iterations,
    AVG(success_rate) as avg_success_rate
FROM test_executions
WHERE execution_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date, test_environment, execution_status
ORDER BY date DESC, test_environment;

-- 标签使用统计视图
CREATE VIEW tag_usage_stats AS
SELECT 
    t.name,
    t.category,
    COUNT(kut.knowledge_unit_id) as usage_count,
    AVG(ku.confidence_score) as avg_confidence
FROM tags t
JOIN knowledge_unit_tags kut ON kut.tag_id = t.id
JOIN knowledge_units ku ON ku.id = kut.knowledge_unit_id
GROUP BY t.id, t.name, t.category
ORDER BY usage_count DESC;
```

---

## 6. 查询示例

### 6.1 Qdrant 向量检索查询

```python
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

def semantic_search_knowledge_units(client, query_text, limit=10):
    """基于语义相似度的知识库检索"""
    
    # 生成查询向量（实际使用时接入embedding模型）
    query_vector = generate_embedding(query_text)  # [0.1, -0.2, ...]
    
    search_result = client.search(
        collection_name="knowledge_units",
        query_vector=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.product_line.soc_type",
                    match=models.MatchValue(value="Tiger_Lake")
                ),
                models.FieldCondition(
                    key="metadata.execution_result.status",
                    match=models.MatchValue(value="success")
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    
    return search_result

def advanced_hybrid_search(client, query_text, filters, limit=20):
    """混合检索：向量 + 元数据过滤"""
    
    query_vector = generate_embedding(query_text)
    
    # 构建复杂的过滤条件
    must_conditions = []
    
    if filters.get('soc_types'):
        must_conditions.append(
            models.FieldCondition(
                key="metadata.product_line.soc_type",
                match=models.MatchAny(any=filters['soc_types'])
            )
        )
    
    if filters.get('firmware_stacks'):
        must_conditions.append(
            models.FieldCondition(
                key="metadata.product_line.firmware_stack",
                match=models.MatchAny(any=filters['firmware_stacks'])
            )
        )
    
    if filters.get('min_confidence'):
        must_conditions.append(
            models.RangeCondition(
                key="metadata.confidence_score",
                gte=filters['min_confidence']
            )
        )
    
    # 添加日期范围过滤
    if filters.get('date_from'):
        must_conditions.append(
            models.FieldCondition(
                key="metadata.execution_result.execution_time",
                match=models.MatchDatetime(gt=filters['date_from'])
            )
        )
    
    search_result = client.search(
        collection_name="knowledge_units",
        query_vector=query_vector,
        query_filter=models.Filter(must=must_conditions) if must_conditions else None,
        limit=limit,
        with_payload=True,
        with_vectors=False,
        score_threshold=0.7  # 最低相似度阈值
    )
    
    return search_result

# 使用示例
client = QdrantClient(host="localhost", port=6333)

# 1. 基础语义搜索
results = semantic_search_knowledge_units(
    client, 
    "PCIe device enumeration timing issues",
    limit=5
)

# 2. 高级混合搜索
advanced_results = advanced_hybrid_search(
    client,
    "UEFI initialization problems",
    {
        'soc_types': ['Tiger_Lake', 'Alder_Lake'],
        'firmware_stacks': ['UEFI_2.8', 'UEFI_2.9'],
        'min_confidence': 0.8,
        'date_from': '2024-01-01T00:00:00Z'
    },
    limit=10
)
```

### 6.2 PostgreSQL 复杂查询示例

```sql
-- 1. 查找特定产品线的高置信度解决方案
SELECT 
    ku.id,
    ku.title,
    ku.summary,
    ku.confidence_score,
    ku.created_at,
    pl.soc_type,
    pl.firmware_stack,
    array_agg(DISTINCT t.name) as relevant_tags
FROM knowledge_units ku
JOIN product_lines pl ON (
    ku.metadata->'product_line'->>'soc_type' = pl.soc_type 
    AND ku.metadata->'product_line'->>'firmware_stack' = pl.firmware_stack
)
LEFT JOIN knowledge_unit_tags kut ON kut.knowledge_unit_id = ku.id
LEFT JOIN tags t ON t.id = kut.tag_id
WHERE pl.soc_type = 'Tiger_Lake'
  AND pl.firmware_stack = 'UEFI_2.8'
  AND ku.confidence_score >= 0.85
  AND ku.metadata->'execution_result'->>'status' = 'success'
GROUP BY ku.id, ku.title, ku.summary, ku.confidence_score, ku.created_at, pl.soc_type, pl.firmware_stack
ORDER BY ku.confidence_score DESC, ku.created_at DESC
LIMIT 10;

-- 2. 分析测试执行趋势
WITH test_trends AS (
    SELECT 
        DATE_TRUNC('week', te.execution_time) as week,
        te.test_environment,
        COUNT(*) as total_executions,
        COUNT(*) FILTER (WHERE te.execution_status = 'success') as successful_executions,
        ROUND(
            COUNT(*) FILTER (WHERE te.execution_status = 'success') * 100.0 / COUNT(*), 2
        ) as success_rate_percent
    FROM test_executions te
    WHERE te.execution_time >= CURRENT_DATE - INTERVAL '12 weeks'
      AND te.knowledge_unit_id IS NOT NULL
    GROUP BY week, te.test_environment
)
SELECT 
    week,
    test_environment,
    total_executions,
    successful_executions,
    success_rate_percent,
    LAG(success_rate_percent) OVER (PARTITION BY test_environment ORDER BY week) as prev_week_success_rate,
    success_rate_percent - LAG(success_rate_percent) OVER (PARTITION BY test_environment ORDER BY week) as success_rate_change
FROM test_trends
ORDER BY week DESC, test_environment;

-- 3. 查找相关知识单元
WITH similar_units AS (
    SELECT DISTINCT
        ku1.id as source_unit,
        ku2.id as target_unit,
        ku2.title,
        ku2.summary,
        ku2.confidence_score,
        -- 基于标签重叠计算相似度
        (
            SELECT COUNT(*) * 1.0 / 
                   GREATEST(
                       (SELECT COUNT(*) FROM knowledge_unit_tags WHERE knowledge_unit_id = ku1.id),
                       (SELECT COUNT(*) FROM knowledge_unit_tags WHERE knowledge_unit_id = ku2.id)
                   )
            FROM knowledge_unit_tags kut1
            JOIN knowledge_unit_tags kut2 ON kut1.tag_id = kut2.tag_id
            WHERE kut1.knowledge_unit_id = ku1.id 
              AND kut2.knowledge_unit_id = ku2.id
        ) as tag_similarity
    FROM knowledge_units ku1
    JOIN knowledge_unit_tags kut1 ON kut1.knowledge_unit_id = ku1.id
    JOIN knowledge_unit_tags kut2 ON kut2.tag_id = kut1.tag_id
    JOIN knowledge_units ku2 ON ku2.id = kut2.knowledge_unit_id
    WHERE ku1.id = 'ku_20241227_001'
      AND ku2.id != 'ku_20241227_001'
      AND ku2.metadata->'execution_result'->>'status' = 'success'
)
SELECT 
    target_unit,
    title,
    summary,
    confidence_score,
    tag_similarity,
    ROUND(tag_similarity * 100, 2) as similarity_percent
FROM similar_units
WHERE tag_similarity >= 0.3
ORDER BY tag_similarity DESC, confidence_score DESC
LIMIT 5;

-- 4. 产品线问题分布分析
SELECT 
    pl.soc_type,
    pl.firmware_stack,
    COUNT(ku.id) as total_issues,
    COUNT(ku.id) FILTER (WHERE ku.metadata->'execution_result'->>'status' = 'success') as resolved_issues,
    COUNT(ku.id) FILTER (WHERE ku.metadata->'execution_result'->>'status' = 'failure') as unresolved_issues,
    ROUND(
        COUNT(ku.id) FILTER (WHERE ku.metadata->'execution_result'->>'status' = 'success') * 100.0 / 
        NULLIF(COUNT(ku.id), 0), 2
    ) as resolution_rate_percent,
    AVG(ku.confidence_score) as avg_confidence
FROM product_lines pl
LEFT JOIN knowledge_units ku ON (
    ku.metadata->'product_line'->>'soc_type' = pl.soc_type 
    AND ku.metadata->'product_line'->>'firmware_stack' = pl.firmware_stack
)
GROUP BY pl.id, pl.soc_type, pl.firmware_stack
HAVING COUNT(ku.id) > 0
ORDER BY resolution_rate_percent DESC, total_issues DESC;

-- 5. 代码修改模式分析
SELECT 
    change_type,
    COUNT(*) as change_count,
    AVG(lines_added) as avg_lines_added,
    AVG(lines_removed) as avg_lines_removed,
    AVG(confidence_score) as avg_confidence,
    array_agg(DISTINCT soc_type) as affected_soc_types
FROM (
    SELECT 
        ku.change_type,
        ku.lines_added,
        ku.lines_removed,
        ku.confidence_score,
        ku.metadata->'product_line'->>'soc_type' as soc_type
    FROM knowledge_units ku
    WHERE ku.change_type IS NOT NULL
      AND ku.created_at >= CURRENT_DATE - INTERVAL '3 months'
) subquery
GROUP BY change_type
ORDER BY change_count DESC;

-- 6. 最近活跃的知识单元
SELECT 
    ku.id,
    ku.title,
    ku.summary,
    ku.confidence_score,
    ku.created_at,
    ku.updated_at,
    ku.metadata->'product_line'->>'soc_type' as soc_type,
    ku.metadata->'execution_result'->>'status' as status,
    -- 检查是否有最近的关联测试
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM test_executions te 
            WHERE te.knowledge_unit_id = ku.id 
            AND te.created_at >= CURRENT_DATE - INTERVAL '7 days'
        ) THEN 'recently_tested'
        ELSE 'no_recent_test'
    END as test_status
FROM knowledge_units ku
WHERE ku.created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND ku.metadata->'execution_result'->>'status' = 'success'
ORDER BY ku.updated_at DESC, ku.confidence_score DESC
LIMIT 15;
```

### 6.3 组合查询：向量检索 + 关系数据

```python
import psycopg2
from qdrant_client import QdrantClient

def comprehensive_search(query_text, soc_type=None, min_confidence=0.7, limit=10):
    """综合检索：先向量搜索，再关系数据过滤和补充"""
    
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    # 步骤1：向量检索候选结果
    vector_results = qdrant_client.search(
        collection_name="knowledge_units",
        query_vector=generate_embedding(query_text),
        limit=limit * 2,  # 获取更多候选结果进行后续过滤
        with_payload=True
    )
    
    if not vector_results:
        return []
    
    # 步骤2：提取候选IDs
    candidate_ids = [r.id for r in vector_results]
    
    # 步骤3：PostgreSQL关系数据补充
    conn = psycopg2.connect(
        host="localhost",
        database="knowledge_db", 
        user="kb_user",
        password="kb_password"
    )
    
    with conn.cursor() as cur:
        # 获取完整信息
        query = """
        SELECT 
            ku.id,
            ku.title,
            ku.summary,
            ku.description,
            ku.confidence_score,
            ku.metadata,
            ku.created_at,
            pl.soc_type,
            pl.firmware_stack,
            ku.metadata->'execution_result'->>'status' as status,
            array_agg(DISTINCT t.name) as tags
        FROM knowledge_units ku
        LEFT JOIN product_lines pl ON (
            ku.metadata->'product_line'->>'soc_type' = pl.soc_type 
            AND ku.metadata->'product_line'->>'firmware_stack' = pl.firmware_stack
        )
        LEFT JOIN knowledge_unit_tags kut ON kut.knowledge_unit_id = ku.id
        LEFT JOIN tags t ON t.id = kut.tag_id
        WHERE ku.id = ANY(%s)
        """
        
        params = [candidate_ids]
        
        if soc_type:
            query += " AND pl.soc_type = %s"
            params.append(soc_type)
        
        if min_confidence:
            query += " AND ku.confidence_score >= %s"
            params.append(min_confidence)
        
        query += """
        GROUP BY ku.id, ku.title, ku.summary, ku.description, 
                 ku.confidence_score, ku.metadata, ku.created_at, 
                 pl.soc_type, pl.firmware_stack
        ORDER BY ku.confidence_score DESC, ku.created_at DESC
        LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, params)
        results = cur.fetchall()
    
    conn.close()
    
    # 步骤4：结合向量相似度和关系数据置信度进行最终排序
    enhanced_results = []
    for result in results:
        ku_id = result[0]
        
        # 找到对应的向量检索结果
        vector_result = next((r for r in vector_results if r.id == ku_id), None)
        if vector_result:
            enhanced_results.append({
                'id': ku_id,
                'title': result[1],
                'summary': result[2],
                'description': result[3],
                'confidence_score': result[4],
                'metadata': result[5],
                'created_at': result[6],
                'soc_type': result[7],
                'firmware_stack': result[8],
                'status': result[9],
                'tags': result[10] or [],
                'vector_similarity': vector_result.score,  # 向量相似度
                'combined_score': (result[4] + vector_result.score) / 2  # 组合得分
            })
    
    # 按组合得分重新排序
    enhanced_results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return enhanced_results[:limit]

# 使用示例
results = comprehensive_search(
    query_text="PCIe initialization and device enumeration",
    soc_type="Tiger_Lake", 
    min_confidence=0.8,
    limit=5
)

for result in results:
    print(f"ID: {result['id']}")
    print(f"Title: {result['title']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Vector Similarity: {result['vector_similarity']:.3f}")
    print(f"Combined Score: {result['combined_score']:.3f}")
    print(f"Tags: {', '.join(result['tags'])}")
    print("-" * 50)
```

---

## 7. 数据迁移和维护

### 7.1 数据导入脚本

```python
import json
import uuid
from datetime import datetime
from qdrant_client import QdrantClient
import psycopg2

def import_knowledge_units_from_json(file_path):
    """从JSON文件批量导入知识单元"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    # PostgreSQL连接
    pg_conn = psycopg2.connect(
        host="localhost",
        database="knowledge_db",
        user="kb_user", 
        password="kb_password"
    )
    
    try:
        for item in data:
            ku_id = item['id']
            
            # 1. 插入PostgreSQL
            insert_postgresql_knowledge_unit(pg_conn, item)
            
            # 2. 插入Qdrant
            insert_qdrant_knowledge_unit(qdrant_client, item)
            
            print(f"✅ 导入知识单元: {ku_id}")
            
        pg_conn.commit()
        print(f"🎉 成功导入 {len(data)} 个知识单元")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ 导入失败: {e}")
        raise
    finally:
        pg_conn.close()

def insert_postgresql_knowledge_unit(conn, ku_data):
    """插入单个知识单元到PostgreSQL"""
    with conn.cursor() as cur:
        # 插入knowledge_units表
        cur.execute("""
            INSERT INTO knowledge_units (
                id, title, summary, description, change_type, files_modified,
                lines_added, lines_removed, author, confidence_score,
                metadata, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                summary = EXCLUDED.summary, 
                description = EXCLUDED.description,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
        """, (
            ku_data['id'],
            ku_data['content']['title'],
            ku_data['content']['summary'],
            ku_data['content']['description'],
            ku_data['content']['modification_details']['change_type'],
            ku_data['content']['modification_details']['files_modified'],
            ku_data['content']['modification_details']['lines_added'],
            ku_data['content']['modification_details']['lines_removed'],
            ku_data['metadata']['author'],
            ku_data['metadata']['confidence_score'],
            json.dumps(ku_data['metadata']),
            ku_data['audit']['created_at'],
            ku_data['audit']['updated_at']
        ))
        
        # 插入代码片段
        for snippet in ku_data['content']['code_snippets']:
            cur.execute("""
                INSERT INTO code_snippets (
                    knowledge_unit_id, file_path, function_name, language, content
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                ku_data['id'],
                snippet['file_path'],
                snippet.get('function'),
                snippet['language'],
                snippet['content']
            ))

def insert_qdrant_knowledge_unit(client, ku_data):
    """插入单个知识单元到Qdrant"""
    
    client.upsert(
        collection_name="knowledge_units",
        points=[models.PointStruct(
            id=ku_data['id'],
            vector=ku_data['vector_embedding']['vector'],
            payload={
                'metadata': ku_data['metadata'],
                'title': ku_data['content']['title'],
                'summary': ku_data['content']['summary']
            }
        )]
    )

# 执行导入
# import_knowledge_units_from_json('/data/knowledge_units_export.json')
```

### 7.2 数据维护脚本

```python
def cleanup_orphaned_data():
    """清理孤立的测试执行记录和关联数据"""
    
    conn = psycopg2.connect(
        host="localhost",
        database="knowledge_db",
        user="kb_user",
        password="kb_password"
    )
    
    try:
        with conn.cursor() as cur:
            # 删除没有知识单元关联的测试执行记录
            cur.execute("""
                DELETE FROM test_executions 
                WHERE knowledge_unit_id IS NOT NULL 
                AND knowledge_unit_id NOT IN (SELECT id FROM knowledge_units)
            """)
            
            # 删除没有知识单元关联的标签关联
            cur.execute("""
                DELETE FROM knowledge_unit_tags 
                WHERE knowledge_unit_id NOT IN (SELECT id FROM knowledge_units)
            """)
            
            # 删除没有知识单元关联的迭代记录
            cur.execute("""
                DELETE FROM iteration_records 
                WHERE knowledge_unit_id NOT IN (SELECT id FROM knowledge_units)
            """)
            
            deleted_count = cur.rowcount
            print(f"🧹 清理了 {deleted_count} 条孤立记录")
            
        conn.commit()
        
    finally:
        conn.close()

def update_confidence_scores():
    """更新知识单元的置信度分数"""
    
    conn = psycopg2.connect(
        host="localhost", 
        database="knowledge_db",
        user="kb_user",
        password="kb_password"
    )
    
    try:
        with conn.cursor() as cur:
            # 基于执行结果更新置信度
            cur.execute("""
                UPDATE knowledge_units 
                SET confidence_score = 
                    CASE 
                        WHEN metadata->'execution_result'->>'status' = 'success' THEN 
                            LEAST(0.95, confidence_score + 0.1)
                        WHEN metadata->'execution_result'->>'status' = 'failure' THEN
                            GREATEST(0.1, confidence_score - 0.1)
                        ELSE confidence_score
                    END
                WHERE metadata->'execution_result'->>'status' IS NOT NULL
            """)
            
            updated_count = cur.rowcount
            print(f"📊 更新了 {updated_count} 个置信度分数")
            
        conn.commit()
        
    finally:
        conn.close()

def generate_usage_report():
    """生成知识库使用报告"""
    
    conn = psycopg2.connect(
        host="localhost",
        database="knowledge_db", 
        user="kb_user",
        password="kb_password"
    )
    
    try:
        with conn.cursor() as cur:
            # 整体统计
            cur.execute("SELECT COUNT(*) FROM knowledge_units")
            total_units = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM knowledge_units WHERE confidence_score >= 0.8")
            high_confidence = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM test_executions WHERE execution_status = 'success'")
            successful_tests = cur.fetchone()[0]
            
            print("📈 知识库使用报告")
            print("=" * 40)
            print(f"总知识单元数: {total_units}")
            print(f"高置信度单元: {high_confidence} ({high_confidence/total_units*100:.1f}%)")
            print(f"成功测试数: {successful_tests}")
            
            # 按产品线统计
            cur.execute("""
                SELECT 
                    metadata->'product_line'->>'soc_type' as soc_type,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM knowledge_units
                GROUP BY metadata->'product_line'->>'soc_type'
                ORDER BY count DESC
            """)
            
            print("\n🔧 按SoC类型统计:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]} 单元, 平均置信度: {row[2]:.2f}")
                
    finally:
        conn.close()

# 执行维护任务
if __name__ == "__main__":
    print("开始数据维护...")
    cleanup_orphaned_data()
    update_confidence_scores()
    generate_usage_report()
    print("数据维护完成!")
```

---

## 8. 性能优化建议

### 8.1 Qdrant 性能优化

```python
# 优化配置
OPTIMIZATION_CONFIG = {
    # 索引优化
    "indexing_threshold": 20000,  # 自动索引的条目阈值
    "max_optimization_threads": 4,
    
    # 内存优化  
    "memmap_threshold_kb": 100,  # 内存映射阈值
    "max_search_threads": 4,     # 并行搜索线程数
    
    # HNSW参数优化
    "hnsw_m": 16,                # 连接数，影响搜索精度和内存
    "hnsw_ef_construct": 100,    # 构建时的搜索范围
    "hnsw_full_scan_threshold": 10000,  # 全表扫描阈值
}

# 监控查询性能
def monitor_qdrant_performance(client):
    """监控Qdrant性能指标"""
    
    collection_info = client.get_collection("knowledge_units")
    
    print("📊 Qdrant 性能指标")
    print("=" * 30)
    print(f"向量数量: {collection_info.vectors_count}")
    print(f"索引状态: {collection_info.indexed_vectors_count}")
    print(f"段数量: {collection_info.segments_count}")
    print(f"状态: {collection_info.status}")
```

### 8.2 PostgreSQL 性能优化

```sql
-- 分区表（按月分区）
CREATE TABLE knowledge_units_partitioned (
    LIKE knowledge_units INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建月度分区
CREATE TABLE knowledge_units_2024_12 PARTITION OF knowledge_units_partitioned
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 查询优化配置
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- 启用并行查询
ALTER SYSTEM SET max_parallel_workers = 4;
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;
```

---

本文档提供了完整的知识库数据结构设计方案，包含300+行详细规范，涵盖了数据模型、存储架构、查询示例和性能优化策略。设计支持高效的语义检索、结构化数据管理和产品线差异化查询，为AI驱动的固件测试系统提供了坚实的数据基础。