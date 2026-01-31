# AI驱动固件智能测试系统 — 配置管理设计文档

> 文档版本：v2.0
>
> 创建时间：2024年
>
> 更新频率：根据系统演进定期更新
>
> 目标：建立统一的配置管理体系，确保系统配置的可维护性、安全性和一致性

---

## 1. 文档概述

### 1.1 文档目的

本文档旨在为AI驱动固件智能测试系统提供完整的配置管理规范，包括：

- **配置分层机制**：建立清晰的配置优先级体系
- **配置分类管理**：按功能域划分配置类别
- **配置加载流程**：定义配置获取和验证的标准流程
- **配置安全规范**：确保敏感配置的安全存储和访问
- **配置最佳实践**：提供配置管理的最佳实践指导

### 1.2 适用范围

本文档适用于以下配置场景：

- 系统运行参数的集中管理
- 多环境部署配置管理（开发、测试、生产）
- 第三方服务集成的配置管理
- 测试环境和硬件适配的配置管理
- 安全认证和权限管理的配置管理

### 1.3 目标受众

- 系统架构师和设计人员
- 后端开发工程师
- DevOps工程师
- 测试工程师
- 运维工程师

---

## 2. 配置分层架构

### 2.1 配置优先级层次

配置管理采用明确的分层结构，确保配置的可控性和可预测性：

```mermaid
graph TD
    A[运行时API调用覆盖<br/>优先级: 1 - 最高] --> B[命令行参数<br/>优先级: 2]
    B --> C[配置文件<br/>优先级: 3]
    C --> D[环境变量<br/>优先级: 4]
    D --> E[硬编码默认值<br/>优先级: 5 - 最低]
    
    style A fill:#ff6b6b,color:#fff
    style B fill:#ffa726,color:#fff
    style C fill:#42a5f5,color:#fff
    style D fill:#66bb6a,color:#fff
    style E fill:#9e9e9e,color:#fff
```

### 2.2 配置层级详解

#### 2.2.1 硬编码默认值（优先级：5）

**描述**：系统内置的默认配置值，优先级最低

**特点**：
- 提供系统运行的基本配置
- 确保系统在无任何外部配置时能正常启动
- 定义合理的保守默认值

**配置位置**：
```python
# src/core/config/defaults.py
DEFAULT_CONFIG = {
    "app": {
        "name": "AI-Firmware-Tester",
        "version": "1.0.0",
        "debug": False,
        "log_level": "INFO",
        "max_workers": 4
    },
    "execution": {
        "default_env": "qemu",
        "timeout": 300,
        "retries": 3,
        "parallel_tasks": 2
    }
}
```

#### 2.2.2 系统环境变量（优先级：4）

**描述**：通过操作系统环境变量传递的配置

**命名规范**：
- 使用前缀 `AFT_` (AI-Firmware-Tester)
- 使用下划线分隔单词
- 使用大写字母

**常用环境变量**：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `AFT_PYTHON_INSTALL_MIRROR` | Python安装镜像 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| `AFT_DEBUG` | 调试模式 | `true`/`false` |
| `AFT_LOG_LEVEL` | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `AFT_MAX_WORKERS` | 最大工作线程数 | `8` |
| `AFT_CONFIG_PATH` | 配置文件路径 | `/etc/aft/config.yaml` |
| `AFT_DATA_DIR` | 数据目录 | `/var/lib/aft` |
| `AFT_LOG_DIR` | 日志目录 | `/var/log/aft` |
| `AFT_REDMINE_URL` | Redmine服务URL | `https://redmine.company.com` |
| `AFT_REDMINE_API_KEY` | Redmine API密钥 | `your_api_key_here` |
| `AFT_GITLAB_URL` | GitLab服务URL | `https://gitlab.company.com` |
| `AFT_GITLAB_TOKEN` | GitLab访问令牌 | `your_gitlab_token_here` |
| `AFT_MODEL_API_URL` | 大模型API地址 | `https://api.openai.com` |
| `AFT_MODEL_API_KEY` | 大模型API密钥 | `your_model_api_key` |
| `AFT_QEMU_PATH` | QEMU可执行文件路径 | `/usr/bin/qemu-system-aarch64` |
| `AFT_BOARD_IP` | 目标板IP地址 | `192.168.1.100` |
| `AFT_BMC_IP` | BMC控制器IP地址 | `192.168.1.200` |
| `AFT_BMC_USERNAME` | BMC用户名 | `admin` |
| `AFT_BMC_PASSWORD` | BMC密码 | `your_bmc_password` |
| `AFT_DATABASE_URL` | 数据库连接URL | `postgresql://user:pass@localhost/aft` |
| `AFT_VECTOR_DB_URL` | 向量数据库URL | `http://localhost:6333` |
| `AFT_CACHE_URL` | 缓存服务URL | `redis://localhost:6379/0` |

**环境变量配置示例**：
```bash
# .env 文件示例
AFT_DEBUG=true
AFT_LOG_LEVEL=DEBUG
AFT_REDMINE_URL=https://redmine.company.com
AFT_REDMINE_API_KEY=sk-1234567890abcdef
AFT_GITLAB_URL=https://gitlab.company.com
AFT_GITLAB_TOKEN=glpat-1234567890abcdef
AFT_MODEL_API_KEY=sk-1234567890abcdef
AFT_QEMU_PATH=/usr/bin/qemu-system-aarch64
AFT_BOARD_IP=192.168.1.100
```

#### 2.2.3 配置文件（优先级：3）

**描述**：YAML格式的配置文件，支持分层配置和环境差异化

**配置文件结构**：
```
config/
├── app.yaml          # 主配置文件
├── env/              # 环境特定配置
│   ├── development.yaml
│   ├── testing.yaml
│   └── production.yaml
├── agents/           # Agent特定配置
│   ├── code_agent.yaml
│   ├── test_agent.yaml
│   ├── analysis_agent.yaml
│   └── kb_agent.yaml
├── integrations/     # 集成服务配置
│   ├── redmine.yaml
│   ├── gitlab.yaml
│   ├── model.yaml
│   └── storage.yaml
└── environments/     # 测试环境配置
    ├── qemu.yaml
    ├── board.yaml
    └── bmc.yaml
```

**主配置文件示例**：
```yaml
# config/app.yaml
app:
  name: "AI-Firmware-Tester"
  version: "1.0.0"
  debug: false
  environment: "production"  # development, testing, production
  
# 日志配置
logging:
  level: "INFO"
  format: "json"  # json, plain
  output: "stdout"  # stdout, file
  file:
    path: "/var/log/aft/app.log"
    max_size: "100MB"
    retention: "30d"
  
# 执行配置
execution:
  default_env: "qemu"
  timeout: 300
  retries: 3
  parallel_tasks: 2
  workspace: "/tmp/aft-workspace"
  
# Agent配置
agents:
  code_agent:
    model: "gpt-4-turbo-preview"
    temperature: 0.1
    max_tokens: 2000
    timeout: 120
    retries: 2
    
  test_agent:
    timeout: 600
    retries: 3
    env_vars: {}
    
  analysis_agent:
    confidence_threshold: 0.8
    max_history: 10
    
  kb_agent:
    similarity_threshold: 0.7
    max_results: 5
    
# 数据库配置
database:
  postgres:
    url: "postgresql://user:password@localhost/aft"
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
    
  qdrant:
    url: "http://localhost:6333"
    collection_name: "firmware_knowledge"
    embedding_model: "all-MiniLM-L6-v2"
    
# 缓存配置
cache:
  redis:
    url: "redis://localhost:6379/0"
    default_timeout: 3600
    max_connections: 20
    
# 集成服务配置
integrations:
  redmine:
    enabled: true
    url: "https://redmine.company.com"
    project_id: "firmware-testing"
    
  gitlab:
    enabled: true
    url: "https://gitlab.company.com"
    default_branch: "main"
    
  model:
    provider: "openai"  # openai, azure, local
    api_base: "https://api.openai.com/v1"
    timeout: 60
    
# 安全配置
security:
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
    
  authentication:
    session_timeout: 3600
    max_login_attempts: 5
    
# 监控配置
monitoring:
  metrics:
    enabled: true
    port: 9090
    
  health_check:
    enabled: true
    port: 8080
    path: "/health"
```

#### 2.2.4 命令行参数（优先级：2）

**描述**：通过命令行界面传递的配置参数

**CLI参数规范**：
```bash
# 基础命令
aft --config /path/to/config.yaml --debug --log-level DEBUG

# 测试执行命令
aft test run \
  --target qemu \
  --timeout 300 \
  --retries 3 \
  --parallel 2 \
  --workspace /tmp/test-workspace

# 代码分析命令
aft code analyze \
  --model gpt-4 \
  --temperature 0.1 \
  --max-tokens 2000

# 环境配置命令
aft env set BOARD_IP=192.168.1.100 \
  BMC_IP=192.168.1.200 \
  BMC_USERNAME=admin \
  BMC_PASSWORD=secret

# 集成服务配置命令
aft config set redmine.url=https://redmine.company.com \
  redmine.api_key=your_key \
  gitlab.token=your_token
```

**支持的命令行参数**：

| 参数 | 简写 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `--config` | `-c` | 路径 | 配置文件路径 | `--config /etc/aft/app.yaml` |
| `--debug` | `-d` | 布尔 | 启用调试模式 | `--debug` |
| `--log-level` | `-l` | 字符串 | 日志级别 | `--log-level DEBUG` |
| `--target` | `-t` | 字符串 | 测试目标环境 | `--target qemu` |
| `--timeout` | `-T` | 整数 | 执行超时时间（秒） | `--timeout 300` |
| `--retries` | `-r` | 整数 | 重试次数 | `--retries 3` |
| `--parallel` | `-p` | 整数 | 并行任务数 | `--parallel 2` |
| `--workspace` | `-w` | 路径 | 工作目录 | `--workspace /tmp/aft-workspace` |
| `--model` | `-m` | 字符串 | LLM模型名称 | `--model gpt-4-turbo-preview` |
| `--temperature` | `-t` | 浮点数 | 模型温度参数 | `--temperature 0.1` |
| `--max-tokens` | `-M` | 整数 | 最大token数 | `--max-tokens 2000` |

#### 2.2.5 运行时API调用覆盖（优先级：1）

**描述**：通过运行时API接口动态修改的配置，优先级最高

**REST API端点**：

```yaml
# 配置更新API
PUT /api/v1/config/{config_key}
Request Body:
{
  "value": "new_value",
  "scope": "runtime",  # runtime, session, persistent
  "ttl": 3600         # 有效期（秒）
}

# 批量配置更新
POST /api/v1/config/batch
Request Body:
{
  "configs": [
    {"key": "execution.timeout", "value": 400},
    {"key": "agents.code_agent.temperature", "value": 0.2}
  ],
  "scope": "runtime"
}

# 获取配置
GET /api/v1/config/{config_key}

# 配置重置
DELETE /api/v1/config/{config_key}
```

**WebSocket实时配置更新**：

```javascript
// 建立WebSocket连接
const ws = new WebSocket('ws://localhost:8080/config-ws');

// 订阅配置变更
ws.send(JSON.stringify({
  action: 'subscribe',
  keys: ['execution.timeout', 'agents.code_agent.model']
}));

// 接收配置更新通知
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('配置已更新:', update.key, '=', update.value);
};
```

---

## 3. 配置分类体系

### 3.1 系统配置（System Configuration）

#### 3.1.1 日志配置

**配置项**：
```yaml
logging:
  level: "INFO"              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "json"             # json, plain, colored
  output: "stdout"           # stdout, file, both
  file:
    path: "/var/log/aft/app.log"
    max_size: "100MB"
    retention: "30d"
    compression: "gzip"
  structured: true           # 是否使用结构化日志
  include_trace: true        # 是否包含调用栈
  sensitive_data_filter: true # 是否过滤敏感数据
```

**功能说明**：
- **日志级别控制**：根据重要性筛选日志内容
- **输出格式控制**：支持开发和生产环境的不同格式需求
- **文件轮转**：自动管理日志文件大小和保留期限
- **敏感数据保护**：自动过滤敏感配置信息

#### 3.1.2 存储配置

**配置项**：
```yaml
storage:
  # 工作空间配置
  workspace:
    base_path: "/tmp/aft-workspace"
    auto_cleanup: true
    max_age_days: 7
    temp_cleanup_interval: 3600  # 秒
    
  # 数据库配置
  database:
    postgres:
      url: "postgresql://user:password@localhost/aft"
      pool_size: 10
      max_overflow: 20
      pool_timeout: 30
      pool_recycle: 3600
      echo: false
      echo_pool: false
      
    qdrant:
      url: "http://localhost:6333"
      collection_name: "firmware_knowledge"
      embedding_model: "all-MiniLM-L6-v2"
      distance_metric: "Cosine"
      
  # 文件存储配置
  file_storage:
    provider: "local"         # local, s3, oss
    local:
      base_path: "/var/lib/aft"
    s3:
      bucket: "aft-storage"
      region: "us-west-2"
      access_key: "${AWS_ACCESS_KEY}"
      secret_key: "${AWS_SECRET_KEY}"
```

**功能说明**：
- **多存储后端支持**：本地文件系统、云存储服务
- **连接池管理**：数据库连接复用和优化
- **存储清理**：自动清理过期文件和工作空间

#### 3.1.3 安全配置

**配置项**：
```yaml
security:
  # 加密配置
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
    key_derivation: "PBKDF2"
    
  # 认证配置
  authentication:
    session_timeout: 3600
    max_login_attempts: 5
    lockout_duration: 900
    
  # 访问控制
  access_control:
    enabled: true
    default_role: "viewer"
    roles:
      admin:
        permissions: ["read", "write", "execute", "admin"]
      engineer:
        permissions: ["read", "write", "execute"]
      viewer:
        permissions: ["read"]
        
  # 审计日志
  audit:
    enabled: true
    log_level: "INFO"
    retention_days: 90
    include_sensitive: false
```

**功能说明**：
- **数据加密**：敏感配置信息的加密存储
- **访问控制**：基于角色的权限管理
- **审计追踪**：配置变更的完整审计日志

### 3.2 集成配置（Integration Configuration）

#### 3.2.1 Redmine集成

**配置项**：
```yaml
redmine:
  enabled: true
  url: "https://redmine.company.com"
  api_key: "${REDMINE_API_KEY}"
  project_id: "firmware-testing"
  timeout: 30
  retries: 3
  
  # 任务映射
  task_mapping:
    code_analysis: "Code Analysis"
    test_execution: "Test Execution"
    bug_reporting: "Bug Reporting"
    
  # 自动更新配置
  auto_update:
    enabled: true
    status_sync: true
    comment_on_result: true
    
  # Webhook配置
  webhook:
    enabled: false
    url: "https://aft.company.com/webhooks/redmine"
    secret: "${REDMINE_WEBHOOK_SECRET}"
```

**API使用示例**：
```python
# 代码中获取Redmine配置
redmine_config = config.get('redmine')
redmine_client = RedmineClient(
    url=redmine_config['url'],
    api_key=redmine_config['api_key']
)
```

#### 3.2.2 GitLab集成

**配置项**：
```yaml
gitlab:
  enabled: true
  url: "https://gitlab.company.com"
  private_token: "${GITLAB_TOKEN}"
  timeout: 30
  retries: 3
  
  # 项目配置
  projects:
    firmware_core:
      id: 123
      branch: "main"
      path: "firmware/core"
    firmware_modules:
      id: 124
      branch: "develop"
      path: "firmware/modules"
      
  # MR处理配置
  merge_requests:
    auto_create: true
    auto_assign: true
    auto_merge: false
    reviewers: ["senior_engineer_1", "senior_engineer_2"]
    
  # CI/CD配置
  cicd:
    pipeline_trigger: true
    build_timeout: 1800
    artifacts_retention: 7  # 天
```

#### 3.2.3 大模型API集成

**配置项**：
```yaml
model:
  # 提供商配置
  provider: "openai"          # openai, azure, local, anthropic
  
  # OpenAI配置
  openai:
    api_base: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
    organization: "${OPENAI_ORG_ID}"
    timeout: 60
    max_retries: 3
    
  # Azure配置
  azure:
    endpoint: "${AZURE_ENDPOINT}"
    api_key: "${AZURE_API_KEY}"
    api_version: "2023-12-01-preview"
    
  # 本地模型配置
  local:
    model_path: "/models/llama-2-7b"
    device: "cuda"             # cpu, cuda, mps
    max_memory: "8GB"
    
  # 模型参数
  default_model: "gpt-4-turbo-preview"
  default_params:
    temperature: 0.1
    max_tokens: 2000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    
  # 批处理配置
  batch_processing:
    enabled: true
    batch_size: 10
    max_concurrent: 5
    
  # 缓存配置
  caching:
    enabled: true
    ttl: 3600
    max_size: 1000
```

### 3.3 环境配置（Environment Configuration）

#### 3.3.1 QEMU环境配置

**配置项**：
```yaml
qemu:
  enabled: true
  binary_path: "${QEMU_PATH}"  # /usr/bin/qemu-system-aarch64
  
  # 系统镜像配置
  image:
    kernel: "/images/kernel.img"
    initrd: "/images/initrd.img"
    disk: "/images/rootfs.ext4"
    
  # 硬件配置
  hardware:
    cpu: "cortex-a57"
    memory: "2G"
    cores: 4
    smp: 4
    
  # 网络配置
  network:
    enabled: true
    bridge: "br0"
    mac_prefix: "52:54:00"
    
  # 串口配置
  serial:
    enabled: true
    stdio: false
    socket: "/tmp/qemu-serial.sock"
    
  # 监控配置
  monitor:
    enabled: true
    socket: "/tmp/qemu-monitor.sock"
    
  # 启动参数
  boot:
    timeout: 30
    kernel_cmdline: "console=ttyAMA0 root=/dev/vda"
    
  # 资源限制
  limits:
    max_memory: "4G"
    max_cpu: 8
    io_limit: "100MB/s"
```

**使用示例**：
```python
# 代码中使用QEMU配置
qemu_config = config.get('qemu')
qemu_env = QEMUEnvironment(
    binary_path=qemu_config['binary_path'],
    image_config=qemu_config['image'],
    hardware_config=qemu_config['hardware']
)
```

#### 3.3.2 目标板配置

**配置项**：
```yaml
board:
  # 板卡基本信息
  name: "Raspberry Pi 4B"
  architecture: "aarch64"
  os: "linux"
  
  # 网络配置
  network:
    ip: "${BOARD_IP}"        # 192.168.1.100
    port: 22
    username: "pi"
    password: "${BOARD_PASSWORD}"
    
  # 硬件信息
  hardware:
    cpu: "Cortex-A72"
    memory: "8GB"
    storage: "64GB"
    
  # 连接配置
  connection:
    type: "ssh"              # ssh, serial, network
    timeout: 30
    retries: 3
    
  # 测试配置
  testing:
    workspace: "/home/pi/aft-workspace"
    results_dir: "/home/pi/aft-results"
    logs_dir: "/home/pi/aft-logs"
    
  # 特殊配置
  special:
    power_control: false    # 是否支持电源控制
    reset_capability: true  # 是否支持复位
```

#### 3.3.3 BMC配置

**配置项**：
```yaml
bmc:
  # BMC基本信息
  name: "IPMI BMC"
  type: "ipmi"
  vendor: "supermicro"
  
  # 网络配置
  network:
    ip: "${BMC_IP}"          # 192.168.1.200
    port: 623
    username: "${BMC_USERNAME}"
    password: "${BMC_PASSWORD}"
    
  # 功能配置
  capabilities:
    power_control: true
    sensor_monitoring: true
    console_access: true
    firmware_update: false
    
  # 传感器配置
  sensors:
    temperature: true
    voltage: true
    fan_speed: true
    
  # 监控配置
  monitoring:
    interval: 30             # 秒
    enabled: true
    alert_thresholds:
      temperature: 80        # 摄氏度
      voltage_min: 11.0      # 伏特
      voltage_max: 13.0      # 伏特
```

### 3.4 Agent配置（Agent Configuration）

#### 3.4.1 CodeAgent配置

**配置项**：
```yaml
code_agent:
  # 模型配置
  model:
    provider: "${MODEL_PROVIDER}"
    name: "gpt-4-turbo-preview"
    temperature: 0.1
    max_tokens: 2000
    top_p: 1.0
    
  # 行为配置
  behavior:
    timeout: 120
    retries: 2
    confidence_threshold: 0.8
    
  # 代码分析配置
  analysis:
    languages: ["c", "cpp", "makefile"]
    include_headers: true
    analyze_dependencies: true
    static_analysis: true
    
  # 修改策略配置
  modification:
    auto_format: true
    preserve_comments: true
    create_backup: true
    backup_extension: ".aft.bak"
    
  # 验证配置
  validation:
    syntax_check: true
    compile_check: true
    security_scan: true
    
  # 知识库配置
  knowledge_base:
    enabled: true
    similarity_threshold: 0.7
    max_relevant_docs: 5
```

**功能说明**：
- **代码分析**：支持多种编程语言的静态分析
- **智能修改**：基于上下文和知识库的安全修改
- **验证机制**：多层验证确保修改的正确性

#### 3.4.2 TestAgent配置

**配置项**：
```yaml
test_agent:
  # 执行配置
  execution:
    timeout: 600
    retries: 3
    parallel_execution: false
    max_concurrent_tests: 2
    
  # 环境配置
  environment:
    default_target: "qemu"
    cleanup_after_test: true
    workspace_isolation: true
    
  # 测试用例配置
  test_cases:
    auto_discovery: true
    pattern: "test_*.py"
    exclude_pattern: "*_integration.py"
    
  # 日志配置
  logging:
    level: "INFO"
    capture_stdout: true
    capture_stderr: true
    log_file: "test_execution.log"
    
  # 结果配置
  results:
    format: "json"
    save_raw_logs: true
    save_artifacts: true
    artifact_retention_days: 7
```

#### 3.4.3 AnalysisAgent配置

**配置项**：
```yaml
analysis_agent:
  # 分析策略
  strategy:
    confidence_threshold: 0.8
    max_history_analysis: 10
    enable_trend_analysis: true
    
  # 分类配置
  classification:
    categories:
      - "compilation_error"
      - "runtime_error"
      - "performance_issue"
      - "security_vulnerability"
      - "code_quality"
      
  # 根因分析
  root_cause_analysis:
    enabled: true
    depth: 3
    include_correlation: true
    
  # 建议生成
  recommendations:
    generate_fixes: true
    generate_tests: true
    include_explanations: true
    
  # 知识库关联
  knowledge_integration:
    enabled: true
    similarity_search: true
    auto_tagging: true
```

#### 3.4.4 KBAgent配置

**配置项**：
```yaml
kb_agent:
  # 向量数据库配置
  vector_db:
    provider: "qdrant"
    url: "${VECTOR_DB_URL}"
    collection_name: "firmware_knowledge"
    embedding_model: "all-MiniLM-L6-v2"
    distance_metric: "Cosine"
    
  # 文档处理配置
  document_processing:
    chunk_size: 1000
    chunk_overlap: 200
    include_metadata: true
    
  # 检索配置
  retrieval:
    similarity_threshold: 0.7
    max_results: 5
    enable_reranking: true
    
  # 更新策略
  updates:
    auto_index: true
    update_frequency: "daily"
    cleanup_orphaned: true
    
  # 知识图谱配置
  knowledge_graph:
    enabled: true
    entity_extraction: true
    relationship_mapping: true
```

---

## 4. 配置加载流程

### 4.1 配置加载时序

```mermaid
sequenceDiagram
    participant App as 应用程序
    participant Loader as 配置加载器
    participant Validator as 配置验证器
    participant Cache as 配置缓存
    participant Env as 环境变量
    participant File as 配置文件
    participant CLI as 命令行
    participant API as 运行时API
    
    App->>Loader: 启动配置加载
    Loader->>Cache: 检查配置缓存
    
    alt 缓存命中
        Cache->>Loader: 返回缓存配置
    else 缓存未命中
        Loader->>Env: 加载环境变量
        Loader->>File: 加载配置文件
        Loader->>CLI: 解析命令行参数
        Loader->>API: 获取运行时配置覆盖
        
        Loader->>Loader: 合并配置层次
        
        Note over Loader: 1. 硬编码默认值<br/>2. 环境变量<br/>3. 配置文件<br/>4. 命令行参数<br/>5. 运行时覆盖
    end
    
    Loader->>Validator: 验证配置
    Validator->>Validator: 检查必填项
    Validator->>Validator: 验证数据类型
    Validator->>Validator: 检查依赖关系
    
    alt 验证通过
        Validator->>Cache: 缓存有效配置
        Cache->>Loader: 返回验证结果
        Loader->>App: 提供最终配置
    else 验证失败
        Validator->>App: 返回错误信息
    end
```

### 4.2 配置合并算法

**配置合并优先级**（从低到高）：

```python
def merge_configs(*configs):
    """
    配置合并算法
    按照优先级从低到高合并配置
    """
    result = {}
    
    for config in reversed(configs):
        if config is None:
            continue
            
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = merge_configs(result[key], value)
            else:
                # 高优先级覆盖低优先级
                result[key] = value
                
    return result

# 使用示例
final_config = merge_configs(
    DEFAULT_CONFIG,           # 优先级 5 (最低)
    ENV_CONFIG,               # 优先级 4
    FILE_CONFIG,              # 优先级 3
    CLI_CONFIG,               # 优先级 2
    RUNTIME_CONFIG            # 优先级 1 (最高)
)
```

### 4.3 配置验证流程

**验证检查清单**：

```python
class ConfigValidator:
    def __init__(self, config):
        self.config = config
        self.errors = []
        
    def validate(self):
        """执行所有验证检查"""
        self._validate_required_fields()
        self._validate_data_types()
        self._validate_value_ranges()
        self._validate_dependencies()
        self._validate_file_paths()
        self._validate_network_connectivity()
        
        return len(self.errors) == 0
        
    def _validate_required_fields(self):
        """检查必填字段"""
        required_fields = [
            'app.name',
            'app.version',
            'execution.default_env',
            'database.postgres.url',
            'integrations.redmine.enabled',
            'integrations.gitlab.enabled'
        ]
        
        for field in required_fields:
            if not self._get_nested_value(field):
                self.errors.append(f"Missing required field: {field}")
                
    def _validate_data_types(self):
        """验证数据类型"""
        type_checks = {
            'app.debug': bool,
            'execution.timeout': int,
            'execution.retries': int,
            'agents.code_agent.temperature': float,
            'agents.code_agent.max_tokens': int
        }
        
        for field, expected_type in type_checks.items():
            value = self._get_nested_value(field)
            if value is not None and not isinstance(value, expected_type):
                self.errors.append(
                    f"Invalid type for {field}: expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
```

### 4.4 环境变量插值

**插值语法**：

```yaml
# 支持的环境变量插值格式
database:
  url: "${DATABASE_URL}"
  url_with_default: "${DATABASE_URL:-postgresql://localhost/aft}"
  url_with_required: "${DATABASE_URL:?Database URL is required}"
  
secrets:
  api_key: "${API_KEY}"              # 必需变量
  optional_secret: "${OPTIONAL_KEY:-default_value}"  # 带默认值
  
paths:
  workspace: "${AFT_WORKSPACE:-/tmp/aft-workspace}"
  log_file: "${AFT_LOG_DIR}/app.log"
  
nested:
  redmine:
    url: "${REDMINE_URL}"
    api_key: "${REDMINE_API_KEY}"
    project_id: "${REDMINE_PROJECT_ID:-firmware-testing}"
```

**插值处理器**：

```python
import re
import os
from typing import Any, Dict

class EnvironmentInterpolator:
    """环境变量插值处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pattern = re.compile(r'\$\{([^}]+)\}')
        
    def interpolate(self) -> Dict[str, Any]:
        """执行环境变量插值"""
        return self._interpolate_value(self.config)
        
    def _interpolate_value(self, value: Any) -> Any:
        """递归插值处理"""
        if isinstance(value, str):
            return self._interpolate_string(value)
        elif isinstance(value, dict):
            return {k: self._interpolate_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate_value(item) for item in value]
        else:
            return value
            
    def _interpolate_string(self, text: str) -> str:
        """插值字符串中的环境变量"""
        def replace_var(match):
            var_expr = match.group(1)
            
            # 解析变量表达式 ${VAR} 或 ${VAR:-default} 或 ${VAR:?error}
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.getenv(var_name, default_value)
            elif ':?' in var_expr:
                var_name, error_msg = var_expr.split(':? ', 1)
                value = os.getenv(var_name)
                if value is None:
                    raise ValueError(f"Environment variable {var_name} is required: {error_msg}")
                return value
            else:
                # 必需变量
                value = os.getenv(var_expr)
                if value is None:
                    raise ValueError(f"Required environment variable {var_expr} is not set")
                return value
                
        return self.pattern.sub(replace_var, text)
```

### 4.5 配置热重载

**热重载机制**：

```python
import asyncio
import json
from pathlib import Path
from typing import Callable, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigHotReloadHandler(FileSystemEventHandler):
    """配置文件热重载处理器"""
    
    def __init__(self, config_path: str, callback: Callable[[Dict[str, Any]], None]):
        self.config_path = Path(config_path)
        self.callback = callback
        self.debounce_timer = None
        
    def on_modified(self, event):
        if event.src_path == str(self.config_path):
            # 防抖动处理
            if self.debounce_timer:
                self.debounce_timer.cancel()
                
            self.debounce_timer = asyncio.call_later(1.0, self._reload_config)
            
    def _reload_config(self):
        """重新加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                new_config = yaml.safe_load(f)
                
            # 验证新配置
            validator = ConfigValidator(new_config)
            if validator.validate():
                # 执行插值
                interpolator = EnvironmentInterpolator(new_config)
                final_config = interpolator.interpolate()
                
                # 通知配置更新
                self.callback(final_config)
                logger.info("Configuration reloaded successfully")
            else:
                logger.error(f"Configuration validation failed: {validator.errors}")
                
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.observers = []
        self.observer = Observer()
        
    async def start_hot_reload(self):
        """启动热重载监控"""
        handler = ConfigHotReloadHandler(self.config_path, self._on_config_changed)
        self.observer.schedule(handler, str(Path(self.config_path).parent))
        self.observer.start()
        
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """配置变更回调"""
        old_config = self.config
        self.config = new_config
        
        # 通知所有观察者
        for callback in self.observers:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")
```

**配置变更通知**：

```python
# 注册配置变更监听器
config_manager = ConfigManager('/etc/aft/config.yaml')

@config_manager.on_change
def on_config_changed(old_config, new_config):
    """配置变更处理"""
    if old_config.get('execution.timeout') != new_config.get('execution.timeout'):
        logger.info(f"Execution timeout changed: {old_config['execution.timeout']} -> {new_config['execution.timeout']}")
        
    if old_config.get('agents.code_agent.model') != new_config.get('agents.code_agent.model'):
        logger.info(f"Code agent model changed: {old_config['agents.code_agent.model']} -> {new_config['agents.code_agent.model']}")
        
    # 重新初始化相关组件
    if 'agents' in new_config:
        initialize_agents(new_config['agents'])
```

---

## 5. 示例配置文件

### 5.1 主配置文件示例

**config/app.yaml**：
```yaml
# =============================================================================
# AI驱动固件智能测试系统 - 主配置文件
# =============================================================================

# 应用基础配置
app:
  name: "AI-Firmware-Tester"
  version: "1.0.0"
  description: "AI驱动的固件智能测试系统"
  debug: false
  environment: "production"  # development, testing, production
  timezone: "Asia/Shanghai"
  locale: "zh_CN"
  
# 日志配置
logging:
  level: "INFO"
  format: "json"
  output: "file"
  file:
    path: "/var/log/aft/app.log"
    max_size: "100MB"
    retention: "30d"
    compression: "gzip"
  structured: true
  include_trace: true
  sensitive_data_filter: true
  
  # 子模块日志级别
  modules:
    code_agent: "DEBUG"
    test_agent: "INFO"
    analysis_agent: "INFO"
    kb_agent: "WARNING"
    
# 执行配置
execution:
  default_env: "qemu"
  timeout: 300
  retries: 3
  parallel_tasks: 2
  workspace: "/tmp/aft-workspace"
  auto_cleanup: true
  max_concurrent_jobs: 5
  
# 数据库配置
database:
  postgres:
    url: "${DATABASE_URL:-postgresql://user:password@localhost/aft}"
    pool_size: 10
    max_overflow: 20
    pool_timeout: 30
    pool_recycle: 3600
    echo: false
    ssl_mode: "prefer"
    
  qdrant:
    url: "${VECTOR_DB_URL:-http://localhost:6333}"
    collection_name: "firmware_knowledge"
    embedding_model: "all-MiniLM-L6-v2"
    distance_metric: "Cosine"
    grpc_port: 6334
    
# 缓存配置
cache:
  redis:
    url: "${REDIS_URL:-redis://localhost:6379/0}"
    default_timeout: 3600
    max_connections: 20
    socket_timeout: 5
    socket_connect_timeout: 5
    
# Agent配置
agents:
  code_agent:
    enabled: true
    model:
      provider: "${MODEL_PROVIDER:-openai}"
      name: "${MODEL_NAME:-gpt-4-turbo-preview}"
      temperature: 0.1
      max_tokens: 2000
      top_p: 1.0
    behavior:
      timeout: 120
      retries: 2
      confidence_threshold: 0.8
    analysis:
      languages: ["c", "cpp", "makefile"]
      include_headers: true
      analyze_dependencies: true
      static_analysis: true
    modification:
      auto_format: true
      preserve_comments: true
      create_backup: true
      backup_extension: ".aft.bak"
      
  test_agent:
    enabled: true
    execution:
      timeout: 600
      retries: 3
      parallel_execution: false
      max_concurrent_tests: 2
    environment:
      default_target: "qemu"
      cleanup_after_test: true
      workspace_isolation: true
    test_cases:
      auto_discovery: true
      pattern: "test_*.py"
      exclude_pattern: "*_integration.py"
      
  analysis_agent:
    enabled: true
    strategy:
      confidence_threshold: 0.8
      max_history_analysis: 10
      enable_trend_analysis: true
    classification:
      categories:
        - "compilation_error"
        - "runtime_error"
        - "performance_issue"
        - "security_vulnerability"
        - "code_quality"
        
  kb_agent:
    enabled: true
    vector_db:
      provider: "qdrant"
      url: "${VECTOR_DB_URL}"
      collection_name: "firmware_knowledge"
      embedding_model: "all-MiniLM-L6-v2"
    retrieval:
      similarity_threshold: 0.7
      max_results: 5
      enable_reranking: true
      
# 集成服务配置
integrations:
  redmine:
    enabled: true
    url: "${REDMINE_URL}"
    api_key: "${REDMINE_API_KEY}"
    project_id: "firmware-testing"
    timeout: 30
    retries: 3
    task_mapping:
      code_analysis: "Code Analysis"
      test_execution: "Test Execution"
      bug_reporting: "Bug Reporting"
      
  gitlab:
    enabled: true
    url: "${GITLAB_URL}"
    private_token: "${GITLAB_TOKEN}"
    timeout: 30
    retries: 3
    default_branch: "main"
    projects:
      firmware_core:
        id: 123
        branch: "main"
        path: "firmware/core"
      firmware_modules:
        id: 124
        branch: "develop"
        path: "firmware/modules"
        
  model:
    provider: "${MODEL_PROVIDER:-openai}"
    api_base: "${MODEL_API_BASE:-https://api.openai.com/v1}"
    api_key: "${MODEL_API_KEY}"
    timeout: 60
    max_retries: 3
    batch_processing:
      enabled: true
      batch_size: 10
      max_concurrent: 5
      
# 测试环境配置
environments:
  qemu:
    enabled: true
    binary_path: "${QEMU_PATH:-/usr/bin/qemu-system-aarch64}"
    image:
      kernel: "/images/kernel.img"
      initrd: "/images/initrd.img"
      disk: "/images/rootfs.ext4"
    hardware:
      cpu: "cortex-a57"
      memory: "2G"
      cores: 4
    network:
      enabled: true
      bridge: "br0"
      
  board:
    enabled: false
    name: "Raspberry Pi 4B"
    network:
      ip: "${BOARD_IP}"
      port: 22
      username: "${BOARD_USERNAME}"
      password: "${BOARD_PASSWORD}"
      
  bmc:
    enabled: false
    name: "IPMI BMC"
    network:
      ip: "${BMC_IP}"
      port: 623
      username: "${BMC_USERNAME}"
      password: "${BMC_PASSWORD}"
      
# 安全配置
security:
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
  authentication:
    session_timeout: 3600
    max_login_attempts: 5
  access_control:
    enabled: true
    default_role: "viewer"
    
# 监控配置
monitoring:
  metrics:
    enabled: true
    port: 9090
  health_check:
    enabled: true
    port: 8080
    path: "/health"
    
# 通知配置
notifications:
  email:
    enabled: false
    smtp_server: "${SMTP_SERVER}"
    smtp_port: 587
    username: "${SMTP_USERNAME}"
    password: "${SMTP_PASSWORD}"
    
  webhook:
    enabled: false
    url: "${WEBHOOK_URL}"
    secret: "${WEBHOOK_SECRET}"
```

### 5.2 环境特定配置

**config/env/development.yaml**：
```yaml
# 开发环境配置
app:
  debug: true
  environment: "development"
  
logging:
  level: "DEBUG"
  format: "plain"
  output: "stdout"
  
execution:
  timeout: 60    # 较短的调试超时
  retries: 1
  parallel_tasks: 1
  
database:
  postgres:
    echo: true           # 显示SQL语句
    pool_size: 5         # 较小的连接池
    
cache:
  redis:
    url: "redis://localhost:6379/1"  # 使用不同的数据库
    
integrations:
  redmine:
    url: "https://redmine-dev.company.com"
    project_id: "firmware-testing-dev"
    
  gitlab:
    url: "https://gitlab-dev.company.com"
    default_branch: "develop"
    
  model:
    timeout: 30          # 开发环境更短的超时
    max_retries: 1
    
environments:
  qemu:
    memory: "1G"          # 开发环境使用较少内存
    cores: 2
```

**config/env/testing.yaml**：
```yaml
# 测试环境配置
app:
  debug: false
  environment: "testing"
  
logging:
  level: "INFO"
  format: "json"
  output: "file"
  
execution:
  timeout: 120
  retries: 2
  parallel_tasks: 2
  
database:
  postgres:
    url: "postgresql://test_user:test_pass@test_db:5432/aft_test"
    pool_size: 3
    
cache:
  redis:
    url: "redis://localhost:6379/2"
    
integrations:
  redmine:
    url: "https://redmine-test.company.com"
    project_id: "firmware-testing-test"
    
  gitlab:
    url: "https://gitlab-test.company.com"
    default_branch: "test"
    
  model:
    provider: "local"     # 测试环境使用本地模型
    api_base: "http://localhost:8080/v1"
    
environments:
  qemu:
    memory: "2G"
    cores: 4
    timeout: 180
```

**config/env/production.yaml**：
```yaml
# 生产环境配置
app:
  debug: false
  environment: "production"
  
logging:
  level: "WARNING"
  format: "json"
  output: "file"
  file:
    retention: "90d"      # 生产环境保留更长时间
    compression: "gzip"
    
execution:
  timeout: 300
  retries: 3
  parallel_tasks: 4
  
database:
  postgres:
    url: "${PROD_DATABASE_URL}"
    pool_size: 20
    max_overflow: 40
    ssl_mode: "require"
    
cache:
  redis:
    url: "${PROD_REDIS_URL}"
    max_connections: 50
    
integrations:
  redmine:
    url: "${PROD_REDMINE_URL}"
    timeout: 60
    retries: 5
    
  gitlab:
    url: "${PROD_GITLAB_URL}"
    timeout: 60
    retries: 5
    
  model:
    timeout: 120          # 生产环境更长的超时
    max_retries: 3
    batch_processing:
      enabled: true
      batch_size: 20
      max_concurrent: 10
      
security:
  encryption:
    key_rotation_days: 30  # 生产环境更频繁的密钥轮换
  access_control:
    enabled: true
    
monitoring:
  metrics:
    enabled: true
  health_check:
    enabled: true
    
notifications:
  email:
    enabled: true
  webhook:
    enabled: true
```

### 5.3 Agent特定配置

**config/agents/code_agent.yaml**：
```yaml
# CodeAgent专用配置
code_agent:
  # 模型配置
  model:
    provider: "openai"
    name: "gpt-4-turbo-preview"
    temperature: 0.1
    max_tokens: 2000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    
  # 行为配置
  behavior:
    timeout: 120
    retries: 2
    confidence_threshold: 0.8
    max_iterations: 10
    
  # 代码分析配置
  analysis:
    languages: 
      - "c"
      - "cpp" 
      - "makefile"
      - "cmake"
    include_headers: true
    analyze_dependencies: true
    static_analysis: true
    security_scan: true
    
    # 编译器配置
    compilers:
      gcc:
        path: "/usr/bin/gcc"
        version: "9.4.0"
        flags: ["-Wall", "-Wextra", "-O2"]
      clang:
        path: "/usr/bin/clang"
        version: "10.0.0"
        flags: ["-Wall", "-Wextra", "-O2"]
        
  # 修改策略配置
  modification:
    auto_format: true
    preserve_comments: true
    create_backup: true
    backup_extension: ".aft.bak"
    atomic_changes: true      # 原子性变更
    change_verification: true # 变更验证
    
  # 验证配置
  validation:
    syntax_check: true
    compile_check: true
    static_analysis: true
    security_scan: true
    unit_tests: true
    
  # 知识库配置
  knowledge_base:
    enabled: true
    similarity_threshold: 0.7
    max_relevant_docs: 5
    include_code_examples: true
    include_best_practices: true
    
  # 缓存配置
  caching:
    analysis_results: true
    code_templates: true
    compilation_results: true
    ttl: 3600
    
  # 性能配置
  performance:
    max_memory_usage: "2GB"
    max_cpu_time: 300
    parallel_analysis: true
    max_parallel_files: 5
    
  # 安全配置
  security:
    sandbox_enabled: true
    file_access_restrictions: true
    network_access: false
    allowed_file_extensions: [".c", ".cpp", ".h", ".hpp", ".cc", ".make", ".cmake"]
```

### 5.4 集成服务配置

**config/integrations/redmine.yaml**：
```yaml
# Redmine集成配置
redmine:
  # 基础配置
  enabled: true
  url: "${REDMINE_URL}"
  api_key: "${REDMINE_API_KEY}"
  project_id: "firmware-testing"
  timeout: 30
  retries: 3
  
  # 认证配置
  authentication:
    method: "api_key"  # api_key, basic_auth, oauth2
    username: "${REDMINE_USERNAME}"
    password: "${REDMINE_PASSWORD}"
    
  # 任务映射配置
  task_mapping:
    code_analysis: 
      tracker_id: 1
      category_id: 2
      priority_id: 3
    test_execution:
      tracker_id: 1
      category_id: 4
      priority_id: 2
    bug_reporting:
      tracker_id: 2
      category_id: 5
      priority_id: 1
      
  # 自动更新配置
  auto_update:
    enabled: true
    status_sync: true
    comment_on_result: true
    upload_attachments: true
    
  # Webhook配置
  webhook:
    enabled: false
    url: "https://aft.company.com/webhooks/redmine"
    secret: "${REDMINE_WEBHOOK_SECRET}"
    
  # 自定义字段配置
  custom_fields:
    test_execution_time:
      id: 1
      name: "Execution Time"
    test_pass_rate:
      id: 2
      name: "Pass Rate"
    agent_version:
      id: 3
      name: "Agent Version"
      
  # 通知配置
  notifications:
    on_creation: true
    on_update: true
    watchers:
      - "test_lead@company.com"
      - "qa_manager@company.com"
      
  # 批量操作配置
  batch_operations:
    enabled: true
    max_batch_size: 10
    delay_between_batches: 1
```

### 5.5 常用环境变量列表

**开发环境变量**：

```bash
#!/bin/bash
# 开发环境环境变量配置

# 应用基础配置
export AFT_DEBUG=true
export AFT_LOG_LEVEL=DEBUG
export AFT_CONFIG_PATH="/home/dev/aft/config/dev.yaml"
export AFT_WORKSPACE="/tmp/aft-dev-workspace"
export AFT_LOG_DIR="/tmp/aft-dev-logs"

# 数据库配置
export DATABASE_URL="postgresql://dev_user:dev_pass@localhost:5432/aft_dev"
export VECTOR_DB_URL="http://localhost:6333"
export REDIS_URL="redis://localhost:6379/1"

# 集成服务配置
export REDMINE_URL="https://redmine-dev.company.com"
export REDMINE_API_KEY="dev_redmine_api_key"
export GITLAB_URL="https://gitlab-dev.company.com"
export GITLAB_TOKEN="dev_gitlab_token"

# 模型配置
export MODEL_PROVIDER="openai"
export MODEL_API_KEY="dev_model_api_key"
export MODEL_API_BASE="https://api.openai.com/v1"

# 测试环境配置
export QEMU_PATH="/usr/bin/qemu-system-aarch64"
export BOARD_IP="192.168.1.100"
export BMC_IP="192.168.1.200"
export BMC_USERNAME="admin"
export BMC_PASSWORD="dev_password"

# 安全配置
export ENCRYPTION_KEY="dev_encryption_key_32_chars"
export SESSION_SECRET="dev_session_secret"
```

**测试环境变量**：

```bash
#!/bin/bash
# 测试环境环境变量配置

# 应用基础配置
export AFT_DEBUG=false
export AFT_LOG_LEVEL=INFO
export AFT_CONFIG_PATH="/etc/aft/config/test.yaml"
export AFT_WORKSPACE="/var/lib/aft/test-workspace"
export AFT_LOG_DIR="/var/log/aft/test"

# 数据库配置
export DATABASE_URL="postgresql://test_user:test_pass@test_db:5432/aft_test"
export VECTOR_DB_URL="http://test-qdrant:6333"
export REDIS_URL="redis://test-redis:6379/2"

# 集成服务配置
export REDMINE_URL="https://redmine-test.company.com"
export REDMINE_API_KEY="test_redmine_api_key"
export GITLAB_URL="https://gitlab-test.company.com"
export GITLAB_TOKEN="test_gitlab_token"

# 模型配置
export MODEL_PROVIDER="local"
export MODEL_API_KEY="test_model_api_key"
export MODEL_API_BASE="http://test-model:8080/v1"

# 通知配置
export SMTP_SERVER="smtp-test.company.com"
export SMTP_USERNAME="test_smtp_user"
export SMTP_PASSWORD="test_smtp_password"
export WEBHOOK_URL="https://webhook-test.company.com/redmine"
export WEBHOOK_SECRET="test_webhook_secret"
```

**生产环境变量**：

```bash
#!/bin/bash
# 生产环境环境变量配置

# 应用基础配置
export AFT_DEBUG=false
export AFT_LOG_LEVEL=WARNING
export AFT_CONFIG_PATH="/etc/aft/config/prod.yaml"
export AFT_WORKSPACE="/var/lib/aft/prod-workspace"
export AFT_LOG_DIR="/var/log/aft/prod"

# 数据库配置
export PROD_DATABASE_URL="postgresql://prod_user:${PROD_DB_PASSWORD}@prod-db:5432/aft_prod"
export VECTOR_DB_URL="http://prod-qdrant:6333"
export PROD_REDIS_URL="redis://prod-redis:6379/3"

# 集成服务配置
export PROD_REDMINE_URL="https://redmine.company.com"
export PROD_REDMINE_API_KEY="${PROD_REDMINE_KEY}"
export GITLAB_URL="https://gitlab.company.com"
export PROD_GITLAB_TOKEN="${PROD_GITLAB_TOKEN}"

# 模型配置
export MODEL_PROVIDER="openai"
export MODEL_API_KEY="${PROD_MODEL_KEY}"
export MODEL_API_BASE="https://api.openai.com/v1"

# 安全配置
export ENCRYPTION_KEY="${PROD_ENCRYPTION_KEY}"
export SESSION_SECRET="${PROD_SESSION_SECRET}"

# 监控配置
export PROMETHEUS_URL="http://prometheus:9090"
export GRAFANA_URL="http://grafana:3000"

# 通知配置
export SMTP_SERVER="smtp.company.com"
export SMTP_USERNAME="${PROD_SMTP_USER}"
export SMTP_PASSWORD="${PROD_SMTP_PASS}"
export WEBHOOK_URL="https://webhook.company.com/redmine"
export WEBHOOK_SECRET="${PROD_WEBHOOK_SECRET}"
```

---

## 6. 配置最佳实践

### 6.1 命名规范

**配置文件命名**：
- 使用小写字母和下划线：`app_config.yaml`
- 按功能域分组：`redmine_integration.yaml`
- 环境特定文件：`app.development.yaml`

**配置项命名**：
- 使用点号分隔的层级结构：`agents.code_agent.timeout`
- 布尔值使用前缀：`enable_hot_reload`
- 时间值包含单位：`timeout_seconds`, `retention_days`
- 尺寸值包含单位：`max_memory_mb`, `max_file_size_mb`

### 6.2 安全最佳实践

**敏感信息处理**：
```yaml
# ✅ 正确做法：使用环境变量
database:
  password: "${DB_PASSWORD}"  # 敏感信息来自环境变量

# ❌ 错误做法：硬编码敏感信息
database:
  password: "hardcoded_password"  # 不安全！
```

**配置加密**：
```python
# 使用加密存储敏感配置
from cryptography.fernet import Fernet

class SecureConfigManager:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        
    def get_secret(self, key: str) -> str:
        encrypted_value = self.config.get(key)
        if encrypted_value:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        return None
        
    def set_secret(self, key: str, value: str):
        encrypted_value = self.cipher.encrypt(value.encode()).decode()
        self.config[key] = encrypted_value
```

### 6.3 性能优化

**配置缓存**：
```python
from functools import lru_cache
import threading

class CachedConfigManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._config_cache = {}
        
    @lru_cache(maxsize=128)
    def get_config(self, key: str, default=None):
        """带缓存的配置获取"""
        with self._lock:
            return self._config_cache.get(key, default)
            
    def invalidate_cache(self, key: str = None):
        """失效缓存"""
        with self._lock:
            if key:
                self._config_cache.pop(key, None)
            else:
                self._config_cache.clear()
```

### 6.4 错误处理

**配置错误处理**：
```python
class ConfigError(Exception):
    """配置相关异常"""
    pass

class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass

class ConfigNotFoundError(ConfigError):
    """配置文件未找到错误"""
    pass

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
        
    def load_config(self):
        try:
            if not os.path.exists(self.config_path):
                raise ConfigNotFoundError(f"Configuration file not found: {self.config_path}")
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            validator = ConfigValidator(config)
            if not validator.validate():
                raise ConfigValidationError(f"Configuration validation failed: {validator.errors}")
                
            self._config = config
            return config
            
        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            else:
                raise ConfigError(f"Failed to load configuration: {e}")
```

### 6.5 测试配置

**配置测试**：
```python
import pytest
import tempfile
import os
from unittest.mock import patch

class TestConfigManager:
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        config = {
            'app': {'name': 'test', 'debug': True},
            'execution': {'timeout': 30}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            yield f.name
            
        os.unlink(f.name)
        
    def test_config_loading(self, temp_config_file):
        """测试配置加载"""
        manager = ConfigManager(temp_config_file)
        config = manager.load_config()
        
        assert config['app']['name'] == 'test'
        assert config['execution']['timeout'] == 30
        
    def test_environment_interpolation(self):
        """测试环境变量插值"""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = {
                'test_field': '${TEST_VAR}'
            }
            
            interpolator = EnvironmentInterpolator(config)
            result = interpolator.interpolate()
            
            assert result['test_field'] == 'test_value'
            
    def test_config_validation(self):
        """测试配置验证"""
        invalid_config = {
            'execution': {
                'timeout': 'invalid_type'  # 应该是整数
            }
        }
        
        validator = ConfigValidator(invalid_config)
        assert not validator.validate()
        assert len(validator.errors) > 0
```

---

## 7. 配置迁移指南

### 7.1 版本迁移

**配置版本检查**：
```python
class ConfigMigrationManager:
    def __init__(self, current_config: dict):
        self.current_config = current_config
        self.migrations = {
            '1.0': self._migrate_from_1_0,
            '1.1': self._migrate_from_1_1,
            '2.0': self._migrate_from_2_0
        }
        
    def migrate_to_current(self):
        """迁移到当前版本"""
        version = self.current_config.get('version', '1.0')
        
        # 执行版本升级路径
        migration_path = self._get_migration_path(version, CURRENT_VERSION)
        
        for target_version in migration_path:
            if target_version in self.migrations:
                self.current_config = self.migrations[target_version](self.current_config)
                
        return self.current_config
        
    def _migrate_from_1_0(self, config):
        """从1.0版本迁移"""
        # 添加新字段
        config['version'] = '1.1'
        config['security'] = {
            'encryption': {'algorithm': 'AES-256-GCM'},
            'authentication': {'session_timeout': 3600}
        }
        
        # 重命名字段
        if 'timeout' in config.get('execution', {}):
            config['execution']['timeout_seconds'] = config['execution'].pop('timeout')
            
        return config
        
    def _migrate_from_1_1(self, config):
        """从1.1版本迁移"""
        config['version'] = '2.0'
        
        # 重构Agent配置结构
        if 'agents' in config:
            old_agents = config.pop('agents')
            config['agents'] = {
                'code_agent': old_agents.get('code_agent', {}),
                'test_agent': old_agents.get('test_agent', {}),
                'analysis_agent': old_agents.get('analysis_agent', {}),
                'kb_agent': old_agents.get('kb_agent', {})
            }
            
        return config
```

### 7.2 配置验证清单

**部署前检查**：
```bash
#!/bin/bash
# 配置验证脚本

echo "🔍 验证系统配置..."

# 检查配置文件存在性
check_config_exists() {
    if [ ! -f "$1" ]; then
        echo "❌ 配置文件不存在: $1"
        return 1
    else
        echo "✅ 配置文件存在: $1"
        return 0
    fi
}

# 检查环境变量
check_env_vars() {
    required_vars=(
        "AFT_CONFIG_PATH"
        "DATABASE_URL"
        "REDMINE_API_KEY"
        "GITLAB_TOKEN"
        "MODEL_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ 必需环境变量未设置: $var"
            return 1
        else
            echo "✅ 环境变量已设置: $var"
        fi
    done
}

# 检查服务连接
check_service_connectivity() {
    # 检查数据库连接
    if command -v psql >/dev/null 2>&1; then
        psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ 数据库连接正常"
        else
            echo "❌ 数据库连接失败"
        fi
    fi
    
    # 检查Redis连接
    if command -v redis-cli >/dev/null 2>&1; then
        redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ Redis连接正常"
        else
            echo "❌ Redis连接失败"
        fi
    fi
}

# 执行检查
echo "1. 检查配置文件..."
check_config_exists "$AFT_CONFIG_PATH"

echo "2. 检查环境变量..."
check_env_vars

echo "3. 检查服务连接..."
check_service_connectivity

echo "🎉 配置验证完成！"
```

---

## 8. 故障排除

### 8.1 常见问题

**Q1: 配置不生效？**
```bash
# 检查配置加载顺序
export AFT_DEBUG=true
export AFT_CONFIG_PATH=/path/to/config.yaml

# 验证配置解析
python -c "
from config import ConfigManager
manager = ConfigManager('$AFT_CONFIG_PATH')
config = manager.load_config()
print('Debug mode:', config.get('app', {}).get('debug'))
"
```

**Q2: 环境变量未正确插值？**
```bash
# 检查环境变量设置
env | grep AFT_

# 手动测试插值
python -c "
from config import EnvironmentInterpolator
config = {'test': '\${AFT_DEBUG:-false}'}
interpolator = EnvironmentInterpolator(config)
result = interpolator.interpolate()
print('Interpolated:', result)
"
```

**Q3: 配置文件语法错误？**
```bash
# YAML语法验证
python -c "
import yaml
try:
    with open('config/app.yaml') as f:
        yaml.safe_load(f)
    print('✅ YAML语法正确')
except yaml.YAMLError as e:
    print('❌ YAML语法错误:', e)
"
```

### 8.2 调试模式

**启用详细日志**：
```yaml
# config/debug.yaml
logging:
  level: "DEBUG"
  format: "detailed"
  include_config_loading: true
  include_environment_vars: true
  include_file_access: true
  
debug:
  show_config_sources: true
  validate_on_every_access: true
  trace_config_merging: true
```

**配置调试命令**：
```bash
# 查看当前生效的配置
aft config show

# 查看配置来源
aft config sources

# 验证配置
aft config validate

# 测试环境变量插值
aft config test-interpolation
```

---

## 9. 总结

### 9.1 配置管理要点

1. **分层明确**：硬编码默认值 → 环境变量 → 配置文件 → 命令行参数 → 运行时API
2. **分类清晰**：系统配置、集成配置、环境配置、Agent配置
3. **安全可靠**：敏感信息加密存储、访问控制、审计日志
4. **易于维护**：配置验证、版本迁移、故障排除
5. **高性能**：配置缓存、热重载、懒加载

### 9.2 最佳实践总结

- ✅ 使用环境变量管理敏感信息
- ✅ 建立清晰的配置分层和优先级
- ✅ 实施严格的配置验证机制
- ✅ 提供完整的配置迁移路径
- ✅ 保持配置文档的及时更新

### 9.3 后续扩展

本配置管理体系为AI驱动固件智能测试系统提供了坚实的配置管理基础，后续可根据实际需求进行以下扩展：

- 配置模板和动态配置生成
- 多租户环境下的配置隔离
- 基于策略的配置治理
- 配置变更的自动测试和验证
- 配置版本控制和回滚机制

---

*本文档将随着系统的发展和需求的变化持续更新维护。*