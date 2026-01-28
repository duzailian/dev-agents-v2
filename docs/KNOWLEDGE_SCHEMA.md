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

## 3.4 产品线隔离与检索策略

### 3.4.1 ProductLineProfile数据模型

为解决多产品线知识库的高效检索问题，设计了ProductLineProfile模型：

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum
import json

class CompatibilityLevel(Enum):
    """产品线兼容性级别"""
    EXACT = "exact"           # 完全匹配
    FAMILY = "family"         # 同系列产品兼容
    ARCH = "architecture"      # 架构级兼容
    GENERIC = "generic"       # 通用解决方案

@dataclass
class ProductLineProfile:
    """产品线档案"""
    profile_id: str
    product_line_tags: Dict[str, Union[str, List[str]]]
    retrieval_priority: int  # 1-10, 10为最高
    weight_multipliers: Dict[str, float]
    compatibility_matrix: Dict[str, CompatibilityLevel]
    
    # 检索性能优化
    cache_ttl: int = 3600  # 缓存时间（秒）
    max_candidates: int = 100  # 最大候选结果数
    
    # 质量控制
    min_confidence_score: float = 0.7
    required_success_rate: float = 0.8
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "profile_id": self.profile_id,
            "product_line_tags": self.product_line_tags,
            "retrieval_priority": self.retrieval_priority,
            "weight_multipliers": self.weight_multipliers,
            "compatibility_matrix": {
                k: v.value for k, v in self.compatibility_matrix.items()
            },
            "cache_ttl": self.cache_ttl,
            "max_candidates": self.max_candidates,
            "min_confidence_score": self.min_confidence_score,
            "required_success_rate": self.required_success_rate
        }

# 典型产品线档案示例
TIGER_LAKE_PROFILE = ProductLineProfile(
    profile_id="tiger_lake_uefi_server",
    product_line_tags={
        "soc_type": "Tiger_Lake",
        "firmware_stack": "UEFI_2.8",
        "chipset": ["HM570", "WM590"],
        "platform": "Server"
    },
    retrieval_priority=9,
    weight_multipliers={
        "soc_type": 1.0,
        "firmware_stack": 0.9,
        "chipset": 0.8,
        "platform": 0.7
    },
    compatibility_matrix={
        "Tiger_Lake": CompatibilityLevel.EXACT,
        "Alder_Lake": CompatibilityLevel.FAMILY,
        "Generic_x86_64": CompatibilityLevel.ARCH,
        "UEFI_2.9": CompatibilityLevel.FAMILY,
        "EDK2": CompatibilityLevel.ARCH
    },
    cache_ttl=7200,  # 2小时缓存
    max_candidates=50,
    min_confidence_score=0.8,
    required_success_rate=0.85
)

EPYC_PROFILE = ProductLineProfile(
    profile_id="epyc_bmc_server",
    product_line_tags={
        "soc_type": "EPYC_Milan",
        "firmware_stack": ["OpenBMC", "UEFI_2.8"],
        "chipset": ["TRX40", "X570"],
        "platform": "Server"
    },
    retrieval_priority=10,
    weight_multipliers={
        "soc_type": 1.0,
        "firmware_stack": 0.95,
        "chipset": 0.75,
        "platform": 0.6
    },
    compatibility_matrix={
        "EPYC_Milan": CompatibilityLevel.EXACT,
        "EPYC_Genoa": CompatibilityLevel.FAMILY,
        "EPYC_Bergamo": CompatibilityLevel.FAMILY,
        "OpenBMC": CompatibilityLevel.EXACT,
        "IPMI": CompatibilityLevel.FAMILY
    },
    cache_ttl=10800,  # 3小时缓存
    max_candidates=80,
    min_confidence_score=0.85,
    required_success_rate=0.9
)

GENERIC_PROFILE = ProductLineProfile(
    profile_id="generic_x86_64",
    product_line_tags={
        "soc_type": "Generic_x86_64",
        "firmware_stack": "Generic",
        "platform": "Generic"
    },
    retrieval_priority=1,
    weight_multipliers={
        "soc_type": 0.5,
        "firmware_stack": 0.4,
        "platform": 0.3
    },
    compatibility_matrix={
        "Generic_x86_64": CompatibilityLevel.EXACT,
        "Generic": CompatibilityLevel.EXACT
    },
    cache_ttl=1800,  # 30分钟缓存
    max_candidates=20,
    min_confidence_score=0.6,
    required_success_rate=0.7
)
```

### 3.4.2 ProductLineMatcher算法

```python
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass

@dataclass
class MatchResult:
    """匹配结果"""
    knowledge_unit_id: str
    similarity_score: float
    compatibility_level: CompatibilityLevel
    matched_tags: Dict[str, str]
    confidence_adjustment: float

class ProductLineMatcher:
    """产品线匹配器"""
    
    def __init__(self, profile: ProductLineProfile):
        self.profile = profile
        self.tag_weights = profile.weight_multipliers
        
    def calculate_tag_similarity(self, 
                                unit_tags: Dict[str, str], 
                                profile_tags: Dict[str, Union[str, List[str]]]) -> float:
        """计算标签相似度"""
        total_weight = 0.0
        weighted_score = 0.0
        
        for tag_type, profile_value in profile_tags.items():
            if tag_type not in unit_tags:
                continue
                
            weight = self.tag_weights.get(tag_type, 0.5)
            unit_value = unit_tags[tag_type]
            
            # 精确匹配
            if isinstance(profile_value, str):
                if unit_value == profile_value:
                    weighted_score += weight * 1.0
                elif unit_value in self.profile.compatibility_matrix:
                    compatibility = self.profile.compatibility_matrix[unit_value]
                    weighted_score += weight * self._get_compatibility_score(compatibility)
                else:
                    weighted_score += weight * 0.0
            
            # 列表匹配
            elif isinstance(profile_value, list):
                if unit_value in profile_value:
                    weighted_score += weight * 1.0
                else:
                    # 查找兼容性
                    for compatible_value in profile_value:
                        if compatible_value in self.profile.compatibility_matrix:
                            compatibility = self.profile.compatibility_matrix[compatible_value]
                            weighted_score += weight * self._get_compatibility_score(compatibility)
                            break
                    else:
                        weighted_score += weight * 0.0
            
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _get_compatibility_score(self, level: CompatibilityLevel) -> float:
        """获取兼容性评分"""
        compatibility_scores = {
            CompatibilityLevel.EXACT: 1.0,
            CompatibilityLevel.FAMILY: 0.8,
            CompatibilityLevel.ARCH: 0.6,
            CompatibilityLevel.GENERIC: 0.4
        }
        return compatibility_scores.get(level, 0.0)
    
    def match_knowledge_unit(self, unit: Dict) -> MatchResult:
        """匹配单个知识单元"""
        unit_tags = unit.get("metadata", {}).get("product_line", {})
        
        # 计算相似度
        similarity_score = self.calculate_tag_similarity(unit_tags, self.profile.product_line_tags)
        
        # 确定兼容性级别
        compatibility_level = self._determine_compatibility_level(unit_tags)
        
        # 识别匹配的标签
        matched_tags = self._find_matched_tags(unit_tags)
        
        # 计算置信度调整
        confidence_adjustment = self._calculate_confidence_adjustment(
            similarity_score, compatibility_level
        )
        
        return MatchResult(
            knowledge_unit_id=unit.get("id"),
            similarity_score=similarity_score,
            compatibility_level=compatibility_level,
            matched_tags=matched_tags,
            confidence_adjustment=confidence_adjustment
        )
    
    def _determine_compatibility_level(self, unit_tags: Dict[str, str]) -> CompatibilityLevel:
        """确定兼容性级别"""
        soc_type = unit_tags.get("soc_type")
        if soc_type and soc_type in self.profile.compatibility_matrix:
            return self.profile.compatibility_matrix[soc_type]
        
        # 检查 firmware_stack 兼容性
        firmware_stack = unit_tags.get("firmware_stack")
        if firmware_stack and firmware_stack in self.profile.compatibility_matrix:
            return self.profile.compatibility_matrix[firmware_stack]
        
        return CompatibilityLevel.GENERIC
    
    def _find_matched_tags(self, unit_tags: Dict[str, str]) -> Dict[str, str]:
        """查找匹配的标签"""
        matched = {}
        for tag_type, unit_value in unit_tags.items():
            profile_value = self.profile.product_line_tags.get(tag_type)
            
            if isinstance(profile_value, str) and unit_value == profile_value:
                matched[tag_type] = unit_value
            elif isinstance(profile_value, list) and unit_value in profile_value:
                matched[tag_type] = unit_value
            elif unit_value in self.profile.compatibility_matrix:
                matched[tag_type] = unit_value
        
        return matched
    
    def _calculate_confidence_adjustment(self, 
                                       similarity_score: float, 
                                       compatibility_level: CompatibilityLevel) -> float:
        """计算置信度调整"""
        base_adjustment = {
            CompatibilityLevel.EXACT: 1.0,
            CompatibilityLevel.FAMILY: 0.9,
            CompatibilityLevel.ARCH: 0.8,
            CompatibilityLevel.GENERIC: 0.6
        }.get(compatibility_level, 0.5)
        
        # 基于相似度进一步调整
        return base_adjustment * similarity_score

def batch_match_knowledge_units(units: List[Dict], 
                              profile: ProductLineProfile,
                              min_score: float = 0.3) -> List[MatchResult]:
    """批量匹配知识单元"""
    matcher = ProductLineMatcher(profile)
    results = []
    
    for unit in units:
        try:
            result = matcher.match_knowledge_unit(unit)
            if result.similarity_score >= min_score:
                results.append(result)
        except Exception as e:
            print(f"匹配知识单元 {unit.get('id', 'unknown')} 时出错: {e}")
            continue
    
    # 按相似度排序
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    return results
```

### 3.4.3 RetrievalStrategy配置

```python
from enum import Enum
from typing import Callable, Dict, Any
import time
import hashlib

class RetrievalMode(Enum):
    """检索模式"""
    STRICT = "strict"          # 严格匹配
    BALANCED = "balanced"      # 平衡模式
    BROAD = "broad"           # 宽泛匹配
    EXPLORATORY = "exploratory"  # 探索性检索

class CacheStrategy(Enum):
    """缓存策略"""
    NONE = "none"
    MEMORY = "memory"
    PERSISTENT = "persistent"
    HYBRID = "hybrid"

@dataclass
class RetrievalStrategy:
    """检索策略配置"""
    strategy_id: str
    mode: RetrievalMode
    cache_strategy: CacheStrategy
    max_results: int = 50
    timeout_seconds: int = 30
    
    # 检索路径配置
    retrieval_paths: List[str] = None
    
    # 动态参数
    confidence_threshold: float = 0.7
    similarity_threshold: float = 0.6
    
    # 性能优化
    enable_parallel_search: bool = True
    max_concurrent_requests: int = 5
    
    # 质量控制
    min_success_rate: float = 0.8
    max_age_days: int = 365
    
    def __post_init__(self):
        if self.retrieval_paths is None:
            self.retrieval_paths = [
                "exact_match",
                "family_match", 
                "architecture_match",
                "generic_match"
            ]
    
    def get_cache_key(self, query: str, profile_id: str) -> str:
        """生成缓存键"""
        content = f"{query}:{profile_id}:{self.strategy_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def should_use_cache(self) -> bool:
        """判断是否使用缓存"""
        return self.cache_strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID, CacheStrategy.PERSISTENT]

# 预定义检索策略
STRICT_RETRIEVAL = RetrievalStrategy(
    strategy_id="strict_tiger_lake",
    mode=RetrievalMode.STRICT,
    cache_strategy=CacheStrategy.PERSISTENT,
    max_results=20,
    confidence_threshold=0.8,
    similarity_threshold=0.7,
    min_success_rate=0.9,
    retrieval_paths=["exact_match", "family_match"]
)

BALANCED_RETRIEVAL = RetrievalStrategy(
    strategy_id="balanced_server",
    mode=RetrievalMode.BALANCED,
    cache_strategy=CacheStrategy.HYBRID,
    max_results=50,
    confidence_threshold=0.7,
    similarity_threshold=0.6,
    min_success_rate=0.8,
    enable_parallel_search=True,
    max_concurrent_requests=3
)

BROAD_RETRIEVAL = RetrievalStrategy(
    strategy_id="broad_exploration",
    mode=RetrievalMode.BROAD,
    cache_strategy=CacheStrategy.MEMORY,
    max_results=100,
    confidence_threshold=0.5,
    similarity_threshold=0.4,
    min_success_rate=0.6,
    retrieval_paths=["exact_match", "family_match", "architecture_match", "generic_match"]
)

class KnowledgeRetrievalEngine:
    """知识检索引擎"""
    
    def __init__(self, profile: ProductLineProfile, strategy: RetrievalStrategy):
        self.profile = profile
        self.strategy = strategy
        self.cache = {} if strategy.cache_strategy != CacheStrategy.NONE else None
        
    async def retrieve_knowledge(self, 
                                query_text: str, 
                                additional_filters: Dict = None) -> List[Dict]:
        """检索知识"""
        start_time = time.time()
        
        # 检查缓存
        if self.strategy.should_use_cache():
            cache_key = self.strategy.get_cache_key(query_text, self.profile.profile_id)
            if cache_key in self.cache:
                print(f"缓存命中: {cache_key}")
                return self.cache[cache_key]
        
        # 执行检索
        results = await self._execute_retrieval(query_text, additional_filters)
        
        # 应用质量过滤
        filtered_results = self._apply_quality_filters(results)
        
        # 缓存结果
        if self.strategy.should_use_cache():
            cache_key = self.strategy.get_cache_key(query_text, self.profile.profile_id)
            self.cache[cache_key] = filtered_results
        
        retrieval_time = time.time() - start_time
        print(f"检索完成: {len(filtered_results)} 个结果，耗时 {retrieval_time:.2f}s")
        
        return filtered_results
    
    async def _execute_retrieval(self, 
                                query_text: str, 
                                additional_filters: Dict = None) -> List[Dict]:
        """执行具体检索逻辑"""
        # 这里是检索的核心实现
        # 需要集成向量检索和关系数据库查询
        # 示例实现：
        
        results = []
        
        # 1. 向量检索
        vector_results = await self._vector_search(query_text)
        results.extend(vector_results)
        
        # 2. 产品线匹配
        matched_results = await self._apply_product_line_matching(results)
        results = matched_results
        
        # 3. 应用额外过滤
        if additional_filters:
            results = self._apply_additional_filters(results, additional_filters)
        
        return results
    
    async def _vector_search(self, query_text: str) -> List[Dict]:
        """向量搜索（模拟实现）"""
        # 实际实现中会调用Qdrant
        print(f"执行向量搜索: {query_text}")
        return []
    
    async def _apply_product_line_matching(self, candidates: List[Dict]) -> List[Dict]:
        """应用产品线匹配"""
        if not candidates:
            return []
        
        # 使用ProductLineMatcher进行匹配
        matcher = ProductLineMatcher(self.profile)
        match_results = []
        
        for candidate in candidates:
            try:
                match_result = matcher.match_knowledge_unit(candidate)
                # 调整置信度
                original_confidence = candidate.get("metadata", {}).get("confidence_score", 0.5)
                adjusted_confidence = original_confidence * match_result.confidence_adjustment
                
                candidate["metadata"]["confidence_score"] = adjusted_confidence
                candidate["metadata"]["similarity_score"] = match_result.similarity_score
                candidate["metadata"]["compatibility_level"] = match_result.compatibility_level.value
                candidate["metadata"]["matched_tags"] = match_result.matched_tags
                
                match_results.append(candidate)
            except Exception as e:
                print(f"匹配知识单元 {candidate.get('id', 'unknown')} 时出错: {e}")
                continue
        
        # 按相似度和置信度排序
        match_results.sort(
            key=lambda x: (
                x.get("metadata", {}).get("similarity_score", 0),
                x.get("metadata", {}).get("confidence_score", 0)
            ),
            reverse=True
        )
        
        return match_results[:self.strategy.max_results]
    
    def _apply_quality_filters(self, results: List[Dict]) -> List[Dict]:
        """应用质量过滤"""
        filtered = []
        
        for result in results:
            metadata = result.get("metadata", {})
            
            # 置信度过滤
            confidence = metadata.get("confidence_score", 0)
            if confidence < self.strategy.confidence_threshold:
                continue
            
            # 相似度过滤
            similarity = metadata.get("similarity_score", 0)
            if similarity < self.strategy.similarity_threshold:
                continue
            
            # 成功率过滤
            execution_result = metadata.get("execution_result", {})
            success_rate = execution_result.get("success_rate", 0)
            if success_rate < self.strategy.min_success_rate:
                continue
            
            # 年龄过滤
            execution_time = execution_result.get("execution_time")
            if execution_time:
                age_days = (time.time() - execution_time.timestamp()) / (24 * 3600)
                if age_days > self.strategy.max_age_days:
                    continue
            
            filtered.append(result)
        
        return filtered[:self.strategy.max_results]
    
    def _apply_additional_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """应用额外过滤条件"""
        filtered = results
        
        for filter_key, filter_value in filters.items():
            filtered = [
                result for result in filtered
                if self._matches_filter(result, filter_key, filter_value)
            ]
        
        return filtered
    
    def _matches_filter(self, result: Dict, filter_key: str, filter_value: Any) -> bool:
        """检查是否匹配过滤条件"""
        # 简化的过滤逻辑实现
        # 实际中需要更复杂的过滤规则
        return True
```

### 3.4.4 检索性能指标

```python
@dataclass
class RetrievalMetrics:
    """检索性能指标"""
    total_results: int
    retrieval_time: float
    cache_hit_rate: float
    avg_confidence: float
    avg_similarity: float
    success_rate: float
    
    # 分布指标
    confidence_distribution: Dict[str, int]  # high/medium/low
    compatibility_distribution: Dict[str, int]
    
    # 性能指标
    throughput: float  # 结果/秒
    memory_usage: float  # MB
    cache_size: int

def calculate_retrieval_metrics(results: List[Dict], 
                              retrieval_time: float,
                              cache_info: Dict = None) -> RetrievalMetrics:
    """计算检索指标"""
    if not results:
        return RetrievalMetrics(
            total_results=0,
            retrieval_time=retrieval_time,
            cache_hit_rate=cache_info.get("hit_rate", 0) if cache_info else 0,
            avg_confidence=0,
            avg_similarity=0,
            success_rate=0,
            confidence_distribution={"high": 0, "medium": 0, "low": 0},
            compatibility_distribution={},
            throughput=0,
            memory_usage=0,
            cache_size=cache_info.get("size", 0) if cache_info else 0
        )
    
    # 计算基础指标
    confidences = [r.get("metadata", {}).get("confidence_score", 0) for r in results]
    similarities = [r.get("metadata", {}).get("similarity_score", 0) for r in results]
    
    avg_confidence = sum(confidences) / len(confidences)
    avg_similarity = sum(similarities) / len(similarities)
    
    # 计算分布
    confidence_dist = {"high": 0, "medium": 0, "low": 0}
    for conf in confidences:
        if conf >= 0.8:
            confidence_dist["high"] += 1
        elif conf >= 0.5:
            confidence_dist["medium"] += 1
        else:
            confidence_dist["low"] += 1
    
    compatibility_dist = {}
    for result in results:
        comp_level = result.get("metadata", {}).get("compatibility_level", "unknown")
        compatibility_dist[comp_level] = compatibility_dist.get(comp_level, 0) + 1
    
    # 计算成功率
    success_rates = [
        r.get("metadata", {}).get("execution_result", {}).get("success_rate", 0)
        for r in results
    ]
    success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
    
    # 计算吞吐量
    throughput = len(results) / retrieval_time if retrieval_time > 0 else 0
    
    return RetrievalMetrics(
        total_results=len(results),
        retrieval_time=retrieval_time,
        cache_hit_rate=cache_info.get("hit_rate", 0) if cache_info else 0,
        avg_confidence=avg_confidence,
        avg_similarity=avg_similarity,
        success_rate=success_rate,
        confidence_distribution=confidence_dist,
        compatibility_distribution=compatibility_dist,
        throughput=throughput,
        memory_usage=0,  # 需要实际测量
        cache_size=cache_info.get("size", 0) if cache_info else 0
    )
```

### 3.4.5 使用示例

```python
# 完整的使用示例
async def example_usage():
    """使用示例"""
    
    # 1. 选择产品线档案
    profile = TIGER_LAKE_PROFILE
    
    # 2. 选择检索策略
    strategy = BALANCED_RETRIEVAL
    
    # 3. 创建检索引擎
    engine = KnowledgeRetrievalEngine(profile, strategy)
    
    # 4. 执行检索
    query = "PCIe设备初始化问题"
    additional_filters = {
        "status": "success",
        "min_confidence": 0.8
    }
    
    results = await engine.retrieve_knowledge(query, additional_filters)
    
    # 5. 分析结果
    print(f"检索到 {len(results)} 个相关知识单元")
    
    for i, result in enumerate(results[:5]):  # 显示前5个结果
        metadata = result.get("metadata", {})
        print(f"\n结果 {i+1}:")
        print(f"  ID: {result.get('id')}")
        print(f"  标题: {result.get('content', {}).get('title', 'N/A')}")
        print(f"  置信度: {metadata.get('confidence_score', 0):.3f}")
        print(f"  相似度: {metadata.get('similarity_score', 0):.3f}")
        print(f"  兼容性: {metadata.get('compatibility_level', 'N/A')}")
        print(f"  匹配标签: {metadata.get('matched_tags', {})}")
        
        # 显示相关性评分
        relevance_score = (
            metadata.get('confidence_score', 0) * 0.6 +
            metadata.get('similarity_score', 0) * 0.4
        )
        print(f"  综合相关性: {relevance_score:.3f}")
    
    # 6. 计算性能指标
    metrics = calculate_retrieval_metrics(results, 0.5)  # 假设检索耗时0.5秒
    print(f"\n检索性能指标:")
    print(f"  总结果数: {metrics.total_results}")
    print(f"  平均置信度: {metrics.avg_confidence:.3f}")
    print(f"  平均相似度: {metrics.avg_similarity:.3f}")
    print(f"  成功率: {metrics.success_rate:.3f}")
    print(f"  吞吐量: {metrics.throughput:.2f} 结果/秒")
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