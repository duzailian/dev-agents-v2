# AI驱动固件智能测试系统 — API规范 (API_SPEC)

> 文档版本：v2.0
>
> 目标：定义系统REST API、Agent工具接口和Webhook的完整规范
>
> 规范：OpenAPI 3.0

---

## 1. API概述

### 1.1 基础信息

```yaml
openapi: 3.0.3
info:
  title: AI-Driven Firmware Intelligent Testing System API
  description: |
    AI驱动固件智能测试系统的REST API接口规范。
    提供任务管理、测试执行、知识库查询等功能。
  version: 2.0.0
  contact:
    name: API Support
    email: support@aft.company.com
  license:
    name: Proprietary

servers:
  - url: http://localhost:8080/api/v1
    description: 开发环境
  - url: https://aft-test.company.com/api/v1
    description: 测试环境
  - url: https://aft.company.com/api/v1
    description: 生产环境
```

### 1.2 认证方式

系统支持两种认证方式：

#### 1.2.1 API Key认证

```yaml
securitySchemes:
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
    description: |
      通过HTTP头传递API密钥进行认证。
      获取方式：联系管理员申请。
      示例：X-API-Key: aft_sk_1234567890abcdef
```

#### 1.2.2 JWT Bearer Token认证

```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: |
      通过JWT令牌进行认证。
      获取方式：调用 /auth/login 接口。
      令牌有效期：1小时
      刷新方式：调用 /auth/refresh 接口
```

### 1.3 通用响应格式

#### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-01-30T10:00:00Z"
  }
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERR_VALIDATION_FAILED",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "test_plan.timeout",
        "message": "超时时间必须大于0"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-01-30T10:00:00Z"
  }
}
```

### 1.4 错误码体系

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `ERR_UNAUTHORIZED` | 401 | 未认证或认证失败 |
| `ERR_FORBIDDEN` | 403 | 无权限访问资源 |
| `ERR_NOT_FOUND` | 404 | 资源不存在 |
| `ERR_VALIDATION_FAILED` | 400 | 请求参数验证失败 |
| `ERR_CONFLICT` | 409 | 资源冲突（如任务已存在）|
| `ERR_RATE_LIMITED` | 429 | 请求频率超限 |
| `ERR_INTERNAL` | 500 | 服务器内部错误 |
| `ERR_SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 |
| `ERR_JOB_NOT_FOUND` | 404 | 任务不存在 |
| `ERR_JOB_ALREADY_RUNNING` | 409 | 任务已在运行 |
| `ERR_JOB_FAILED` | 500 | 任务执行失败 |
| `ERR_ENVIRONMENT_ERROR` | 500 | 测试环境错误 |
| `ERR_KNOWLEDGE_NOT_FOUND` | 404 | 知识库记录不存在 |

---

## 2. 认证接口

### 2.1 用户登录

```yaml
/auth/login:
  post:
    summary: 用户登录
    description: 使用用户名和密码登录，获取JWT令牌
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - username
              - password
            properties:
              username:
                type: string
                description: 用户名
                example: "admin"
              password:
                type: string
                format: password
                description: 密码
                example: "********"
    responses:
      '200':
        description: 登录成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                data:
                  type: object
                  properties:
                    access_token:
                      type: string
                      description: JWT访问令牌
                      example: "eyJhbGciOiJIUzI1NiIs..."
                    refresh_token:
                      type: string
                      description: 刷新令牌
                      example: "eyJhbGciOiJIUzI1NiIs..."
                    token_type:
                      type: string
                      example: "Bearer"
                    expires_in:
                      type: integer
                      description: 过期时间（秒）
                      example: 3600
      '401':
        description: 认证失败
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
```

### 2.2 刷新令牌

```yaml
/auth/refresh:
  post:
    summary: 刷新访问令牌
    description: 使用刷新令牌获取新的访问令牌
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - refresh_token
            properties:
              refresh_token:
                type: string
                description: 刷新令牌
    responses:
      '200':
        description: 刷新成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    access_token:
                      type: string
                    expires_in:
                      type: integer
      '401':
        description: 刷新令牌无效或已过期
```

---

## 3. 任务管理接口

### 3.1 创建任务

```yaml
/jobs:
  post:
    summary: 创建测试任务
    description: |
      创建新的自动化测试/修复任务。
      任务将按照配置执行代码分析、修改、测试和结果分析的完整流程。
    tags:
      - Jobs
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/JobCreateRequest'
          examples:
            basic:
              summary: 基础任务
              value:
                name: "Fix memory leak in driver"
                repo_url: "https://gitlab.company.com/firmware/core.git"
                branch: "main"
                target_files:
                  - "src/drivers/memory.c"
                test_environment: "qemu"
            advanced:
              summary: 高级任务配置
              value:
                name: "Performance optimization"
                repo_url: "https://gitlab.company.com/firmware/core.git"
                branch: "feature/perf"
                target_files:
                  - "src/core/*.c"
                test_environment: "board"
                test_plan:
                  test_suite: "performance"
                  timeout: 600
                  retries: 2
                options:
                  max_iterations: 5
                  auto_commit: false
                  notify_on_complete: true
    responses:
      '201':
        description: 任务创建成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobResponse'
      '400':
        description: 请求参数无效
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
      '409':
        description: 任务已存在
```

### 3.2 获取任务列表

```yaml
/jobs:
  get:
    summary: 获取任务列表
    description: 分页获取任务列表，支持过滤和排序
    tags:
      - Jobs
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: status
        in: query
        description: 按状态过滤
        schema:
          type: string
          enum: [pending, running, completed, failed, cancelled]
      - name: environment
        in: query
        description: 按测试环境过滤
        schema:
          type: string
          enum: [qemu, board, bmc]
      - name: page
        in: query
        description: 页码（从1开始）
        schema:
          type: integer
          default: 1
          minimum: 1
      - name: page_size
        in: query
        description: 每页数量
        schema:
          type: integer
          default: 20
          minimum: 1
          maximum: 100
      - name: sort_by
        in: query
        description: 排序字段
        schema:
          type: string
          enum: [created_at, updated_at, name]
          default: created_at
      - name: sort_order
        in: query
        description: 排序方向
        schema:
          type: string
          enum: [asc, desc]
          default: desc
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    items:
                      type: array
                      items:
                        $ref: '#/components/schemas/JobSummary'
                    pagination:
                      $ref: '#/components/schemas/Pagination'
```

### 3.3 获取任务详情

```yaml
/jobs/{job_id}:
  get:
    summary: 获取任务详情
    description: 获取指定任务的详细信息，包括执行状态和进度
    tags:
      - Jobs
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: job_id
        in: path
        required: true
        description: 任务ID
        schema:
          type: string
          format: uuid
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobDetailResponse'
      '404':
        description: 任务不存在
```

### 3.4 取消任务

```yaml
/jobs/{job_id}/cancel:
  post:
    summary: 取消任务
    description: 取消正在执行的任务
    tags:
      - Jobs
    security:
      - BearerAuth: []
    parameters:
      - name: job_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              reason:
                type: string
                description: 取消原因
    responses:
      '200':
        description: 取消成功
      '400':
        description: 任务无法取消（已完成或已取消）
      '404':
        description: 任务不存在
```

### 3.5 获取任务产物

```yaml
/jobs/{job_id}/artifacts:
  get:
    summary: 获取任务产物列表
    description: 获取任务执行过程中产生的所有产物（日志、报告、补丁等）
    tags:
      - Jobs
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: job_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: type
        in: query
        description: 按产物类型过滤
        schema:
          type: string
          enum: [log, report, patch, dump, all]
          default: all
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/Artifact'
```

### 3.6 下载任务报告

```yaml
/jobs/{job_id}/report:
  get:
    summary: 下载任务报告
    description: 下载任务的最终报告（Markdown或JSON格式）
    tags:
      - Jobs
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: job_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: format
        in: query
        description: 报告格式
        schema:
          type: string
          enum: [markdown, json, html]
          default: markdown
    responses:
      '200':
        description: 成功
        content:
          text/markdown:
            schema:
              type: string
          application/json:
            schema:
              $ref: '#/components/schemas/JobReport'
          text/html:
            schema:
              type: string
      '404':
        description: 任务或报告不存在
```

---

## 4. 问题管理接口

### 4.1 获取Redmine问题列表

```yaml
/issues:
  get:
    summary: 获取待处理问题
    description: 从Redmine获取待处理的问题列表
    tags:
      - Issues
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: project_id
        in: query
        description: 项目ID
        schema:
          type: string
      - name: status
        in: query
        description: 问题状态
        schema:
          type: string
          enum: [open, in_progress, resolved, closed]
      - name: priority
        in: query
        description: 优先级
        schema:
          type: string
          enum: [low, normal, high, urgent, immediate]
      - name: assigned_to
        in: query
        description: 指派人
        schema:
          type: string
      - name: limit
        in: query
        description: 返回数量限制
        schema:
          type: integer
          default: 25
          maximum: 100
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    issues:
                      type: array
                      items:
                        $ref: '#/components/schemas/Issue'
                    total_count:
                      type: integer
```

### 4.2 从问题创建任务

```yaml
/issues/{issue_id}/create-job:
  post:
    summary: 从问题创建任务
    description: 根据Redmine问题自动创建测试/修复任务
    tags:
      - Issues
    security:
      - BearerAuth: []
    parameters:
      - name: issue_id
        in: path
        required: true
        description: Redmine问题ID
        schema:
          type: integer
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              test_environment:
                type: string
                enum: [qemu, board, bmc]
                default: qemu
              options:
                type: object
                properties:
                  auto_start:
                    type: boolean
                    default: true
                  max_iterations:
                    type: integer
                    default: 5
    responses:
      '201':
        description: 任务创建成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JobResponse'
      '404':
        description: 问题不存在
```

---

## 5. 知识库接口

### 5.1 知识库搜索

```yaml
/knowledge/search:
  post:
    summary: 知识库语义搜索
    description: |
      基于语义相似度搜索知识库中的相关记录。
      支持按产品线过滤和TopK检索。
    tags:
      - Knowledge
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - query
            properties:
              query:
                type: string
                description: 搜索查询文本
                minLength: 3
                maxLength: 1000
                example: "memory leak in I2C driver initialization"
              product_line:
                type: string
                description: 产品线过滤
                example: "BMC-X100"
              tags:
                type: array
                items:
                  type: string
                description: 标签过滤
                example: ["memory", "driver"]
              limit:
                type: integer
                description: 返回结果数量
                default: 5
                minimum: 1
                maximum: 20
              threshold:
                type: number
                description: 相似度阈值
                default: 0.7
                minimum: 0
                maximum: 1
              include_content:
                type: boolean
                description: 是否返回完整内容
                default: false
    responses:
      '200':
        description: 搜索成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    results:
                      type: array
                      items:
                        $ref: '#/components/schemas/KnowledgeUnit'
                    total_found:
                      type: integer
                    search_time_ms:
                      type: integer
            example:
              success: true
              data:
                results:
                  - id: "ku_abc123"
                    title: "I2C Driver Memory Leak Fix"
                    summary: "Fixed memory leak caused by missing free() in error path"
                    similarity: 0.92
                    product_line: "BMC-X100"
                    tags: ["memory", "driver", "I2C"]
                    created_at: "2026-01-15T10:30:00Z"
                total_found: 3
                search_time_ms: 45
```

### 5.2 添加知识

```yaml
/knowledge:
  post:
    summary: 添加知识记录
    description: 向知识库添加新的知识记录
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/KnowledgeCreateRequest'
    responses:
      '201':
        description: 创建成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  $ref: '#/components/schemas/KnowledgeUnit'
      '400':
        description: 请求参数无效
```

### 5.3 获取知识详情

```yaml
/knowledge/{knowledge_id}:
  get:
    summary: 获取知识详情
    description: 获取指定知识记录的完整内容
    tags:
      - Knowledge
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: knowledge_id
        in: path
        required: true
        schema:
          type: string
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  $ref: '#/components/schemas/KnowledgeUnitDetail'
      '404':
        description: 知识记录不存在
```

---

## 6. 测试环境接口

### 6.1 获取环境状态

```yaml
/environments:
  get:
    summary: 获取测试环境列表
    description: 获取所有可用测试环境的状态
    tags:
      - Environments
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/Environment'
```

### 6.2 获取特定环境详情

```yaml
/environments/{env_id}:
  get:
    summary: 获取环境详情
    description: 获取指定测试环境的详细状态
    tags:
      - Environments
    security:
      - BearerAuth: []
      - ApiKeyAuth: []
    parameters:
      - name: env_id
        in: path
        required: true
        schema:
          type: string
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  $ref: '#/components/schemas/EnvironmentDetail'
```

---

## 7. Webhook接口

### 7.1 GitLab Webhook

```yaml
/webhooks/gitlab:
  post:
    summary: GitLab事件回调
    description: |
      接收GitLab的Webhook事件通知。
      支持的事件类型：
      - Push events
      - Merge request events
      - Pipeline events
    tags:
      - Webhooks
    parameters:
      - name: X-Gitlab-Token
        in: header
        required: true
        description: GitLab Webhook密钥
        schema:
          type: string
      - name: X-Gitlab-Event
        in: header
        required: true
        description: 事件类型
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            oneOf:
              - $ref: '#/components/schemas/GitLabPushEvent'
              - $ref: '#/components/schemas/GitLabMergeRequestEvent'
              - $ref: '#/components/schemas/GitLabPipelineEvent'
    responses:
      '200':
        description: 事件处理成功
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
      '401':
        description: Webhook密钥验证失败
      '400':
        description: 不支持的事件类型或请求格式错误
```

### 7.2 Redmine Webhook

```yaml
/webhooks/redmine:
  post:
    summary: Redmine事件回调
    description: |
      接收Redmine的Webhook事件通知。
      支持的事件类型：
      - Issue created
      - Issue updated
      - Issue status changed
    tags:
      - Webhooks
    parameters:
      - name: X-Redmine-Token
        in: header
        required: true
        description: Redmine Webhook密钥
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/RedmineWebhookPayload'
    responses:
      '200':
        description: 事件处理成功
      '401':
        description: Webhook密钥验证失败
```

---

## 8. Agent工具接口

以下接口供Agent内部调用，不直接对外暴露。

### 8.1 代码分析

```yaml
# 内部接口：供CodeAgent调用
/internal/tools/analyze_code:
  post:
    summary: 代码分析工具
    description: 分析指定文件的代码结构和问题
    tags:
      - Internal Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - file_paths
            properties:
              file_paths:
                type: array
                items:
                  type: string
                description: 要分析的文件路径列表
              focus_function:
                type: string
                description: 聚焦分析的函数名
              analysis_type:
                type: string
                enum: [structure, dependency, metrics, static, full]
                default: full
    responses:
      '200':
        description: 分析完成
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CodeAnalysisResult'
```

### 8.2 生成补丁

```yaml
/internal/tools/generate_patch:
  post:
    summary: 补丁生成工具
    description: 根据修改建议生成Git补丁
    tags:
      - Internal Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - file_path
              - original_code
              - modified_code
            properties:
              file_path:
                type: string
              original_code:
                type: string
              modified_code:
                type: string
              description:
                type: string
    responses:
      '200':
        description: 补丁生成成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Patch'
```

### 8.3 执行测试

```yaml
/internal/tools/execute_test:
  post:
    summary: 测试执行工具
    description: 在指定环境中执行测试
    tags:
      - Internal Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - test_suite
              - environment
            properties:
              test_suite:
                type: string
                description: 测试套件名称
              environment:
                type: string
                enum: [qemu, board, bmc]
              timeout:
                type: integer
                default: 300
              retries:
                type: integer
                default: 1
    responses:
      '200':
        description: 测试执行完成
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TestResult'
```

---

## 9. 健康检查接口

### 9.1 健康检查

```yaml
/health:
  get:
    summary: 健康检查
    description: 检查服务健康状态
    tags:
      - Health
    responses:
      '200':
        description: 服务健康
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [healthy, degraded, unhealthy]
                version:
                  type: string
                uptime:
                  type: integer
                  description: 运行时间（秒）
                components:
                  type: object
                  properties:
                    database:
                      type: string
                      enum: [up, down]
                    vector_db:
                      type: string
                      enum: [up, down]
                    redis:
                      type: string
                      enum: [up, down]
```

### 9.2 就绪检查

```yaml
/ready:
  get:
    summary: 就绪检查
    description: 检查服务是否准备好接收请求
    tags:
      - Health
    responses:
      '200':
        description: 服务就绪
      '503':
        description: 服务未就绪
```

---

## 10. 数据模型定义

### 10.1 请求模型

```yaml
components:
  schemas:
    JobCreateRequest:
      type: object
      required:
        - name
        - repo_url
        - target_files
      properties:
        name:
          type: string
          description: 任务名称
          minLength: 1
          maxLength: 200
        description:
          type: string
          description: 任务描述
          maxLength: 2000
        repo_url:
          type: string
          format: uri
          description: Git仓库URL
        branch:
          type: string
          description: 分支名称
          default: main
        target_files:
          type: array
          items:
            type: string
          description: 目标文件列表（支持glob模式）
          minItems: 1
        test_environment:
          type: string
          enum: [qemu, board, bmc]
          default: qemu
        test_plan:
          type: object
          properties:
            test_suite:
              type: string
            timeout:
              type: integer
              minimum: 1
              maximum: 3600
              default: 300
            retries:
              type: integer
              minimum: 0
              maximum: 5
              default: 1
        options:
          type: object
          properties:
            max_iterations:
              type: integer
              minimum: 1
              maximum: 10
              default: 5
            auto_commit:
              type: boolean
              default: false
            notify_on_complete:
              type: boolean
              default: true
            mode:
              type: string
              enum: [interactive, ci, auto]
              default: interactive

    KnowledgeCreateRequest:
      type: object
      required:
        - title
        - content
        - type
      properties:
        title:
          type: string
          minLength: 1
          maxLength: 200
        content:
          type: string
          minLength: 10
        summary:
          type: string
          maxLength: 500
        type:
          type: string
          enum: [bug_fix, feature, optimization, documentation]
        product_line:
          type: string
        tags:
          type: array
          items:
            type: string
        related_files:
          type: array
          items:
            type: string
        metadata:
          type: object
          additionalProperties: true
```

### 10.2 响应模型

```yaml
    JobResponse:
      type: object
      properties:
        success:
          type: boolean
        data:
          $ref: '#/components/schemas/Job'

    JobDetailResponse:
      type: object
      properties:
        success:
          type: boolean
        data:
          $ref: '#/components/schemas/JobDetail'

    Job:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        status:
          type: string
          enum: [pending, running, completed, failed, cancelled]
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    JobDetail:
      allOf:
        - $ref: '#/components/schemas/Job'
        - type: object
          properties:
            description:
              type: string
            repo_url:
              type: string
            branch:
              type: string
            target_files:
              type: array
              items:
                type: string
            test_environment:
              type: string
            current_phase:
              type: string
              enum: [analyzing, modifying, testing, analyzing_results]
            iteration:
              type: integer
            max_iterations:
              type: integer
            progress:
              type: object
              properties:
                current_step:
                  type: string
                total_steps:
                  type: integer
                completed_steps:
                  type: integer
                percentage:
                  type: number
            results:
              type: object
              properties:
                tests_passed:
                  type: integer
                tests_failed:
                  type: integer
                pass_rate:
                  type: number
            started_at:
              type: string
              format: date-time
            completed_at:
              type: string
              format: date-time

    JobSummary:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        status:
          type: string
        test_environment:
          type: string
        iteration:
          type: integer
        pass_rate:
          type: number
        created_at:
          type: string
          format: date-time

    JobReport:
      type: object
      properties:
        job_id:
          type: string
        title:
          type: string
        summary:
          type: string
        iterations:
          type: array
          items:
            type: object
            properties:
              iteration:
                type: integer
              changes:
                type: string
              test_results:
                type: object
              decision:
                type: string
        final_status:
          type: string
        recommendations:
          type: array
          items:
            type: string
        artifacts:
          type: array
          items:
            $ref: '#/components/schemas/Artifact'

    Artifact:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        type:
          type: string
          enum: [log, report, patch, dump, screenshot]
        path:
          type: string
        size:
          type: integer
        download_url:
          type: string
          format: uri
        created_at:
          type: string
          format: date-time

    Issue:
      type: object
      properties:
        id:
          type: integer
        subject:
          type: string
        description:
          type: string
        status:
          type: string
        priority:
          type: string
        assigned_to:
          type: string
        project:
          type: string
        created_on:
          type: string
          format: date-time
        updated_on:
          type: string
          format: date-time

    KnowledgeUnit:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        summary:
          type: string
        type:
          type: string
        product_line:
          type: string
        tags:
          type: array
          items:
            type: string
        similarity:
          type: number
          description: 搜索时返回的相似度分数
        created_at:
          type: string
          format: date-time

    KnowledgeUnitDetail:
      allOf:
        - $ref: '#/components/schemas/KnowledgeUnit'
        - type: object
          properties:
            content:
              type: string
            related_files:
              type: array
              items:
                type: string
            related_jobs:
              type: array
              items:
                type: string
            metadata:
              type: object
            created_by:
              type: string
            updated_at:
              type: string
              format: date-time

    Environment:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        type:
          type: string
          enum: [qemu, board, bmc]
        status:
          type: string
          enum: [idle, busy, offline, error]
        current_job:
          type: string
          nullable: true

    EnvironmentDetail:
      allOf:
        - $ref: '#/components/schemas/Environment'
        - type: object
          properties:
            config:
              type: object
            metrics:
              type: object
              properties:
                cpu_usage:
                  type: number
                memory_usage:
                  type: number
                uptime:
                  type: integer
            last_used:
              type: string
              format: date-time

    CodeAnalysisResult:
      type: object
      properties:
        files_analyzed:
          type: integer
        issues:
          type: array
          items:
            type: object
            properties:
              file:
                type: string
              line:
                type: integer
              severity:
                type: string
              message:
                type: string
        dependencies:
          type: object
        metrics:
          type: object

    Patch:
      type: object
      properties:
        id:
          type: string
        file_path:
          type: string
        unified_diff:
          type: string
        description:
          type: string
        created_at:
          type: string
          format: date-time

    TestResult:
      type: object
      properties:
        test_id:
          type: string
        status:
          type: string
          enum: [passed, failed, skipped, error]
        duration:
          type: number
        output:
          type: string
        error_message:
          type: string
          nullable: true

    Pagination:
      type: object
      properties:
        page:
          type: integer
        page_size:
          type: integer
        total_items:
          type: integer
        total_pages:
          type: integer

    ErrorResponse:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
        meta:
          type: object
          properties:
            request_id:
              type: string
            timestamp:
              type: string
              format: date-time
```

### 10.3 Webhook事件模型

```yaml
    GitLabPushEvent:
      type: object
      properties:
        object_kind:
          type: string
          example: push
        ref:
          type: string
        checkout_sha:
          type: string
        commits:
          type: array
          items:
            type: object
        project:
          type: object

    GitLabMergeRequestEvent:
      type: object
      properties:
        object_kind:
          type: string
          example: merge_request
        object_attributes:
          type: object
        project:
          type: object

    GitLabPipelineEvent:
      type: object
      properties:
        object_kind:
          type: string
          example: pipeline
        object_attributes:
          type: object
        builds:
          type: array

    RedmineWebhookPayload:
      type: object
      properties:
        action:
          type: string
          enum: [created, updated, status_changed]
        issue:
          $ref: '#/components/schemas/Issue'
        changes:
          type: object
```

---

## 11. 版本管理

### 11.1 API版本策略

- **当前版本**：v1
- **URL格式**：`/api/v1/...`
- **版本兼容性**：
  - 主版本（v1 → v2）：可能包含破坏性变更
  - 次版本：向后兼容，新增功能
  - 补丁版本：向后兼容，Bug修复

### 11.2 废弃策略

- 废弃的API将在响应头中添加 `Deprecation` 和 `Sunset` 头
- 废弃期至少为3个月
- 废弃期间会在文档中标注替代方案

```http
Deprecation: true
Sunset: Sat, 30 Jun 2026 23:59:59 GMT
Link: </api/v2/jobs>; rel="successor-version"
```

---

## 12. 速率限制

### 12.1 限制规则

| 端点类型 | 限制 | 窗口 |
|----------|------|------|
| 认证接口 | 10次 | 1分钟 |
| 任务创建 | 60次 | 1小时 |
| 知识库搜索 | 100次 | 1分钟 |
| 其他读取接口 | 1000次 | 1分钟 |
| Webhook | 无限制 | - |

### 12.2 响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706612400
```

### 12.3 超限响应

```json
{
  "success": false,
  "error": {
    "code": "ERR_RATE_LIMITED",
    "message": "请求频率超限，请稍后重试",
    "retry_after": 60
  }
}
```

---

**文档版本**：v2.0
**更新日期**：2026-01-30
**状态**：已完善OpenAPI 3.0规范
