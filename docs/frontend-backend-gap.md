# 前后端对接缺口

## 已接通

- `POST /api/auth/wechat-login`
- `GET /api/travels`
- `POST /api/travels`
- `GET /api/travels/{id}`
- `PATCH /api/travels/{id}`
- `POST /api/travels/{id}/members`
- `PATCH /api/travels/{id}/members/{memberId}`
- `DELETE /api/travels/{id}/members/{memberId}`
- `POST /api/travels/{id}/members/{memberId}/clear-claim`
- `POST /api/travels/{id}/expenses`
- `POST /api/travels/{id}/settle`
- `GET /api/travels/{id}/settlement`
- `GET /api/travels/{id}/settlement/detail`
- `POST /api/uploads/avatar`

## 还没接

- `GET /api/invites/{inviteCode}` 与 `POST /api/travels/join`
- `GET /api/travels/{id}/me` 与 `PATCH /api/travels/{id}/me`
- `POST /api/travels/{id}/binding` / `DELETE /api/travels/{id}/binding`
- `GET /api/travels/{id}/expenses` 的列表分页、筛选入口
- 账单详情编辑页的 `GET /PATCH /DELETE /api/travels/{id}/expenses/{expenseId}`
- 猫猫家庭、预收款、基金独立台账
- 归档 / 删除旅行

## 说明

前端现在已经从本地 demo store 切到后端主数据源；上面这些缺口先保留为页面上的本地功能或占位，不阻塞主流程。
