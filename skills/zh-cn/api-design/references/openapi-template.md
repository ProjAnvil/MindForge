## OpenAPI 规范模板

### 完整示例

```yaml
openapi: 3.0.0
info:
  title: Blog API
  version: 1.0.0
  description: 博客平台 RESTful API

servers:
  - url: https://api.example.com/v1
    description: 生产服务器

paths:
  /users:
    get:
      summary: 列出用户
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
    post:
      summary: 创建用户
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: 已创建
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        username:
          type: string
        email:
          type: string
        created_at:
          type: string
          format: date-time
```

### 最佳实践模板

```yaml
openapi: 3.0.0

info:
  title: Your API Name
  version: 1.0.0
  description: |
    详细的 API 描述
    
    ## 认证
    使用 Bearer token
    
    ## 错误处理
    所有错误都返回标准格式
  contact:
    name: API Support
    url: https://support.example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: 生产环境
  - url: https://staging.example.com/v1
    description: 测试环境

paths:
  /resources:
    get:
      tags:
        - Resources
      summary: 列出资源
      operationId: listResources
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/SizeParam'
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
    post:
      tags:
        - Resources
      summary: 创建资源
      operationId: createResource
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResourceRequest'
      responses:
        '201':
          description: 已创建
          headers:
            Location:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceResponse'
        '400':
          $ref: '#/components/responses/BadRequest'

components:
  schemas:
    Error:
      type: object
      properties:
        code:
          type: integer
        message:
          type: string
        details:
          type: object
      required:
        - code
        - message

    ResourceList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Resource'
        pagination:
          $ref: '#/components/schemas/Pagination'

    Resource:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        created_at:
          type: string
          format: date-time
      required:
        - id
        - name

  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        default: 1

    SizeParam:
      name: size
      in: query
      schema:
        type: integer
        default: 20

  responses:
    BadRequest:
      description: 请求无效
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: 未授权
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

### 使用 OpenAPI 的优点

- **自动化文档生成** - Swagger UI、Redoc
- **客户端代码生成** - 自动生成 SDK
- **API 契约测试** - 验证实现符合规范
- **版本控制** - 追踪 API 变更
- **开发者体验** - 清晰的 API 文档和示例
