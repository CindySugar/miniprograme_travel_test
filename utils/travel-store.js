const { formatDate, formatMoney, roundMoney, todayISO } = require('./util.js')

const STORAGE_KEY = 'travel_aa_state_v1'

const demoState = {
  currentUser: {
    openid: 'demo-openid-local',
    name: '你',
    avatarUrl: '',
  },
  travels: [
    {
      id: 'travel_demo_hangzhou',
      title: '杭州周末游',
      destination: '杭州',
      currency: 'CNY',
      startDate: todayISO(),
      endDate: '',
      status: '进行中',
      inviteCode: 'HK1234',
      createdAt: new Date().toISOString(),
      members: [
        { id: 'member_me', openid: 'demo-openid-local', name: '你', avatarUrl: '', isOwner: true },
        { id: 'member_lu', openid: 'demo-lu', name: '小路', avatarUrl: '', isOwner: false },
        { id: 'member_qi', openid: 'demo-qi', name: '琪琪', avatarUrl: '', isOwner: false },
      ],
      expenses: [
        {
          id: 'expense_1',
          title: '机场接机',
          category: '交通',
          amount: 128,
          payerId: 'member_lu',
          note: '高峰打车',
          paidAt: new Date().toISOString(),
          shareWeights: [
            { memberId: 'member_me', weight: 1 },
            { memberId: 'member_lu', weight: 1 },
            { memberId: 'member_qi', weight: 1 },
          ],
        },
        {
          id: 'expense_2',
          title: '晚餐',
          category: '餐饮',
          amount: 246,
          payerId: 'member_me',
          note: '四人套餐',
          paidAt: new Date().toISOString(),
          shareWeights: [
            { memberId: 'member_me', weight: 1 },
            { memberId: 'member_lu', weight: 1 },
            { memberId: 'member_qi', weight: 1 },
          ],
        },
      ],
    },
  ],
}

const clone = (value) => JSON.parse(JSON.stringify(value))

const loadState = () => {
  const stored = wx.getStorageSync(STORAGE_KEY)
  if (!stored) {
    saveState(clone(demoState))
    return clone(demoState)
  }
  return {
    ...clone(demoState),
    ...stored,
    currentUser: {
      ...demoState.currentUser,
      ...(stored.currentUser || {}),
    },
    travels: Array.isArray(stored.travels) && stored.travels.length ? stored.travels : clone(demoState.travels),
  }
}

const saveState = (state) => {
  wx.setStorageSync(STORAGE_KEY, state)
}

const ensureState = () => {
  const state = loadState()
  if (!state.travels.length) {
    saveState(clone(demoState))
    return clone(demoState)
  }
  return state
}

const currentState = () => ensureState()

const getCurrentUser = () => currentState().currentUser

const listTravels = () => {
  const state = currentState()
  return state.travels
    .slice()
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .map((travel) => enrichTravel(travel))
}

const getTravel = (travelId) => {
  const state = currentState()
  const travel = state.travels.find((item) => item.id === travelId)
  return travel ? enrichTravel(travel) : null
}

const createId = (prefix) => `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`

const createTravel = (payload) => {
  const state = currentState()
  const currentUser = state.currentUser
  const title = (payload.title || '').trim() || '未命名旅行'
  const ownerName = (payload.ownerName || currentUser.name || '我').trim()
  const members = [
    {
      id: createId('member'),
      openid: currentUser.openid,
      name: ownerName,
      avatarUrl: payload.ownerAvatarUrl || currentUser.avatarUrl || '',
      isOwner: true,
    },
  ]

  const extraMembers = Array.isArray(payload.members) ? payload.members : []
  extraMembers.forEach((member) => {
    const name = (member.name || '').trim()
    if (!name || members.some((item) => item.name === name)) {
      return
    }
    members.push({
      id: createId('member'),
      openid: member.openid || '',
      name,
      avatarUrl: member.avatarUrl || '',
      isOwner: false,
    })
  })

  const travel = {
    id: createId('travel'),
    title,
    destination: (payload.destination || '').trim(),
    currency: payload.currency || 'CNY',
    startDate: payload.startDate || todayISO(),
    endDate: payload.endDate || '',
    status: '进行中',
    inviteCode: payload.inviteCode || createId('invite').slice(-6).toUpperCase(),
    createdAt: new Date().toISOString(),
    members,
    expenses: [],
  }

  state.travels.unshift(travel)
  saveState(state)
  return enrichTravel(travel)
}

const addMember = (travelId, payload) => {
  const state = currentState()
  const travel = state.travels.find((item) => item.id === travelId)
  if (!travel) {
    throw new Error('Travel not found')
  }

  const name = (payload.name || '').trim()
  if (!name) {
    throw new Error('Member name is required')
  }

  const exists = travel.members.some((member) => member.name === name)
  if (exists) {
    throw new Error('Member already exists')
  }

  travel.members.push({
    id: createId('member'),
    openid: payload.openid || '',
    name,
    avatarUrl: payload.avatarUrl || '',
    isOwner: false,
  })
  saveState(state)
  return enrichTravel(travel)
}

const addExpense = (travelId, payload) => {
  const state = currentState()
  const travel = state.travels.find((item) => item.id === travelId)
  if (!travel) {
    throw new Error('Travel not found')
  }

  const title = (payload.title || '').trim()
  const amount = roundMoney(payload.amount)
  const payerId = payload.payerId || travel.members[0]?.id
  if (!title) {
    throw new Error('Expense title is required')
  }
  if (!amount || Number.isNaN(Number(amount)) || amount <= 0) {
    throw new Error('Expense amount is invalid')
  }
  if (!payerId) {
    throw new Error('Payer is required')
  }

  const participantIds = Array.isArray(payload.participantIds) && payload.participantIds.length
    ? payload.participantIds
    : travel.members.map((member) => member.id)

  const shareWeights = participantIds.map((memberId) => ({
    memberId,
    weight: 1,
  }))

  travel.expenses.unshift({
    id: createId('expense'),
    title,
    category: (payload.category || '其他').trim(),
    amount,
    payerId,
    note: (payload.note || '').trim(),
    paidAt: payload.paidAt || new Date().toISOString(),
    shareWeights,
  })

  saveState(state)
  return enrichTravel(travel)
}

const computeTravelSummary = (travel) => {
  const balances = travel.members.map((member) => ({
    memberId: member.id,
    name: member.name,
    paid: 0,
    owed: 0,
    net: 0,
  }))
  const balanceMap = new Map(balances.map((item) => [item.memberId, item]))

  travel.expenses.forEach((expense) => {
    const payer = balanceMap.get(expense.payerId)
    if (payer) {
      payer.paid = roundMoney(payer.paid + Number(expense.amount))
    }

    const shares = Array.isArray(expense.shareWeights) && expense.shareWeights.length
      ? expense.shareWeights
      : travel.members.map((member) => ({ memberId: member.id, weight: 1 }))
    const totalWeight = shares.reduce((sum, item) => sum + Number(item.weight || 1), 0)
    let distributed = 0
    shares.forEach((share, index) => {
      const memberBalance = balanceMap.get(share.memberId)
      if (!memberBalance) {
        return
      }
      const amount = index === shares.length - 1
        ? roundMoney(Number(expense.amount) - distributed)
        : roundMoney((Number(expense.amount) * Number(share.weight || 1)) / totalWeight)
      distributed = roundMoney(distributed + amount)
      memberBalance.owed = roundMoney(memberBalance.owed + amount)
    })
  })

  balances.forEach((item) => {
    item.net = roundMoney(item.paid - item.owed)
  })

  return {
    totalSpent: roundMoney(travel.expenses.reduce((sum, expense) => sum + Number(expense.amount), 0)),
    balances,
    transfers: buildTransfers(balances),
  }
}

const decorateSummary = (travel, summary) => {
  return {
    ...summary,
    totalSpentDisplay: formatMoney(summary.totalSpent),
    balances: summary.balances.map((item) => ({
      ...item,
      paidDisplay: formatMoney(item.paid),
      owedDisplay: formatMoney(item.owed),
      netDisplay: formatMoney(item.net),
      netClass: item.net < -0.005 ? 'amount-negative' : item.net > 0.005 ? 'amount-positive' : '',
    })),
    transfers: summary.transfers.map((item) => ({
      ...item,
      amountDisplay: formatMoney(item.amount),
    })),
    balanceLookup: Object.fromEntries(summary.balances.map((item) => [item.memberId, item])),
    memberLookup: Object.fromEntries(
      travel.members.map((member) => [member.id, member])
    ),
    participantLookup: Object.fromEntries(
      travel.members.map((member) => [member.id, member.name])
    ),
  }
}

const buildTransfers = (balances) => {
  const creditors = balances
    .filter((item) => item.net > 0.005)
    .map((item) => ({ ...item }))
    .sort((a, b) => b.net - a.net)
  const debtors = balances
    .filter((item) => item.net < -0.005)
    .map((item) => ({ ...item }))
    .sort((a, b) => a.net - b.net)

  const transfers = []
  let debtorIndex = 0
  let creditorIndex = 0

  while (debtorIndex < debtors.length && creditorIndex < creditors.length) {
    const debtor = debtors[debtorIndex]
    const creditor = creditors[creditorIndex]
    const amount = roundMoney(Math.min(-debtor.net, creditor.net))
    if (amount <= 0) {
      break
    }

    transfers.push({
      fromMemberId: debtor.memberId,
      fromName: debtor.name,
      toMemberId: creditor.memberId,
      toName: creditor.name,
      amount,
    })

    debtor.net = roundMoney(debtor.net + amount)
    creditor.net = roundMoney(creditor.net - amount)

    if (Math.abs(debtor.net) < 0.005) {
      debtorIndex += 1
    }
    if (Math.abs(creditor.net) < 0.005) {
      creditorIndex += 1
    }
  }

  return transfers
}

const enrichTravel = (travel) => {
  const summary = decorateSummary(travel, computeTravelSummary(travel))
  const expenses = travel.expenses.map((expense) => ({
    ...expense,
    amountDisplay: formatMoney(expense.amount),
    payerName: summary.participantLookup[expense.payerId] || '未知',
    participantNames: (expense.shareWeights || [])
      .map((share) => summary.participantLookup[share.memberId])
      .filter(Boolean)
      .join('、'),
  }))
  return {
    ...clone(travel),
    expenses,
    summary,
    expenseCount: travel.expenses.length,
    memberCount: travel.members.length,
    memberNames: travel.members.map((member) => member.name),
    displayDate: travel.endDate || formatDate(travel.startDate || travel.createdAt),
  }
}

const markTravelCompleted = (travelId) => {
  const state = currentState()
  const travel = state.travels.find((item) => item.id === travelId)
  if (!travel) {
    throw new Error('Travel not found')
  }
  travel.status = '已结清'
  travel.endDate = travel.endDate || todayISO()
  saveState(state)
  return enrichTravel(travel)
}

module.exports = {
  addExpense,
  addMember,
  createTravel,
  currentState,
  ensureState,
  getCurrentUser,
  getTravel,
  listTravels,
  markTravelCompleted,
  computeTravelSummary,
  decorateSummary,
}
