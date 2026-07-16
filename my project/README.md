# 智能招标信息采集系统

基于 Python Flask 的招标数据采集与分析平台，支持关键词/URL 双模式采集、三层 URL 去重、六维组合筛选和 ECharts 可视化分析。

## 功能模块

- **用户认证**：注册/登录，Session 管理，登录拦截
- **数据采集**：关键词采集 + URL 采集双模式，模拟招标数据生成
- **三层去重**：MD5 哈希 → 缓存 Set → 数据库唯一索引
- **招标列表**：地区/行业/关键词/日期范围/排序/分页六维组合筛选
- **趋势分析**：折线图、饼图、柱状图、词云、热力图（ECharts 5.x）
- **HTML 解析**：标准表格解析 + 容错解析双策略
- **任务管理**：采集任务记录与查询

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.x + Flask 3.0 |
| 数据库 | SQLite |
| 缓存 | JSON 文件缓存（模拟 Redis，支持 KV + Set） |
| 前端 | HTML + CSS + 原生 JS + ECharts 5.x |
| 解析 | BeautifulSoup4 + lxml |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化测试数据
python init_data.py

# 3. 启动服务
python app.py
```

访问 http://127.0.0.1:5000，任意用户名密码即可注册并登录。

## 项目结构

```
.
├── app.py              # Flask 主应用，13 个路由
├── database.py         # SQLite 数据操作层
├── crawler.py          # 数据采集引擎
├── cache.py            # JSON 文件缓存层（模拟 Redis）
├── config.py           # 配置（地区、行业、采集源）
├── init_data.py        # 测试数据初始化脚本
├── requirements.txt    # 依赖清单
├── templates/          # Jinja2 页面模板
│   ├── login.html
│   ├── dashboard.html
│   ├── list.html
│   ├── analysis.html
│   └── detail.html
└── static/
    ├── css/style.css
    └── js/
        ├── dashboard.js
        ├── list.js
        └── analysis.js
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login` | 登录/注册 |
| GET | `/dashboard` | 控制台页面 |
| GET | `/list` | 招标列表页面 |
| GET | `/analysis` | 趋势分析页面 |
| GET | `/detail/<id>` | 招标详情页面 |
| POST | `/api/crawl` | 数据采集（关键词/URL） |
| GET | `/api/bidding` | 招标列表查询 |
| GET | `/api/trend` | 趋势数据 |
| GET | `/api/region-distribution` | 地区分布 |
| GET | `/api/industry-distribution` | 行业分布 |
| GET | `/api/keyword-analysis` | 关键词分析 |
| GET | `/api/stats` | 统计面板 |
| GET | `/api/tasks` | 采集任务列表 |

## License

MIT
