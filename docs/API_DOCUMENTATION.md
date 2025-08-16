# 智能测试报告系统 API 文档

## 概述

本文档描述了智能测试报告系统的RESTful API接口，包括认证、报告管理、数据分析、监控等功能模块的API使用方法。

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证方式

### JWT Token认证

所有API请求需要在Header中包含JWT Token：

```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### 获取Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

响应：
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

## API接口详情

### 1. 报告管理 API

#### 1.1 获取报告列表

```http
GET /api/reports
```

查询参数：
- `page`: 页码（默认：1）
- `size`: 每页数量（默认：10）
- `type`: 报告类型（execution/defect/coverage）
- `status`: 报告状态（generating/completed/failed）
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）

响应示例：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "测试执行报告",
        "report_type": "execution",
        "status": "completed",
        "generated_by": "admin",
        "generation_time": "2024-01-15T10:30:00Z",
        "file_path": "/uploads/reports/report_1.pdf"
      }
    ],
    "total": 25,
    "page": 1,
    "size": 10,
    "pages": 3
  }
}
```#### 1
.2 生成报告

```http
POST /api/reports/generate
```

请求体：
```json
{
  "report_type": "execution",
  "title": "月度测试执行报告",
  "template_id": 1,
  "time_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "filters": {
    "test_case_ids": [1, 2, 3],
    "requirement_ids": [10, 11],
    "priority": "high"
  }
}
```

响应：
```json
{
  "success": true,
  "data": {
    "report_id": 123,
    "status": "generating",
    "estimated_completion": "2024-01-15T10:35:00Z"
  }
}
```

#### 1.3 获取报告详情

```http
GET /api/reports/{report_id}
```

响应：
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "月度测试执行报告",
    "report_type": "execution",
    "status": "completed",
    "report_data": {
      "summary": {
        "total_test_cases": 150,
        "passed": 135,
        "failed": 15,
        "pass_rate": 0.9
      },
      "details": {
        // 详细数据
      }
    },
    "file_path": "/uploads/reports/report_123.pdf",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 1.4 导出报告

```http
GET /api/reports/{report_id}/export
```

查询参数：
- `format`: 导出格式（pdf/excel/html）

响应：文件流

#### 1.5 删除报告

```http
DELETE /api/reports/{report_id}
```

### 2. 数据分析 API

#### 2.1 获取统计数据

```http
GET /api/analytics/stats
```

查询参数：
- `metric`: 指标类型（coverage/defects/performance）
- `period`: 时间周期（1d/7d/30d/90d）
- `group_by`: 分组方式（date/module/priority）

响应：
```json
{
  "success": true,
  "data": {
    "metric": "coverage",
    "period": "30d",
    "data": [
      {
        "date": "2024-01-01",
        "value": 85.5,
        "details": {
          "total_requirements": 200,
          "covered_requirements": 171
        }
      }
    ]
  }
}
```

#### 2.2 获取趋势分析

```http
GET /api/analytics/trends
```

查询参数：
- `type`: 趋势类型（defects/coverage/performance）
- `range`: 时间范围（7d/30d/90d）
- `granularity`: 数据粒度（hour/day/week）

响应：
```json
{
  "success": true,
  "data": {
    "type": "defects",
    "trend_data": [
      {
        "timestamp": "2024-01-01T00:00:00Z",
        "value": 12,
        "change_rate": 0.15
      }
    ],
    "prediction": {
      "next_period_estimate": 10,
      "confidence": 0.85
    }
  }
}
```

#### 2.3 获取智能建议

```http
GET /api/analytics/suggestions
```

查询参数：
- `context`: 建议上下文（optimization/risk/coverage）
- `limit`: 返回数量限制

响应：
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "id": 1,
        "type": "optimization",
        "priority": "high",
        "title": "优化重复测试用例",
        "description": "发现15个功能相似的测试用例，建议合并以提高效率",
        "impact_score": 8.5,
        "effort_estimate": "2小时",
        "recommended_actions": [
          "合并测试用例TC001和TC002",
          "重构测试数据准备逻辑"
        ]
      }
    ]
  }
}
```

### 3. 监控 API

#### 3.1 获取系统状态

```http
GET /api/monitoring/status
```

响应：
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "services": {
      "database": {
        "status": "healthy",
        "response_time": 15,
        "last_check": "2024-01-15T10:30:00Z"
      },
      "redis": {
        "status": "healthy",
        "memory_usage": "45%",
        "connections": 12
      }
    },
    "system_metrics": {
      "cpu_usage": 25.5,
      "memory_usage": 68.2,
      "disk_usage": 45.8
    }
  }
}
```

#### 3.2 获取监控指标

```http
GET /api/monitoring/metrics
```

查询参数：
- `metric`: 指标名称（response_time/error_rate/throughput）
- `period`: 时间周期（1h/6h/24h）
- `resolution`: 数据分辨率（1m/5m/1h）

响应：
```json
{
  "success": true,
  "data": {
    "metric": "response_time",
    "unit": "ms",
    "data_points": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "value": 125.5,
        "percentiles": {
          "p50": 100,
          "p95": 200,
          "p99": 350
        }
      }
    ]
  }
}
```

#### 3.3 配置告警规则

```http
POST /api/monitoring/alerts
```

请求体：
```json
{
  "rule_name": "高错误率告警",
  "metric_type": "error_rate",
  "condition": {
    "operator": "greater_than",
    "threshold": 0.05,
    "duration": "5m"
  },
  "severity": "critical",
  "notification_channels": ["email", "slack"],
  "recipients": ["admin@example.com"],
  "is_active": true
}
```

#### 3.4 获取告警历史

```http
GET /api/monitoring/alerts/history
```

查询参数：
- `severity`: 告警级别（info/warning/critical）
- `status`: 告警状态（active/resolved/acknowledged）
- `start_time`: 开始时间
- `end_time`: 结束时间

### 4. 模板管理 API

#### 4.1 获取模板列表

```http
GET /api/templates
```

#### 4.2 创建模板

```http
POST /api/templates
```

请求体：
```json
{
  "template_name": "标准执行报告模板",
  "template_type": "execution",
  "template_content": "<!DOCTYPE html>...",
  "template_config": {
    "sections": ["summary", "details", "charts"],
    "chart_types": ["bar", "line", "pie"]
  }
}
```

#### 4.3 更新模板

```http
PUT /api/templates/{template_id}
```

#### 4.4 删除模板

```http
DELETE /api/templates/{template_id}
```

## 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 使用示例

### Python示例

```python
import requests

# 登录获取token
login_response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_response.json()['data']['access_token']

# 设置请求头
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# 生成报告
report_response = requests.post('http://localhost:8000/api/reports/generate', 
    headers=headers,
    json={
        'report_type': 'execution',
        'title': '测试报告',
        'time_range': {
            'start': '2024-01-01',
            'end': '2024-01-31'
        }
    }
)

print(report_response.json())
```

### JavaScript示例

```javascript
// 登录获取token
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
    })
});

const { data: { access_token } } = await loginResponse.json();

// 获取报告列表
const reportsResponse = await fetch('http://localhost:8000/api/reports', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});

const reports = await reportsResponse.json();
console.log(reports);
```

## 限制说明

- API请求频率限制：每分钟100次
- 文件上传大小限制：100MB
- 报告生成超时时间：10分钟
- 并发报告生成数量：5个

## 版本更新

### v1.1.0 (计划中)
- 新增批量操作API
- 支持Webhook通知
- 增强权限控制

### v1.0.0 (当前版本)
- 基础功能API
- 报告生成和管理
- 数据分析和监控

---

*API文档最后更新时间: 2024年1月*