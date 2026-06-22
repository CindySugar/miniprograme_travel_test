import { formatDate, formatMoney, todayISO } from './util.js'

const SESSION_KEY = 'travel_aa_session_v1'
const LOGIN_CODE_KEY = 'travel_aa_login_code'
const DEFAULT_API_PREFIX = 'http://127.0.0.1:8000/api'

const defaultCurrentUser = {
  openid: '',
  name: '我',
  avatarUrl: '',
}

const memberBadgeClasses = ['member-badge-green', 'member-badge-coral', 'member-badge-blue', 'member-badge-mint']
const memberToneClasses = ['member-tone-coral', 'member-tone-blue', 'member-tone-mint', 'member-tone-gold']
const isH5Runtime = typeof window !== 'undefined' && typeof document !== 'undefined'

const API_PREFIX = (() => {
  const envBase = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.VITE_API_BASE_URL : ''
  if (envBase) {
    return envBase.replace(/\/$/, '')
  }
  return (isH5Runtime ? '/api' : DEFAULT_API_PREFIX).replace(/\/$/, '')
})()

const isObject = (value) => value !== null && typeof value === 'object'
const clone = (value) => JSON.parse(JSON.stringify(value))

const createApiError = (message, statusCode = 0, body = null) => {
  const error = new Error(message || '请求失败')
  error.statusCode = statusCode
  error.body = body
  return error
}

const toMessage = (value) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map(toMessage).filter(Boolean).join('，')
  }
  if (isObject(value)) {
    return Object.values(value).map(toMessage).filter(Boolean).join('，')
  }
  return '请求失败'
}

const buildQuery = (params = {}) => {
  const parts = []
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
  })
  return parts.length ? `?${parts.join('&')}` : ''
}

const resolveUrl = (path) => {
  if (/^https?:\/\//.test(path)) return path
  const cleanPath = `${path}`.replace(/^\/+/, '')
  return `${API_PREFIX}/${cleanPath}`
}

let cachedSession = null
let sessionPromise = null

const normalizeSession = (value) => {
  const session = isObject(value) ? value : {}
  const wechat = isObject(session.wechat) ? session.wechat : null
  const currentUser = isObject(session.currentUser) ? session.currentUser : {}
  return {
    token: typeof session.token === 'string' ? session.token : '',
    wechat,
    currentUser: {
      ...defaultCurrentUser,
      ...currentUser,
      openid: currentUser.openid || wechat?.openid || '',
    },
  }
}

const loadSession = () => {
  if (cachedSession) return cachedSession
  cachedSession = normalizeSession(uni.getStorageSync(SESSION_KEY))
  return cachedSession
}

const saveSession = (session) => {
  cachedSession = normalizeSession(session)
  uni.setStorageSync(SESSION_KEY, cachedSession)
  return cachedSession
}

const clearSession = () => {
  cachedSession = null
  uni.removeStorageSync(SESSION_KEY)
}

const loadLoginCode = () => {
  const stored = uni.getStorageSync(LOGIN_CODE_KEY)
  return typeof stored === 'string' ? stored : ''
}

const saveLoginCode = (code) => {
  if (code) {
    uni.setStorageSync(LOGIN_CODE_KEY, code)
  }
}

const getLoginCode = async () => {
  if (typeof uni.login === 'function') {
    try {
      const result = await new Promise((resolve, reject) => {
        uni.login({
          provider: 'weixin',
          success: resolve,
          fail: reject,
        })
      })
      if (result?.code) {
        return result.code
      }
    } catch {
      // fallback below
    }
  }
  const stored = loadLoginCode()
  if (stored) {
    return stored
  }
  // ponytail: stable local login code keeps the backend dev fallback identity persistent across reloads.
  const code = 'dev-local-code'
  saveLoginCode(code)
  return code
}

const normalizeSummary = (travel, summary = {}) => {
  const balances = Array.isArray(summary.balances) ? summary.balances : []
  const transfers = Array.isArray(summary.transfers) ? summary.transfers : []
  const memberLookup = Object.fromEntries((travel.members || []).map((member) => [member.id, member]))

  return {
    ...summary,
    totalSpent: summary.totalSpent ?? '0.00',
    totalSpentDisplay: formatMoney(summary.totalSpent ?? 0),
    balances: balances.map((item) => ({
      ...item,
      paidDisplay: formatMoney(item.paid ?? 0),
      owedDisplay: formatMoney(item.owed ?? 0),
      netDisplay: formatMoney(item.net ?? 0),
      netClass: Number(item.net) < -0.005 ? 'amount-negative' : Number(item.net) > 0.005 ? 'amount-positive' : '',
    })),
    transfers: transfers.map((item) => ({
      ...item,
      amountDisplay: formatMoney(item.amount ?? 0),
    })),
    balanceLookup: Object.fromEntries(balances.map((item) => [item.memberId, item])),
    memberLookup,
    participantLookup: Object.fromEntries((travel.members || []).map((member) => [member.id, member.name])),
  }
}

const normalizeMember = (member) => ({
  ...member,
  id: member.id,
  userId: member.userId,
  name: member.name || member.user?.nickname || '',
  avatarUrl: member.avatarUrl || member.user?.avatarUrl || '',
  isOwner: !!member.isOwner,
  claimed: !!member.claimed,
  openid: member.claimed ? 'bound' : '',
  canBookkeep: member.canBookkeep !== false,
  status: member.user?.status || 'enabled',
})

const normalizeExpense = (expense) => {
  const participantShares = Array.isArray(expense.participantShares) ? expense.participantShares : []
  const participants = Array.isArray(expense.participants) ? expense.participants : []
  return {
    ...expense,
    id: expense.id,
    expenseId: expense.expenseId || expense.id,
    title: expense.title || '',
    category: expense.category || '其他',
    amount: expense.amount ?? '0.00',
    amountDisplay: formatMoney(expense.amount ?? 0),
    payerId: expense.payerMemberId,
    payerMemberId: expense.payerMemberId,
    payerName: expense.payerName || '',
    payerAvatarUrl: expense.payerAvatarUrl || '',
    splitType: expense.splitType || 'equal',
    participants: participants.map((item) => ({
      memberId: item.memberId,
      name: item.name,
      avatarUrl: item.avatarUrl || '',
    })),
    participantShares: participantShares.map((item) => ({
      memberId: item.memberId,
      name: item.name,
      shareAmount: item.shareAmount ?? '0.00',
    })),
    shareWeights: participantShares.map((item) => ({
      memberId: item.memberId,
      weight: 1,
      shareAmount: item.shareAmount ?? '0.00',
    })),
    note: expense.note || '',
    paidAt: expense.paidAt || expense.createdAt || '',
    createdAt: expense.createdAt || expense.paidAt || '',
    editable: expense.editable !== false,
  }
}

const normalizeTravel = (travel) => {
  const members = Array.isArray(travel.members) ? travel.members.map(normalizeMember) : []
  const expenses = Array.isArray(travel.expenses) ? travel.expenses.map(normalizeExpense) : []
  const base = clone(travel)
  const settings = {
    allowInvite: true,
    allowMemberFamilyEdit: true,
    allowInvitedIdentity: true,
    requireAvatar: false,
    ...(travel.settings || {}),
  }

  return {
    ...base,
    members,
    expenses,
    settings,
    summary: normalizeSummary({ members }, travel.summary || {}),
    memberCount: travel.memberCount ?? members.length,
    expenseCount: travel.expenseCount ?? expenses.length,
    memberNames: members.map((member) => member.name),
    visibleMembers: members.slice(0, 4).map((member, index) => ({
      ...member,
      badgeClass: memberBadgeClasses[index % memberBadgeClasses.length],
      initial: index === 0 ? '' : (member.name || '猫').slice(0, 1),
    })),
    updatedAtDisplay: travel.updatedAt ? travel.updatedAt.slice(0, 10) : (travel.createdAt || '').slice(0, 10),
    displayDate: travel.endDate || formatDate(travel.startDate || travel.createdAt || todayISO()),
  }
}

const parseResponseBody = (res) => {
  const rawBody = typeof res.data === 'string'
    ? (() => {
        try {
          return JSON.parse(res.data)
        } catch {
          return res.data
        }
      })()
    : res.data
  const body = isObject(rawBody) ? rawBody : {}

  if (res.statusCode < 200 || res.statusCode >= 300) {
    throw createApiError(toMessage(body.message ?? body.detail ?? rawBody), res.statusCode, body)
  }
  if (isObject(body) && typeof body.code === 'number' && body.code !== 0) {
    throw createApiError(toMessage(body.message), res.statusCode, body)
  }
  return isObject(body) && 'data' in body ? body.data : rawBody
}

const requestOnce = (path, { method = 'GET', data, headers = {}, skipAuth = false } = {}) => new Promise((resolve, reject) => {
  const session = loadSession()
  const header = {
    'content-type': 'application/json',
    ...headers,
  }

  if (!skipAuth) {
    if (!session.token) {
      reject(createApiError('未登录', 401))
      return
    }
    header.Authorization = `Bearer ${session.token}`
  }

  uni.request({
    url: resolveUrl(path),
    method,
    data,
    header,
    success(res) {
      try {
        resolve(parseResponseBody(res))
      } catch (error) {
        reject(error)
      }
    },
    fail(err) {
      reject(createApiError(err.errMsg || '网络请求失败'))
    },
  })
})

const request = async (path, options = {}) => {
  if (!options.skipAuth) {
    await ensureSession()
  }

  try {
    return await requestOnce(path, options)
  } catch (error) {
    if (!options.skipAuth && error.statusCode === 401) {
      clearSession()
      await ensureSession()
      return requestOnce(path, options)
    }
    throw error
  }
}

const ensureSession = async () => {
  const session = loadSession()
  if (session.token) {
    return session
  }
  if (sessionPromise) {
    return sessionPromise
  }

  sessionPromise = (async () => {
    const code = await getLoginCode()
    const payload = await requestOnce('auth/wechat-login', {
      method: 'POST',
      data: { code },
      skipAuth: true,
    })
    return saveSession({
      token: payload.token,
      wechat: payload.wechat,
      currentUser: {
        ...defaultCurrentUser,
        openid: payload.wechat?.openid || '',
      },
    })
  })().finally(() => {
    sessionPromise = null
  })

  return sessionPromise
}

const getCurrentUser = () => {
  const session = loadSession()
  if (!session.token && !sessionPromise) {
    void ensureSession()
  }
  return session.currentUser
}

const uploadAvatar = async (filePath) => {
  if (!filePath) {
    throw new Error('请选择头像')
  }
  const session = loadSession()

  const payload = await new Promise((resolve, reject) => {
    uni.uploadFile({
      url: resolveUrl('uploads/avatar'),
      filePath,
      name: 'file',
      header: session.token ? { Authorization: `Bearer ${session.token}` } : {},
      formData: {},
      success(res) {
        const body = typeof res.data === 'string'
          ? (() => {
              try {
                return JSON.parse(res.data)
              } catch {
                return res.data
              }
            })()
          : res.data
        const data = isObject(body) && 'data' in body ? body.data : body
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(createApiError(toMessage(body?.message ?? body?.detail ?? body), res.statusCode, body))
          return
        }
        if (isObject(body) && typeof body.code === 'number' && body.code !== 0) {
          reject(createApiError(toMessage(body.message), res.statusCode, body))
          return
        }
        resolve(data)
      },
      fail(err) {
        reject(createApiError(err.errMsg || '上传失败'))
      },
    })
  })

  return payload?.url || payload?.avatarUrl || ''
}

const listTravels = async (params = {}) => {
  const payload = await request(`travels${buildQuery(params)}`)
  const list = Array.isArray(payload?.list) ? payload.list : []
  return list.map(normalizeTravel)
}

const getTravel = async (travelId) => normalizeTravel(await request(`travels/${travelId}`))

const getSettlement = async (travelId) => {
  const travel = await getTravel(travelId)
  const summary = await request(`travels/${travelId}/settlement`)
  return {
    ...travel,
    summary: normalizeSummary(travel, summary || {}),
  }
}

const getSettlementDetail = async (travelId) => {
  const travel = await getTravel(travelId)
  const detail = await request(`travels/${travelId}/settlement/detail`)
  return {
    ...travel,
    settlementDetail: detail,
  }
}

const getInviteDetail = async (inviteCode) => request(`invites/${inviteCode}`, { skipAuth: true })

const joinTravel = async (payload) => normalizeTravel(await request('travels/join', {
  method: 'POST',
  data: payload,
}))

const createTravel = async (payload) => normalizeTravel(await request('travels', {
  method: 'POST',
  data: payload,
}))

const updateTravel = async (travelId, payload) => normalizeTravel(await request(`travels/${travelId}`, {
  method: 'PATCH',
  data: payload,
}))

const getMe = async (travelId) => request(`travels/${travelId}/me`)

const updateMe = async (travelId, payload) => request(`travels/${travelId}/me`, {
  method: 'PATCH',
  data: payload,
})

const bindTravelUser = async (travelId, userId) => request(`travels/${travelId}/binding`, {
  method: 'POST',
  data: { userId },
})

const unbindTravelUser = async (travelId) => request(`travels/${travelId}/binding`, {
  method: 'DELETE',
})

const addMember = async (travelId, payload) => normalizeTravel(await request(`travels/${travelId}/members`, {
  method: 'POST',
  data: payload,
}))

const updateMember = async (travelId, memberId, payload) => request(`travels/${travelId}/members/${memberId}`, {
  method: 'PATCH',
  data: payload,
})

const removeMember = async (travelId, memberId) => normalizeTravel(await request(`travels/${travelId}/members/${memberId}`, {
  method: 'DELETE',
}))

const clearMemberClaim = async (travelId, memberId) => normalizeTravel(await request(`travels/${travelId}/members/${memberId}/clear-claim`, {
  method: 'POST',
}))

const addExpense = async (travelId, payload) => request(`travels/${travelId}/expenses`, {
  method: 'POST',
  data: payload,
})

const markTravelCompleted = async (travelId, endDate = todayISO()) => normalizeTravel(await request(`travels/${travelId}/settle`, {
  method: 'POST',
  data: { endDate },
}))

export {
  addExpense,
  addMember,
  bindTravelUser,
  clearMemberClaim,
  createTravel,
  ensureSession,
  getCurrentUser,
  getInviteDetail,
  getMe,
  getSettlement,
  getSettlementDetail,
  getTravel,
  joinTravel,
  listTravels,
  markTravelCompleted,
  removeMember,
  unbindTravelUser,
  updateMember,
  updateMe,
  updateTravel,
  uploadAvatar,
}
