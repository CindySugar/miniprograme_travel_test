const store = require('../../utils/travel-store.js')

Page({
  data: {
    travelId: '',
    travel: null,
    memberName: '',
    expenseForm: {
      title: '',
      category: '餐饮',
      amount: '',
      note: '',
      payerId: '',
      participantIds: [],
    },
  },
  onLoad(query) {
    const travelId = query.travelId || ''
    this.setData({ travelId })
  },
  onShow() {
    this.refresh()
  },
  refresh() {
    const travel = store.getTravel(this.data.travelId) || store.listTravels()[0] || null
    if (!travel) {
      return
    }
    const payerId = this.data.expenseForm.payerId || travel.members[0]?.id || ''
    const participantIds = this.data.expenseForm.participantIds.length
      ? this.data.expenseForm.participantIds
      : travel.members.map((member) => member.id)

    const payerName = travel.members.find((member) => member.id === payerId)?.name || travel.members[0]?.name || ''
    const memberPills = travel.members.map((member) => ({
      ...member,
      selected: participantIds.includes(member.id),
    }))

    this.setData({
      travel,
      'travel.memberNames': travel.memberNames,
      'travel.payerName': payerName,
      'travel.memberPills': memberPills,
      'expenseForm.payerId': payerId,
      'expenseForm.participantIds': participantIds,
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
  onExpenseInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`expenseForm.${field}`]: e.detail.value,
    })
  },
  onPayerChange(e) {
    const payerId = this.data.travel.members[Number(e.detail.value)]?.id || ''
    const payerName = this.data.travel.members.find((member) => member.id === payerId)?.name || ''
    this.setData({
      'expenseForm.payerId': payerId,
      'travel.payerName': payerName,
    })
  },
  toggleParticipant(e) {
    const memberId = e.currentTarget.dataset.id
    const participantIds = new Set(this.data.expenseForm.participantIds)
    if (participantIds.has(memberId)) {
      participantIds.delete(memberId)
    } else {
      participantIds.add(memberId)
    }
    const memberPills = this.data.travel.members.map((member) => ({
      ...member,
      selected: participantIds.has(member.id),
    }))
    this.setData({
      'expenseForm.participantIds': Array.from(participantIds),
      'travel.memberPills': memberPills,
    })
  },
  addExpense() {
    const { travel, expenseForm } = this.data
    if (!travel) {
      wx.showToast({ title: '请先创建旅行', icon: 'none' })
      return
    }

    try {
      store.addExpense(travel.id, {
        title: expenseForm.title,
        category: expenseForm.category,
        amount: expenseForm.amount,
        note: expenseForm.note,
        payerId: expenseForm.payerId,
        participantIds: expenseForm.participantIds,
      })
      this.setData({
        expenseForm: {
          title: '',
          category: '餐饮',
          amount: '',
          note: '',
          payerId: this.data.travel.members[0]?.id || '',
          participantIds: this.data.travel.members.map((member) => member.id),
        },
      })
      this.refresh()
      wx.showToast({ title: '花销已记录', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' })
    }
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
