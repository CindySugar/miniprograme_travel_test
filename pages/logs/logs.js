const store = require('../../utils/travel-store.js')

const MEMBER_TONES = ['member-tone-coral', 'member-tone-blue', 'member-tone-mint', 'member-tone-gold']

const formatNumber = (value) => (`${value}`[1] ? `${value}` : `0${value}`)

const formatDateTime = (value) => {
  if (!value) {
    return '时间待补'
  }
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '时间待补'
  }
  return `${formatNumber(date.getMonth() + 1)}-${formatNumber(date.getDate())} ${formatNumber(date.getHours())}:${formatNumber(date.getMinutes())}`
}

const decorateMembers = (members = []) => {
  let toneIndex = 0
  return members.map((member) => {
    const toneClass = member.isOwner ? 'member-tone-owner' : MEMBER_TONES[toneIndex++ % MEMBER_TONES.length]
    const isPendingClaim = !member.openid
    return {
      ...member,
      badgeText: (member.name || '猫').slice(0, 1),
      toneClass,
      isPendingClaim,
      claimStatusText: isPendingClaim ? '待认领' : '已认领',
      identityText: member.isOwner
        ? '管理员'
        : isPendingClaim
          ? '临时身份未绑定微信号'
          : '微信号已绑定',
    }
  })
}

const decorateExpenses = (travel, memberLookup) => {
  return (travel.expenses || [])
    .map((expense) => {
      const payerBadge = memberLookup[expense.payerId] || {
        badgeText: '垫',
        toneClass: 'member-tone-owner',
        isOwner: false,
      }
      const participantBadges = (expense.shareWeights || [])
        .map((share) => memberLookup[share.memberId])
        .filter(Boolean)

      return {
        ...expense,
        payerBadge,
        participantBadges,
        amountFullDisplay: `¥${expense.amountDisplay}`,
        createdAtDisplay: `创建于：${formatDateTime(expense.paidAt || expense.createdAt)}`,
        editableText: '可编辑',
      }
    })
    .sort((a, b) => new Date(b.paidAt || 0) - new Date(a.paidAt || 0))
}

const buildTravelView = (travel, options = {}) => {
  const members = decorateMembers(travel.members || [])
  const memberLookup = Object.fromEntries(members.map((member) => [member.id, member]))
  const expenses = decorateExpenses(travel, memberLookup)
  const owner = members.find((member) => member.isOwner) || members[0] || { name: '未设置' }
  const pendingClaimCount = members.filter((member) => member.isPendingClaim).length
  const familyCount = members.length ? 1 : 0
  const showAllExpenses = !!options.showAllExpenses

  return {
    ...travel,
    displayDateLabel: travel.displayDate || '未设置日期',
    statusToneClass: travel.status === '已结清' ? 'status-settled' : 'status-active',
    summaryLabel: travel.status === '已结清' ? '总花费' : '待分摊',
    totalSpentFullDisplay: `¥${travel.summary.totalSpentDisplay}`,
    expenseCountDisplay: `${travel.expenseCount} 笔账单`,
    memberSummaryDisplay: familyCount
      ? `${travel.memberCount}只猫猫 · ${familyCount}个家庭`
      : `${travel.memberCount}只猫猫`,
    claimSummaryDisplay: pendingClaimCount
      ? `${pendingClaimCount}位待认领 · 管理员：${owner.name}`
      : `已全部认领 · 管理员：${owner.name}`,
    pendingClaimHelp: pendingClaimCount
      ? '待认领表示临时成员还没有绑定微信号。'
      : '当前同行成员都已经绑定微信号。',
    bookActionText: showAllExpenses && expenses.length > 2 ? '收起账本' : '查看账本',
    hasMoreExpenses: expenses.length > 2,
    membersDecorated: members,
    visibleExpenses: showAllExpenses ? expenses : expenses.slice(0, 2),
  }
}

Page({
  data: {
    travelId: '',
    travel: null,
    memberName: '',
    showMemberManager: false,
    showAllExpenses: false,
    showFundPanel: false,
  },
  onLoad(query) {
    this.setData({
      travelId: query.travelId || '',
    })
  },
  onShow() {
    this.refresh()
  },
  refresh() {
    const rawTravel = store.getTravel(this.data.travelId) || store.listTravels()[0] || null
    if (!rawTravel) {
      return
    }
    this.setData({
      travelId: rawTravel.id,
      travel: buildTravelView(rawTravel, { showAllExpenses: this.data.showAllExpenses }),
    })
  },
  onMemberInput(e) {
    this.setData({ memberName: e.detail.value })
  },
  addMember() {
    const { travel, memberName } = this.data
    if (!travel) {
      wx.showToast({ title: '请先创建旅行', icon: 'none' })
      return
    }
    try {
      store.addMember(travel.id, { name: memberName })
      this.setData({ memberName: '' })
      this.refresh()
      wx.showToast({ title: '成员已添加', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },
  toggleMemberManager() {
    this.setData({
      showMemberManager: !this.data.showMemberManager,
    })
  },
  toggleExpenseBook() {
    if (!this.data.travel) {
      return
    }
    if (!this.data.travel.hasMoreExpenses && !this.data.showAllExpenses) {
      wx.showToast({ title: '当前已展示全部账单', icon: 'none' })
      return
    }
    this.setData({
      showAllExpenses: !this.data.showAllExpenses,
    }, () => {
      this.refresh()
    })
  },
  toggleFundPanel() {
    this.setData({
      showFundPanel: !this.data.showFundPanel,
    })
  },
  inviteMembers() {
    const { travel } = this.data
    if (!travel) {
      return
    }
    wx.setClipboardData({
      data: travel.inviteCode,
      success: () => {
        wx.showToast({ title: '邀请码已复制', icon: 'none' })
      },
    })
  },
  gotoMemberManage() {
    const { travel } = this.data
    if (!travel) {
      return
    }
    wx.navigateTo({
      url: `/pages/member-manage/member-manage?travelId=${travel.id}`,
    })
  },
  showExpenseEditHint() {
    wx.showToast({ title: '编辑账单入口稍后补上', icon: 'none' })
  },
  finishTravel() {
    const { travel } = this.data
    if (!travel) {
      return
    }
    store.markTravelCompleted(travel.id)
    wx.showToast({ title: '已结清', icon: 'success' })
    this.refresh()
  },
  gotoSettlement() {
    const { travel } = this.data
    if (!travel) {
      return
    }
    wx.navigateTo({
      url: `/pages/settlement/settlement?travelId=${travel.id}`,
    })
  },
  gotoExpense() {
    const { travel } = this.data
    if (!travel) {
      return
    }
    wx.navigateTo({
      url: `/pages/expense/expense?travelId=${travel.id}`,
    })
  },
})
