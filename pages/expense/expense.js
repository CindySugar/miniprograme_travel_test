const store = require('../../utils/travel-store.js')

Page({
  data: {
    travelId: '',
    travel: null,
    form: {
      title: '',
      category: '餐饮',
      amount: '',
      note: '',
      payerId: '',
      participantIds: [],
    },
  },
  onLoad(query) {
    this.setData({ travelId: query.travelId || '' })
  },
  onShow() {
    this.refresh()
  },
  refresh() {
    const travel = store.getTravel(this.data.travelId) || null
    if (!travel) {
      return
    }
    const payerId = this.data.form.payerId || travel.members[0]?.id || ''
    const payerName = travel.members.find((member) => member.id === payerId)?.name || travel.members[0]?.name || ''
    this.setData({
      travel,
      'travel.memberNames': travel.memberNames,
      'travel.payerName': payerName,
      'travel.memberPills': travel.members.map((member) => ({
        ...member,
        selected: this.data.form.participantIds.length
          ? this.data.form.participantIds.includes(member.id)
          : true,
      })),
      'form.payerId': payerId,
      'form.participantIds': this.data.form.participantIds.length
        ? this.data.form.participantIds
        : travel.members.map((member) => member.id),
    })
  },
  onInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [`form.${field}`]: e.detail.value,
    })
  },
  onPayerChange(e) {
    const payerId = this.data.travel.members[Number(e.detail.value)]?.id || ''
    const payerName = this.data.travel.members.find((member) => member.id === payerId)?.name || ''
    this.setData({
      'form.payerId': payerId,
      'travel.payerName': payerName,
    })
  },
  toggleParticipant(e) {
    const memberId = e.currentTarget.dataset.id
    const participantIds = new Set(this.data.form.participantIds)
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
      'form.participantIds': Array.from(participantIds),
      'travel.memberPills': memberPills,
    })
  },
  saveExpense() {
    const { travel, form } = this.data
    if (!travel) {
      wx.showToast({ title: '请先创建旅行', icon: 'none' })
      return
    }
    try {
      store.addExpense(travel.id, {
        title: form.title,
        category: form.category,
        amount: form.amount,
        note: form.note,
        payerId: form.payerId,
        participantIds: form.participantIds,
      })
      wx.showToast({ title: '花销已记录', icon: 'success' })
      this.setData({
        form: {
          title: '',
          category: '餐饮',
          amount: '',
          note: '',
          payerId: this.data.travel.members[0]?.id || '',
          participantIds: this.data.travel.members.map((member) => member.id),
        },
      })
      this.refresh()
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },
})
