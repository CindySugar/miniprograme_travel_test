# 后端接口需求文档

## 1. 范围

- 前端项目：旅行 AA 记账 / 猫猫鱼记账微信小程序
- 项目路径：`/home/bo/miniprograme_travel_test`
- 分析日期：2026-06-18
- 证据来源：
  - 页面配置：`app.json`
  - 页面代码：`pages/index`、`pages/create`、`pages/logs`、`pages/expense`、`pages/settlement`
  - 本地数据层：`utils/travel-store.js`
  - 当前后端骨架：`backend/trips/models.py`、`serializers.py`、`views.py`、`urls.py`、`services.py`
  - 需求说明：`项目整体情况说明.md`、`PRD.md`
- 当前状态：前端主要使用 `utils/travel-store.js` + `wx.setStorageSync` 本地存储；后端已有 Django/DRF 基础接口，但尚未接入小程序请求层。

## 2. 页面与接口总览

| 页面 | 路径 | 当前数据来源 | P0 接口 | P1/P2 接口 | 备注 |
|---|---|---|---|---|---|
| 首页 / 我的组队 | `pages/index/index` | `store.getCurrentUser()`、`store.listTravels()` | `POST /api/auth/wechat-login`；`GET /api/travels` | `DELETE /api/travels/{id}`；`PATCH /api/travels/{id}/archive` | 页面上有“归档/删除/查看全部”视觉入口，但当前未绑定实际操作。 |
| 创建组队 | `pages/create/create` | `store.getCurrentUser()`、预览成员本地 state、`store.createTravel()` | `POST /api/travels` | `POST /api/uploads/avatar`；创建后邀请卡/邀请码接口；高级规则字段扩展 | `advanceAmount`、`catFund`、权限开关目前只在页面 state 中，未进入本地 createTravel payload。 |
| 旅行详情 | `pages/logs/logs` | `store.getTravel()`、`store.listTravels()[0]`、`store.addMember()`、`store.markTravelCompleted()` | `GET /api/travels/{id}`；`POST /api/travels/{id}/members`；`POST /api/travels/{id}/settle` 或 `PATCH /api/travels/{id}` | `POST /api/travels/join`；成员认领；成员家庭管理；账单编辑/删除 | “邀请同行”当前复制 `inviteCode`；“编辑账单入口稍后补上”。 |
| 新增花销 | `pages/expense/expense` | `store.getTravel()`、`store.addExpense()` | `GET /api/travels/{id}`；`POST /api/travels/{id}/expenses` | 分类字典接口；编辑花销接口 | 付款人和分摊人来自旅行成员列表。 |
| 结算结果 | `pages/settlement/settlement` | `store.getTravel()` 本地计算 summary | `GET /api/travels/{id}/settlement` | `POST /api/travels/{id}/settlement/confirm` | 后端已有 `GET /api/travels/{id}/settlement/` 计算能力。 |

## 3. 当前已有后端能力对照

Django 路由前缀来自 `backend/travel_splitter/urls.py`：`/api/`。

当前 `backend/trips/urls.py` 使用 DRF `DefaultRouter` 注册：

```text
/api/travels/
/api/travels/{id}/
/api/travels/{id}/members/
/api/travels/{id}/expenses/
/api/travels/{id}/settlement/
```

当前后端已实现：

| 当前接口 | 方法 | 后端位置 | 能力 | 与前端差距 |
|---|---|---|---|---|
| `/api/travels/` | GET | `TravelViewSet.list` | 返回全部旅行 | 需要按当前用户过滤；需要返回前端展示字段或统一转换。 |
| `/api/travels/{id}/` | GET | `TravelViewSet.retrieve` | 返回旅行详情、成员、账单、settlement | 前端字段是 camelCase，本接口是 snake_case；缺少 display 字段可前端计算。 |
| `/api/travels/` | POST | `TravelViewSet.create` | 创建旅行和 owner 成员 | 只接收 `title/destination/start_date/owner_openid/owner_nickname`；缺少头像、初始成员、预收/基金、权限。 |
| `/api/travels/{id}/members/` | POST | `TravelViewSet.members` | 添加成员 | 当前用 openid/nickname；前端支持临时成员无 openid，需要保留。 |
| `/api/travels/{id}/expenses/` | POST | `TravelViewSet.expenses` | 添加账单和分摊成员 | 当前请求用 `payer_openid` 和 `participant_openids`；前端使用 memberId。需要统一。 |
| `/api/travels/{id}/settlement/` | GET | `TravelViewSet.settlement` | 计算并保存结算 payload | 返回字段 snake_case；前端当前需要 display 格式可前端继续处理。 |

## 4. 通用约定建议

### 4.1 Base URL

```text
开发环境：待确认，例如 http://127.0.0.1:8000/api
生产环境：待确认
```

### 4.2 鉴权

当前前端 `app.js` 已调用 `wx.login`，但未向后端交换身份。建议：

1. 小程序启动时调用 `wx.login` 获取 `code`。
2. 前端 `POST /api/auth/wechat-login`。
3. 后端用 `code` 换取 `openid/session_key`，创建或更新用户。
4. 返回业务 `token` 或 session 标识。
5. 后续请求携带：

```http
Authorization: Bearer <token>
```

如果短期先本地联调，可临时继续传 `openid`，但正式接口应避免由前端直接伪造 openid。

### 4.3 响应包裹

当前 DRF 直接返回 serializer 数据。为了小程序端统一处理，建议新接口统一为：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

若保持 DRF 原样返回，也需要在前端 request wrapper 中统一适配。

### 4.4 命名风格

- 后端 Django 当前是 snake_case：`start_date`、`invite_code`。
- 前端本地 store 当前是 camelCase：`startDate`、`inviteCode`、`memberCount`。

建议二选一：

1. 后端继续 snake_case，前端 request 层统一转换为 camelCase。
2. 后端 API serializer 直接输出 camelCase。

为了减少前端改动，推荐 API 响应对小程序输出 camelCase。

### 4.5 分页

首页当前只显示最近 1 个，但有“查看全部”。建议列表接口支持分页：

```text
page: number
pageSize: number
total: number
list: TravelSummary[]
```

## 5. 数据模型

以下模型基于当前前端字段和后端模型整理。字段名优先使用前端 camelCase。

```ts
interface CurrentUser {
  id?: number;
  openid: string;
  name: string;
  nickname?: string;
  avatarUrl: string;
}

interface TravelMember {
  id: string | number;
  openid?: string;          // 临时成员可为空
  name: string;
  avatarUrl?: string;
  isOwner: boolean;
  familyId?: string | number; // P1，猫猫家庭功能需要
  claimed?: boolean;          // P1，认领身份需要
}

interface ExpenseShareWeight {
  memberId: string | number;
  weight: number;
}

interface Expense {
  id: string | number;
  title: string;
  category: string;
  amount: number | string;
  amountDisplay?: string;
  payerId: string | number;
  payerName?: string;
  note?: string;
  paidAt: string;
  createdAt?: string;
  shareWeights: ExpenseShareWeight[];
  participantNames?: string;
}

interface TravelSummaryBalance {
  memberId: string | number;
  name: string;
  paid: string;
  owed: string;
  net: string;
}

interface TransferSuggestion {
  fromMemberId: string | number;
  fromName: string;
  toMemberId: string | number;
  toName: string;
  amount: string;
}

interface TravelSummary {
  totalSpent: string;
  balances: TravelSummaryBalance[];
  transfers: TransferSuggestion[];
}

interface Travel {
  id: string | number;
  title: string;
  destination?: string;
  currency: "CNY" | string;
  startDate?: string;
  endDate?: string;
  status: "进行中" | "已结清" | "active" | "settled";
  inviteCode: string;
  createdAt?: string;
  updatedAt?: string;
  ownerId?: string | number;
  members: TravelMember[];
  expenses: Expense[];
  summary: TravelSummary;

  // P1 高级规则
  advanceAmount?: string;
  catFund?: string;
  permissions?: TravelPermissions;
}

interface TravelPermissions {
  allowMemberFamilyEdit: boolean;
  allowInvitedIdentity: boolean;
  requireAvatar: boolean;
}
```

## 6. 接口详情

### 6.1 微信登录 / 当前用户

#### POST /api/auth/wechat-login

用途：把 `wx.login` 返回的 code 交换成后端登录态，并返回当前用户信息。

前端来源：
- `app.js:6` 调用 `wx.login`
- `项目整体情况说明.md` 明确下一步需要接入微信登录、openid、用户表绑定

优先级：P0
状态：需新增

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | string | 是 | `wx.login` 返回的临时 code。 |
| nickname | string | 否 | 用户昵称，可能来自 `type="nickname"` 输入。 |
| avatarUrl | string | 否 | 用户头像 URL 或上传后 URL。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "token": "session-or-jwt-token",
    "user": {
      "id": 1,
      "openid": "openid-from-wechat",
      "name": "你",
      "avatarUrl": ""
    }
  }
}
```

错误/空态：
- 400：code 缺失或无效。
- 502：微信服务异常，前端提示稍后重试。

备注/问题：
- 需确认使用 JWT、DRF Token 还是自定义 session。
- 当前后端 `User` 已有 `openid/nickname/avatar_url` 字段，可以承载。

#### GET /api/me

用途：进入首页或恢复会话时获取当前用户。

前端来源：
- `pages/index/index.js:5` 使用 `store.getCurrentUser()`
- `pages/create/create.js:12` 使用当前用户展示登录状态、默认管理员

优先级：P1
状态：需新增

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "openid": "openid-from-wechat",
    "name": "你",
    "avatarUrl": ""
  }
}
```

### 6.2 首页 / 旅行列表

#### GET /api/travels

用途：首页展示“我的猫猫组队”列表，并支持后续“查看全部”。

前端来源：
- `pages/index/index.js:11`：`store.listTravels()`
- `pages/index/index.wxml:26-54`：展示最近旅行卡片
- 当前后端已有：`TravelViewSet.list`

优先级：P0
状态：已有后端基础能力，需改为按当前用户过滤并适配前端字段

Request query:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page | number | 否 | 页码，默认 1。 |
| pageSize | number | 否 | 每页数量，默认 20。 |
| status | string | 否 | `active` / `settled`，用于筛选。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "杭州周末游",
        "destination": "杭州",
        "currency": "CNY",
        "startDate": "2026-06-18",
        "endDate": "",
        "status": "进行中",
        "inviteCode": "HK1234",
        "createdAt": "2026-06-18T10:00:00Z",
        "memberCount": 3,
        "expenseCount": 2,
        "summary": {
          "totalSpent": "374.00",
          "balances": [],
          "transfers": []
        }
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20
  }
}
```

错误/空态：
- 空列表：前端显示“还没有旅行”。
- 401：未登录，前端先触发登录流程。

备注/问题：
- 当前首页 `index.wxml` 仍有硬编码 `4 只猫猫`、`1 笔账单`、`2026-06-15 更新`，接 API 时应改成接口字段或前端计算字段。

### 6.3 创建组队

#### POST /api/travels

用途：创建一次旅行/组队账本，包含管理员、初始成员、活动信息和可选高级规则。

前端来源：
- `pages/create/create.js:125-145`：`createTravel()`
- `pages/create/create.wxml`：组队标题、管理员昵称/头像、同行成员、活动日期、地点/备注、预收款、基金、权限开关
- 当前后端已有：`TravelViewSet.create`

优先级：P0
状态：已有后端基础能力，需扩展请求字段

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 是 | 组队标题。 |
| destination | string | 否 | 地点/备注，当前前端字段复用 `destination`。 |
| startDate | string | 否 | 活动日期，格式 `YYYY-MM-DD`。 |
| ownerName | string | 否 | 管理员昵称；未传时用当前用户昵称。 |
| ownerAvatarUrl | string | 否 | 管理员头像。 |
| members | array | 否 | 初始同行成员，允许无 openid 的临时成员。 |
| advanceAmount | string | 否 | 每只猫猫预收金额，当前页面已有字段但本地未保存。P1。 |
| catFund | string | 否 | 猫猫基金说明或金额，当前页面已有字段但本地未保存。P1。 |
| permissions | object | 否 | 协作权限。P1。 |

members item:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 同行猫猫昵称。 |
| openid | string | 否 | 被邀请人认领前可为空。 |
| avatarUrl | string | 否 | 成员头像。 |

permissions:

```json
{
  "allowMemberFamilyEdit": true,
  "allowInvitedIdentity": true,
  "requireAvatar": false
}
```

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "title": "海边晒太阳小分队",
    "destination": "周末去海边，顺路吃下午茶",
    "currency": "CNY",
    "startDate": "2026-06-18",
    "endDate": "",
    "status": "进行中",
    "inviteCode": "A1B2C3",
    "members": [
      {
        "id": 10,
        "openid": "openid-owner",
        "name": "你",
        "avatarUrl": "",
        "isOwner": true
      },
      {
        "id": 11,
        "openid": "",
        "name": "小路",
        "avatarUrl": "",
        "isOwner": false
      }
    ],
    "expenses": [],
    "summary": {
      "totalSpent": "0.00",
      "balances": [],
      "transfers": []
    }
  }
}
```

错误/空态：
- 400：`title` 为空，前端当前提示“请输入组队名称”。
- 400：成员昵称重复，前端当前提示“这只猫猫已在队伍里”。
- 401：未登录。

备注/问题：
- 当前后端 `TravelCreateSerializer` 要求 `owner_openid`，正式登录后应从 token 取当前用户，不应让前端传 owner_openid。
- 当前后端未支持一次创建初始成员，建议补齐，否则前端创建后还需要多次调用添加成员接口。
- 若保留高级规则，需要新增模型字段或独立配置表。

### 6.4 旅行详情

#### GET /api/travels/{travelId}

用途：旅行详情页、新增花销页、结算页都需要加载同一个旅行详情对象。

前端来源：
- `pages/logs/logs.js:112`：`store.getTravel(travelId)`
- `pages/expense/expense.js:23`：`store.getTravel(travelId)`
- `pages/settlement/settlement.js:13`：`store.getTravel(travelId)`
- 当前后端已有：`TravelViewSet.retrieve`

优先级：P0
状态：已有后端基础能力，需适配字段和权限

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "title": "杭州周末游",
    "destination": "杭州",
    "currency": "CNY",
    "startDate": "2026-06-18",
    "endDate": "",
    "status": "进行中",
    "inviteCode": "HK1234",
    "members": [
      {
        "id": 1,
        "openid": "demo-openid-local",
        "name": "你",
        "avatarUrl": "",
        "isOwner": true,
        "claimed": true
      }
    ],
    "expenses": [
      {
        "id": 1,
        "title": "晚餐",
        "category": "餐饮",
        "amount": "246.00",
        "payerId": 1,
        "payerName": "你",
        "note": "四人套餐",
        "paidAt": "2026-06-18T10:00:00Z",
        "shareWeights": [
          { "memberId": 1, "weight": 1 }
        ]
      }
    ],
    "summary": {
      "totalSpent": "246.00",
      "balances": [],
      "transfers": []
    }
  }
}
```

错误/空态：
- 404：旅行不存在，前端返回首页或提示“旅行不存在”。
- 403：当前用户不是成员，前端提示无权限。

备注/问题：
- 当前详情页有 fallback：没有 travelId 时展示第一条旅行。接后端后不建议保留该逻辑，避免误操作。

### 6.5 成员与邀请

#### POST /api/travels/{travelId}/members

用途：旅行详情页“管理”中添加同行猫猫。

前端来源：
- `pages/logs/logs.js:124-138`：`addMember()`
- `pages/logs/logs.wxml:77-80`：成员管理输入框和添加按钮
- 当前后端已有：`TravelViewSet.members`

优先级：P0
状态：已有后端基础能力，需支持临时成员和字段映射

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 成员昵称。 |
| openid | string | 否 | 若是已登录用户可传；临时成员为空。 |
| avatarUrl | string | 否 | 头像。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "travel": { "id": 1, "members": [] }
  }
}
```

错误/空态：
- 400：昵称为空，前端当前提示 `Member name is required`。
- 409：成员已存在，前端当前提示 `Member already exists`。
- 403：非管理员且无成员管理权限。

备注/问题：
- 当前后端 `MemberCreateSerializer` 字段为 `nickname`，建议统一前端使用的 `name` 或在接口层兼容。
- 当前后端 `get_or_create_user` 在 openid 为空时会生成 `temp_xxx` 用户；这能支持临时成员，但后续认领时需要合并/绑定。

#### POST /api/travels/join

用途：被邀请人通过邀请码加入旅行或认领临时身份。

前端来源：
- `pages/logs/logs.js:163-174`：当前“邀请同行”复制 `inviteCode`
- `项目整体情况说明.md`：邀请加入和多人协作还是骨架

优先级：P1
状态：需新增

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| inviteCode | string | 是 | 旅行邀请码。 |
| name | string | 否 | 新建身份时的昵称。 |
| claimMemberId | string/number | 否 | 认领已有临时成员时传。 |
| avatarUrl | string | 否 | 头像。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "travelId": 1,
    "memberId": 12,
    "joined": true,
    "claimed": true
  }
}
```

错误/空态：
- 404：邀请码无效。
- 409：当前用户已在该旅行中。
- 403：旅行关闭了 `allowInvitedIdentity` 且未选择可认领身份。

#### GET /api/travels/{travelId}/invite

用途：生成或返回邀请卡片信息。短期可只返回邀请码，后续可扩展小程序分享参数。

前端来源：
- `pages/logs/logs.js:168`：复制 `travel.inviteCode`

优先级：P2
状态：需新增，可暂缓

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "inviteCode": "HK1234",
    "sharePath": "/pages/index/index?inviteCode=HK1234",
    "title": "邀请你加入杭州周末游"
  }
}
```

### 6.6 新增花销

#### POST /api/travels/{travelId}/expenses

用途：记录一笔花销，包含付款人和参与分摊成员。

前端来源：
- `pages/expense/expense.js:76-106`：`saveExpense()`
- `pages/expense/expense.wxml`：标题、分类、金额、备注、付款人、参与分摊的人
- 当前后端已有：`TravelViewSet.expenses`

优先级：P0
状态：已有后端基础能力，需统一成员 ID / openid 字段

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 是 | 花销标题，例如“晚餐”。 |
| category | string | 否 | 分类，默认“其他”；前端默认“餐饮”。 |
| amount | string/number | 是 | 金额，必须大于 0。 |
| note | string | 否 | 备注。 |
| payerMemberId | string/number | 是 | 付款成员 ID；建议用 TravelMember.id。 |
| participantMemberIds | array | 否 | 参与分摊成员 ID；为空时默认全员。 |
| paidAt | string | 否 | 支付时间；默认服务端当前时间。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "travel": {
      "id": 1,
      "expenses": [],
      "summary": {
        "totalSpent": "246.00",
        "balances": [],
        "transfers": []
      }
    }
  }
}
```

错误/空态：
- 400：标题为空，前端当前对应 `Expense title is required`。
- 400：金额无效，前端当前对应 `Expense amount is invalid`。
- 400：付款人为空，前端当前对应 `Payer is required`。
- 404：旅行不存在。
- 403：当前用户不是成员或没有记账权限。

备注/问题：
- 当前后端请求字段是 `payer_openid`、`participant_openids`，但前端本地数据用 memberId。建议后端改为 `payer_member_id`、`participant_member_ids`，避免临时成员无 openid 时无法记账。
- 当前后端未保存 `paid_at`，模型有字段但 create 未赋值。建议支持。

#### GET /api/expense-categories

用途：提供花销分类。当前前端是自由输入，默认“餐饮”。

前端来源：
- `pages/expense/expense.js:9` 默认 `category: '餐饮'`

优先级：P2
状态：需新增，可暂缓

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": ["餐饮", "交通", "住宿", "门票", "购物", "其他"]
}
```

### 6.7 账单编辑 / 删除

#### PATCH /api/travels/{travelId}/expenses/{expenseId}

用途：编辑已有账单。当前页面显示“可编辑”，但点击只提示“编辑账单入口稍后补上”。

前端来源：
- `pages/logs/logs.wxml:99`：账单卡片 `bindtap="showExpenseEditHint"`
- `pages/logs/logs.js:175-177`：提示“编辑账单入口稍后补上”

优先级：P1
状态：需新增

Request body：同新增花销，字段均可选。

Response：返回更新后的 expense 或 travel。

#### DELETE /api/travels/{travelId}/expenses/{expenseId}

用途：删除误记账单。

优先级：P1
状态：需新增

错误/空态：
- 403：非创建者/管理员且无权限。
- 404：账单不存在。

### 6.8 结算

#### GET /api/travels/{travelId}/settlement

用途：结算页展示转账建议和成员净额。

前端来源：
- `pages/settlement/settlement.js:13`：当前从本地 travel.summary 读取
- `pages/settlement/settlement.wxml:15-24`：转账建议
- `pages/settlement/settlement.wxml:34-40`：成员净额
- 当前后端已有：`TravelViewSet.settlement`

优先级：P0
状态：已有后端能力，需字段映射

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "totalSpent": "374.00",
    "balances": [
      {
        "memberId": 1,
        "name": "你",
        "paid": "246.00",
        "owed": "124.67",
        "net": "121.33"
      }
    ],
    "transfers": [
      {
        "fromMemberId": 2,
        "fromName": "小路",
        "toMemberId": 1,
        "toName": "你",
        "amount": "121.33"
      }
    ]
  }
}
```

错误/空态：
- 无转账建议：前端显示“目前已经平账，不需要额外转账”。
- 404：旅行不存在。

备注/问题：
- 当前后端返回字段为 `total_spent`、`member_id`、`from_member_id` 等 snake_case。前端需要转换成 `totalSpent`、`memberId`、`fromMemberId`。

#### POST /api/travels/{travelId}/settle

用途：将旅行标记为已结清，设置结束日期。

前端来源：
- `pages/logs/logs.js:178-186`：`finishTravel()` 调用 `store.markTravelCompleted()`
- `pages/logs/logs.wxml:24`：点击“标记已结清”

优先级：P0
状态：需新增或用 `PATCH /api/travels/{id}` 实现

Request body:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| endDate | string | 否 | 结清日期，默认当天。 |

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "status": "已结清",
    "endDate": "2026-06-18"
  }
}
```

### 6.9 旅行状态、归档、删除

#### PATCH /api/travels/{travelId}

用途：更新旅行标题、地点、日期、状态、高级规则等。

前端来源：
- 创建页 PRD 提到详情和权限创建后可修改
- `pages/index/index.wxml:33-34` 有“归档/删除”视觉入口

优先级：P1
状态：需新增/扩展

Request body:

```json
{
  "title": "杭州周末游",
  "destination": "杭州",
  "startDate": "2026-06-18",
  "endDate": "2026-06-20",
  "status": "settled",
  "permissions": {
    "allowMemberFamilyEdit": true,
    "allowInvitedIdentity": true,
    "requireAvatar": false
  }
}
```

#### DELETE /api/travels/{travelId}

用途：首页删除旅行。

前端来源：
- `pages/index/index.wxml:34` 显示“删除”

优先级：P2
状态：需新增，当前未绑定事件

#### PATCH /api/travels/{travelId}/archive

用途：首页归档旅行。

前端来源：
- `pages/index/index.wxml:33` 显示“归档”

优先级：P2
状态：需新增，当前未绑定事件；也可先不做。

### 6.10 头像 / 文件上传

#### POST /api/uploads/avatar

用途：保存 `chooseAvatar` 得到的头像，返回可长期访问的 URL。

前端来源：
- `pages/create/create.wxml:52`：`open-type="chooseAvatar"`
- `pages/create/create.js:89-100`：`onChooseAvatar()` 保存 `avatarUrl`

优先级：P1
状态：需新增

Request:

```text
multipart/form-data
file: image
```

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "url": "https://example.com/media/avatar/xxx.png"
  }
}
```

备注/问题：
- 微信 `chooseAvatar` 返回可能是临时文件路径，正式使用需要 `wx.uploadFile` 上传到后端或对象存储。

### 6.11 猫猫家庭 / 预收款 / 猫猫基金

这些是页面已出现、但当前本地数据层未完整落库的高级功能。

#### GET /api/travels/{travelId}/families
#### POST /api/travels/{travelId}/families
#### PATCH /api/travels/{travelId}/families/{familyId}

用途：配置“猫猫家庭”，结算时按家庭合并转账。

前端来源：
- `pages/create/create.wxml:92-98`：猫猫家庭说明
- `pages/logs/logs.js:68` 当前 `familyCount` 写死为 1 或 0

优先级：P2
状态：需新增，当前暂无完整 UI

#### GET /api/travels/{travelId}/funds
#### POST /api/travels/{travelId}/funds

用途：记录每人预收款、猫猫基金，并影响最终结算。

前端来源：
- `pages/create/create.wxml:131-142`：预收金额、猫猫基金字段
- `pages/logs/logs.wxml:88-95`：预收/基金提示面板

优先级：P2
状态：需新增，当前可先用普通账单/备注代替

备注/问题：
- 若要影响结算算法，需要扩展 `compute_settlement()`，明确预收款是个人已付款，基金是公共抵扣还是公共收入。

## 7. 错误码和状态建议

| code/status | 场景 | 前端处理 |
|---|---|---|
| 0 / 200 | 成功 | 正常渲染或 toast 成功。 |
| 400 | 参数错误，如标题为空、金额无效 | 展示后端 message；保留表单输入。 |
| 401 | 未登录或 token 失效 | 重新调用 `wx.login`，必要时提示登录。 |
| 403 | 无权限，如非成员访问旅行 | toast 提示无权限，返回首页。 |
| 404 | 旅行/成员/账单不存在 | toast 提示不存在，返回上一页或首页。 |
| 409 | 重复成员、重复加入 | toast 提示冲突原因。 |
| 500 | 服务端异常 | toast 提示稍后重试。 |

## 8. 优先级建议

### P0：前后端打通必须做

1. `POST /api/auth/wechat-login`
2. `GET /api/travels`
3. `POST /api/travels`
4. `GET /api/travels/{travelId}`
5. `POST /api/travels/{travelId}/members`
6. `POST /api/travels/{travelId}/expenses`
7. `GET /api/travels/{travelId}/settlement`
8. `POST /api/travels/{travelId}/settle` 或 `PATCH /api/travels/{travelId}`

### P1：产品流程完整化

1. `GET /api/me`
2. `POST /api/uploads/avatar`
3. `POST /api/travels/join`
4. `PATCH /api/travels/{travelId}/expenses/{expenseId}`
5. `DELETE /api/travels/{travelId}/expenses/{expenseId}`
6. `PATCH /api/travels/{travelId}`

### P2：后续增强

1. 归档/删除旅行
2. 分类字典
3. 邀请卡片接口
4. 猫猫家庭
5. 预收款/猫猫基金台账
6. 成员认领高级权限

## 9. 前端接入建议

当前前端没有 request wrapper，建议新增：

```text
utils/request.js
utils/api.js 或 api/travels.js
```

第一阶段替换：

| 当前本地方法 | 建议 API |
|---|---|
| `store.getCurrentUser()` | `GET /api/me` 或登录后缓存 user |
| `store.listTravels()` | `GET /api/travels` |
| `store.getTravel(travelId)` | `GET /api/travels/{travelId}` |
| `store.createTravel(payload)` | `POST /api/travels` |
| `store.addMember(travelId, payload)` | `POST /api/travels/{travelId}/members` |
| `store.addExpense(travelId, payload)` | `POST /api/travels/{travelId}/expenses` |
| `store.markTravelCompleted(travelId)` | `POST /api/travels/{travelId}/settle` |
| `travel.summary` 本地计算 | `GET /api/travels/{travelId}/settlement` 或详情接口携带 summary |

建议保留 `travel-store.js` 作为 mock fallback，直到后端联调完成。

## 10. 当前后端需要调整点

1. 列表接口按当前用户过滤，不应返回全部旅行。
2. 创建旅行从登录态读取 owner，不应依赖前端传 `owner_openid`。
3. 创建旅行支持初始临时成员、头像、权限和高级字段。
4. 成员接口兼容前端 `name/avatarUrl` 字段。
5. 花销接口建议改用 `payerMemberId/participantMemberIds`，支持无 openid 的临时成员。
6. 结算接口字段转 camelCase，或前端统一转换。
7. 新增登录接口、request 鉴权、错误响应约定。
8. 可选：统一响应包裹 `{ code, message, data }`。

## 11. 待确认问题

1. 后端正式鉴权使用 JWT、DRF Token、session，还是小程序自定义 token？
2. API 响应是否统一包裹 `{ code, message, data }`？还是沿用 DRF 原生响应？
3. 前后端字段命名采用 camelCase 还是 snake_case？
4. 临时成员无 openid 时，后端是否允许记账和分摊？后续认领如何合并？
5. 预收款和猫猫基金是否必须进入第一期结算算法？
6. “猫猫家庭”是否第一期实现？按家庭合并转账的规则细节是什么？
7. 邀请加入是复制邀请码、分享小程序卡片，还是扫码加入？
8. 首页“归档/删除/查看全部”是否需要第一期做真实功能？
9. 账单编辑/删除是否第一期必须实现？
10. 数据库从 SQLite 切到 MySQL 的时间点和部署环境待确认。
