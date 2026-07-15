# 智能招标信息采集系统 — API 接口文档

**Base URL**：`http://127.0.0.1:5000`（生产环境请替换为实际域名）  
**Content-Type**：`application/json`（POST 请求）  
**认证方式**：基于 Flask Session Cookie（登录后自动携带）  
**接口总数**：**13 个**（页面路由 5 个 + API 接口 8 个）

---

## 目录

1. [一、通用说明](#一通用说明)
2. [二、登录与登出](#二登录与登出)
3. [三、采集与爬虫相关](#三采集与爬虫相关)
4. [四、招标列表与筛选](#四招标列表与筛选)
5. [五、趋势分析与统计](#五趋势分析与统计)
6. [六、测试工具接口](#六测试工具接口)
7. [七、页面路由汇总](#七页面路由汇总)
8. [八、数据结构定义](#八数据结构定义)
9. [九、Postman 导入脚本示例](#九postman-导入脚本示例)

---

## 一、通用说明

### 1.1 统一响应格式

所有 API 接口采用统一响应结构：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "from_cache": true,
  "total": 150,
  "count": 5,
  "first_insert": true,
  "second_insert": false,
  "url_cached": true,
  "standard_parse": [],
  "robust_parse": [],
  "deduped": false,
  "redirect": "/dashboard"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 是否成功，必返回 |
| message | string | 中文提示消息 |
| data | object/array | 业务数据，不同接口结构不同 |
| from_cache | bool | （仅数据接口）该响应是否来自 Redis 缓存 |
| total | int | （列表接口）符合筛选条件的总记录数 |
| count | int | （爬虫接口）本次新采集到的数量 |
| deduped | bool | （爬虫接口）本次是否因 URL 去重被拦截 |
| redirect | string | （登录接口）登录成功后跳转的前端路径 |
| first_insert / second_insert | bool | （去重测试接口）两次插入的返回值 |
| url_cached | bool | （去重测试接口）URL 是否存在于 Redis 集合 |
| standard_parse / robust_parse | array | （解析测试接口）两种解析规则的结果 |

### 1.2 错误响应示例

```json
{
  "success": false,
  "message": "请先登录"
}
```

### 1.3 HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 | 正常响应（即使业务失败也会返回 200 + success=false） |
| 401 | 未登录 / Session 已过期 |
| 302 | 页面级跳转（如未登录访问 /dashboard） |

### 1.4 枚举值参考

**地区 ID（region）**：`all` / `beijing` / `shanghai` / `guangdong` / `jiangsu` / `zhejiang` / `sichuan` / `hubei` / `henan` / `shandong`

**行业 ID（industry）**：`it` / `construction` / `medical` / `education` / `finance` / `energy` / `transport`

---

## 二、登录与登出

---

### 2.1 用户登录 / 自动注册

```
POST /login
Content-Type: application/json
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（新用户会被自动创建） |
| password | string | 是 | 密码（MD5 存储） |

```json
{
  "username": "tester",
  "password": "test123"
}
```

**成功响应（新用户）** 200 OK：

```json
{
  "success": true,
  "message": "注册并登录成功",
  "redirect": "/dashboard"
}
```

**成功响应（老用户）** 200 OK：

```json
{
  "success": true,
  "message": "登录成功",
  "redirect": "/dashboard"
}
```

**失败响应** 200 OK：

```json
{
  "success": false,
  "message": "用户名和密码不能为空"
}
```

```json
{
  "success": false,
  "message": "密码错误"
}
```

**测试要点**：
- 用户名/密码为空、全空格 → 拒绝
- 新用户名自动创建 → 可在数据库 users 表查询
- 同用户名 + 错误密码 → 密码错误
- 登录后浏览器获得 `session` Cookie

---

### 2.2 登录页（GET）

```
GET /login
```

返回 HTML 页面（`templates/login.html`），无需登录。

---

### 2.3 登出

```
GET /logout
```

清除 Session 后，重定向回登录页（302 → `/login`）。

---

## 三、采集与爬虫相关

---

### 3.1 自定义采集（关键词或URL）

```
POST /api/crawl
Content-Type: application/json
需要登录
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词（中英文皆可，上限 100 字符） |
| url | string | 否 | 目标 URL（必须 http/https/ftp 协议） |

> keyword 与 url 至少填写一个；若两者都填，按 url 模式执行。

```json
{
  "keyword": "软件开发",
  "url": "http://example.com/bid"
}
```

**成功响应（关键词采集）** 200 OK：

```json
{
  "success": true,
  "message": "成功获取5条新数据",
  "count": 5,
  "data": [
    {
      "title": "[北京]关于软件开发项目的招标公告",
      "content": "本项目为软件开发...",
      "url": "http://example.com/bidding/123",
      "region": "beijing",
      "industry": "it",
      "publish_date": "2024-06-10",
      "source": "中国政府采购网",
      "budget": 286.50,
      "keywords": "软件开发,信息技术,招标"
    }
  ]
}
```

**成功响应（URL重复，被去重拦截）** 200 OK：

```json
{
  "success": true,
  "message": "该URL已处理（去重）",
  "count": 0,
  "deduped": true
}
```

**失败响应** 200 OK：

```json
{
  "success": false,
  "message": "请输入关键词或URL"
}
```

```json
{
  "success": false,
  "message": "URL格式无效，请检查"
}
```

```json
{
  "success": false,
  "message": "关键词过长"
}
```

**未登录响应** 401 Unauthorized：

```json
{
  "success": false,
  "message": "请先登录"
}
```

---

### 3.2 最近采集任务列表

```
GET /api/tasks?limit=10
需要登录
```

**查询参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|-------|------|
| limit | int | 10 | 返回最近 N 条任务 |

**成功响应** 200 OK：

```json
{
  "success": true,
  "data": [
    {
      "id": 15,
      "user_id": 1,
      "keyword": "软件开发",
      "url": "",
      "status": "completed",
      "result_count": 5,
      "created_at": "2024-06-20 10:21:30"
    }
  ]
}
```

**字段说明**：
- status 可能值：`completed` / `duplicate` / `failed`
- url 为空表示按关键词模式采集
- result_count 为本次新插入的条数

---

## 四、招标列表与筛选

---

### 4.1 招标列表查询

```
GET /api/bidding?region=all&industry=&keyword=&start_date=&end_date=&sort_by=date&page=1&per_page=20
需要登录
```

**查询参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|-------|------|
| region | string | `all` | 地区 ID（参考 1.4 枚举值）|
| industry | string | 空 | 行业 ID（留空=全部）|
| keyword | string | 空 | 模糊搜索（匹配 title 和 keywords 字段）|
| start_date | string | 空 | 起始日期，格式 `YYYY-MM-DD` |
| end_date | string | 空 | 结束日期，格式 `YYYY-MM-DD` |
| sort_by | string | `date` | 排序方式：`date`（按发布日期）/ `budget`（按预算金额）|
| page | int | 1 | 页码，从 1 开始 |
| per_page | int | 20 | 每页条数 |

**请求示例**：

```
GET /api/bidding?region=beijing&industry=it&keyword=软件&sort_by=budget&page=1&per_page=10
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "from_cache": false,
  "total": 45,
  "data": [
    {
      "id": 101,
      "title": "[北京]关于软件开发服务的招标公告",
      "content": "本项目为软件开发相关招标...",
      "url": "http://example.com/bid/101",
      "region": "beijing",
      "region_name": "北京",
      "industry": "it",
      "publish_date": "2024-06-15",
      "source": "中国政府采购网",
      "budget": 1280.50,
      "keywords": "软件开发,信息技术,招标",
      "created_at": "2024-06-20 10:21:30"
    }
  ]
}
```

**字段说明**：
- `from_cache=true` 表示该响应来自 Redis 缓存（5 分钟 TTL）
- `data` 数组长度不超过 `per_page`
- `total` 为符合筛选条件的总记录数（用于分页计算）
- `region_name` 为地区中文名称，方便前端直接展示

**缓存命中响应示例**：

```json
{
  "success": true,
  "from_cache": true,
  "total": 45,
  "data": [...]
}
```

---

### 4.2 单条招标详情（页面）

```
GET /detail/{bid_id}
需要登录（返回 HTML 页面）
```

**路径参数**：`bid_id` - 招标记录 ID（整型）

返回 HTML 页面，展示该条招标的完整字段详情。

---

## 五、趋势分析与统计

---

### 5.1 发布数量趋势（按天 / 按行业）

```
GET /api/trend?days=30
需要登录
```

**查询参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|-------|------|
| days | int | 30 | 统计最近 N 天的数据 |

**成功响应** 200 OK：

```json
{
  "success": true,
  "from_cache": false,
  "data": [
    { "date": "2024-06-18", "cnt": 7, "industry": "it" },
    { "date": "2024-06-18", "cnt": 3, "industry": "construction" },
    { "date": "2024-06-19", "cnt": 5, "industry": "it" }
  ]
}
```

**字段说明**：
- 每天 × 每个行业组合一条数据
- `cnt` 为该天该行业的发布数量
- 缓存 TTL = 600 秒（10 分钟）

---

### 5.2 地区分布

```
GET /api/region-distribution
需要登录
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "from_cache": false,
  "data": [
    { "region": "beijing", "name": "北京", "cnt": 22, "avg_budget": 1580.30 },
    { "region": "shanghai", "name": "上海", "cnt": 18, "avg_budget": 1350.80 }
  ]
}
```

---

### 5.3 行业分布

```
GET /api/industry-distribution
需要登录
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "from_cache": false,
  "data": [
    { "industry": "it", "name": "信息技术", "cnt": 45, "total_budget": 38500.00 },
    { "industry": "construction", "name": "建筑工程", "cnt": 30, "total_budget": 27800.50 }
  ]
}
```

---

### 5.4 高频关键词分析

```
GET /api/keyword-analysis
需要登录
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "from_cache": false,
  "data": [
    { "word": "软件开发", "count": 28 },
    { "word": "招标", "count": 45 },
    { "word": "云计算", "count": 12 }
  ]
}
```

> 返回 TOP 50 高频关键词，供词云图 / 标签云渲染使用

---

### 5.5 系统统计面板

```
GET /api/stats
需要登录
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "data": {
    "total_records": 150,
    "cached_urls": 75,
    "regions_count": 9,
    "industries_count": 7
  }
}
```

---

## 六、测试工具接口

---

### 6.1 URL 去重功能验证

```
POST /api/dedupe-test
Content-Type: application/json
需要登录
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 测试用标题（默认 "测试重复标题"）|
| url | string | 否 | 测试用 URL（默认 "http://test.com/duplicate"）|

```json
{
  "title": "重复测试标题_001",
  "url": "http://test.com/dedup001"
}
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "first_insert": true,
  "second_insert": false,
  "url_cached": true,
  "message": "去重功能验证完成"
}
```

**字段含义**：
- `first_insert=true` → 第一条数据成功写入数据库
- `second_insert=false` → 第二条相同 URL 的数据被数据库唯一索引拦截
- `url_cached=true` → 该 URL 已在 Redis 去重集合中记录

> 该接口用于验证 "Redis集合 + 数据库唯一索引" 双重去重机制

---

### 6.2 HTML 解析规则测试

```
POST /api/parse-test
Content-Type: application/json
需要登录
```

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| html | string | 否 | 自定义 HTML 片段（不传则使用内置示例） |

```json
{
  "html": "<table><tr><td class=\"td_1\">项目A</td><td>2024-01-01</td></tr></table>"
}
```

**成功响应** 200 OK：

```json
{
  "success": true,
  "standard_parse": [
    { "title": "项目A", "url": "", "publish_date": "2024-01-01" }
  ],
  "robust_parse": [
    { "title": "项目A", "date": "2024-01-01", "cells_count": 2 }
  ],
  "message": "标准解析找到1条，容错解析找到1条"
}
```

**解析规则说明**：
- `standard_parse`：优先匹配 `class="td_1"` 的 `<td>` 标签
- `robust_parse`：不受 td_1 限制，匹配所有 `<td>` 标签（应对网站改版场景）
- 当两种解析结果数量不一致时，可能表示 HTML 结构发生变动

---

## 七、页面路由汇总

| 方法 | 路径 | 是否需登录 | 说明 |
|------|------|----------|------|
| GET | `/` | 否 | 根路径，自动跳转（登录→控制台，否则→登录页）|
| GET | `/dashboard` | 是 | 控制台（自定义采集 + 任务记录 + 测试工具）|
| GET | `/list` | 是 | 招标列表 + 筛选 |
| GET | `/analysis` | 是 | 趋势分析图表 |
| GET | `/detail/{bid_id}` | 是 | 单条招标详情页 |
| GET | `/login` | 否 | 登录页（表单页面）|
| POST | `/login` | 否 | 登录提交（API）|
| GET | `/logout` | 否 | 登出 |

---

## 八、数据结构定义

### 8.1 招标数据对象（BiddingItem）

```json
{
  "id": 101,
  "title": "[北京]关于软件开发项目的招标公告",
  "content": "本项目为软件开发...",
  "url": "http://example.com/bid/101",
  "region": "beijing",
  "region_name": "北京",
  "industry": "it",
  "publish_date": "2024-06-15",
  "source": "中国政府采购网",
  "budget": 1280.50,
  "keywords": "软件开发,信息技术,招标",
  "created_at": "2024-06-20 10:21:30"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 数据库自增主键 |
| title | string | 标题 |
| content | string | 内容摘要 |
| url | string | 原始链接（MD5 哈希用于去重）|
| region | string | 地区 ID（枚举值）|
| region_name | string | 地区中文名（仅列表接口返回）|
| industry | string | 行业 ID（枚举值）|
| publish_date | string | 发布日期 YYYY-MM-DD |
| source | string | 来源网站名 |
| budget | float | 预算金额（万元）|
| keywords | string | 关键词（英文逗号分隔）|
| created_at | string | 入库时间 |

### 8.2 任务记录对象（TaskItem）

```json
{
  "id": 15,
  "user_id": 1,
  "keyword": "软件开发",
  "url": "",
  "status": "completed",
  "result_count": 5,
  "created_at": "2024-06-20 10:21:30"
}
```

---

## 九、Postman 导入脚本示例

可将以下 JSON 保存为 `zhaobiao-postman.json`，在 Postman 中通过 Import → File 导入。

```json
{
  "info": {
    "name": "智能招标信息采集系统 API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    { "key": "base_url", "value": "http://127.0.0.1:5000", "type": "string" }
  ],
  "item": [
    {
      "name": "1. 登录",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/login",
        "body": {
          "mode": "raw",
          "raw": "{\"username\":\"tester\",\"password\":\"test123\"}"
        }
      }
    },
    {
      "name": "2. 关键词采集",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/api/crawl",
        "body": {
          "mode": "raw",
          "raw": "{\"keyword\":\"软件开发\"}"
        }
      }
    },
    {
      "name": "3. URL采集（去重测试）",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/api/crawl",
        "body": {
          "mode": "raw",
          "raw": "{\"keyword\":\"测试\",\"url\":\"http://test.com/dedup-test\"}"
        }
      }
    },
    {
      "name": "4. 招标列表 - 默认筛选",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/bidding?region=all&sort_by=date&page=1&per_page=20"
      }
    },
    {
      "name": "5. 招标列表 - 地区+行业+关键词",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/bidding?region=beijing&industry=it&keyword=软件&sort_by=budget&page=1&per_page=10"
      }
    },
    {
      "name": "6. 30天趋势",
      "request": { "method": "GET", "url": "{{base_url}}/api/trend?days=30" }
    },
    {
      "name": "7. 地区分布",
      "request": { "method": "GET", "url": "{{base_url}}/api/region-distribution" }
    },
    {
      "name": "8. 行业分布",
      "request": { "method": "GET", "url": "{{base_url}}/api/industry-distribution" }
    },
    {
      "name": "9. 关键词分析",
      "request": { "method": "GET", "url": "{{base_url}}/api/keyword-analysis" }
    },
    {
      "name": "10. 系统统计",
      "request": { "method": "GET", "url": "{{base_url}}/api/stats" }
    },
    {
      "name": "11. 最近任务记录",
      "request": { "method": "GET", "url": "{{base_url}}/api/tasks?limit=10" }
    },
    {
      "name": "12. 去重测试接口",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/api/dedupe-test",
        "body": { "mode": "raw", "raw": "{\"title\":\"测试标题\",\"url\":\"http://test.com/auto-test\"}" }
      }
    },
    {
      "name": "13. HTML解析测试",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/api/parse-test",
        "body": { "mode": "raw", "raw": "{}" }
      }
    }
  ]
}
```

---

**文档结束**
