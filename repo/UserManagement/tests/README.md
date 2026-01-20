# User Management API Test Suite

## 概述

这是用户管理微服务的完整测试套件，包含功能测试、边界条件测试、安全测试和认证测试。

## 测试结构

### 测试文件说明

- `test_user_api.py` - 用户管理API的核心功能测试
- `test_auth_api.py` - 认证和授权相关测试
- `test_edge_cases.py` - 边界条件、安全测试和异常情况测试
- `conftest.py` - pytest配置和共享fixtures
- `__init__.py` - 测试包初始化文件

### 测试覆盖范围

#### 功能测试 (test_user_api.py)
- ✅ 用户创建 (CRUD操作)
- ✅ 用户列表获取 (分页、过滤、搜索)
- ✅ 单个用户获取
- ✅ 用户信息更新
- ✅ 用户删除
- ✅ 健康检查
- ✅ 数据验证
- ✅ 错误处理

#### 认证测试 (test_auth_api.py)
- ✅ 用户登录
- ✅ 密码重置
- ✅ 无效凭据处理
- ✅ 账户状态检查
- ✅ 令牌验证
- ✅ 并发登录测试

#### 边界条件测试 (test_edge_cases.py)
- ✅ 输入边界值测试
- ✅ Unicode字符处理
- ✅ 特殊字符处理
- ✅ 空值和null值处理
- ✅ 额外字段处理
- ✅ 大小写敏感性测试
- ✅ 分页边界测试

#### 安全测试 (test_edge_cases.py)
- ✅ SQL注入防护
- ✅ XSS攻击防护
- ✅ 密码强度验证
- ✅ 用户名格式验证
- ✅ 并发请求处理
- ✅ 恶意输入处理

## 运行测试

### 环境要求

```bash
# 安装测试依赖
pip install -r requirements.txt

# 确保API服务运行在 localhost:8081
```

### 运行所有测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_user_api.py
pytest tests/test_auth_api.py
pytest tests/test_edge_cases.py

# 运行特定测试类
pytest tests/test_user_api.py::TestUserAPI

# 运行特定测试方法
pytest tests/test_user_api.py::TestUserAPI::test_create_user_success
```

### 测试选项

```bash
# 详细输出
pytest -v

# 显示打印输出
pytest -s

# 运行失败的测试
pytest --lf

# 并行运行测试
pytest -n auto

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 跳过慢速测试
pytest -m "not slow"

# 只运行安全测试
pytest -m security
```

## 测试数据管理

### 自动清理

测试套件包含自动清理机制：
- 每个测试前后自动清理测试用户
- 使用 `test_` 前缀标识测试用户
- 确保测试间的数据隔离

### 测试用户命名规范

- 功能测试: `test_user_001`, `test_admin_001`
- 边界测试: `test_boundary_*`
- 安全测试: `test_security_*`
- 并发测试: `test_concurrent_*`

## 测试指标

### 目标指标

- **测试用例通过率**: 100%
- **代码覆盖率**: >90%
- **API接口覆盖率**: 100%
- **错误场景覆盖率**: 100%

### 性能指标

- 单个测试执行时间: <5秒
- 完整测试套件执行时间: <10分钟
- 并发测试支持: 10个并发用户

## 故障排除

### 常见问题

1. **API服务器未运行**
   ```
   pytest.skip("API server not running")
   ```
   解决方案: 确保用户管理服务运行在 localhost:8081

2. **测试数据冲突**
   ```
   AssertionError: Expected status code 201, got 409
   ```
   解决方案: 检查是否有重复的测试用户，运行清理脚本

3. **网络连接问题**
   ```
   requests.exceptions.ConnectionError
   ```
   解决方案: 检查网络连接和API服务状态

### 调试技巧

```bash
# 运行单个测试并显示详细输出
pytest tests/test_user_api.py::TestUserAPI::test_create_user_success -v -s

# 在失败时进入调试器
pytest --pdb

# 显示最慢的10个测试
pytest --durations=10
```

## 持续集成

### CI/CD配置

测试套件设计为支持持续集成：
- 无状态测试 (每个测试独立)
- 自动清理机制
- 并行执行支持
- 详细的错误报告

### 测试报告

测试完成后会生成：
- 控制台输出报告
- JUnit XML报告 (用于CI系统)
- HTML覆盖率报告
- 性能基准报告

## 扩展测试

### 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用描述性的测试名称
3. 包含适当的断言
4. 遵循现有的命名规范

### 测试最佳实践

- 每个测试应该独立且可重复
- 使用有意义的断言消息
- 测试正面和负面场景
- 包含边界条件测试
- 验证错误处理机制
