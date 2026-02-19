Flask 微服务基准（Benchmark）

功能描述

本基准用于评估基于 Flask 的简单 Web 微服务能力。服务提供健康探测、字符串回显与求和计算三个接口。实现方式不作限定，但需满足下述对外接口契约。需求文档不包含具体函数名，仅定义微服务监听端口、接口名称、输入输出约定。

服务约束

端口

服务默认监听端口：5000。

接口定义

GET /health

语义：健康检查。

输入：无。

输出（application/json）：

{
  "status": "ok"
}

状态码：200。

POST /echo

语义：回显请求体中的消息，并返回其长度。

输入（application/json）：

{
  "message": "<string>"
}

输出（application/json）：

{
  "message": "<string>",
  "length": <int>
}

状态码：200。输入缺失或类型错误时应返回 400（application/json，包含错误原因）。

GET /sum

语义：对两个整数求和。

输入（query）：a=<int>&b=<int>

输出（application/json）：

{
  "result": <int>
}

状态码：200。参数缺失或非整数时应返回 400（application/json，包含错误原因）。

测试说明

tests 目录提供黑盒测试：

- 基于接口契约构造请求与断言响应行为。
- 采用 Flask 测试客户端构造最小应用以校验接口契约与边界条件（输入缺失、类型错误等）。

运行方法

在仓库根目录执行：

pytest -q repo_ori/flask/tests



