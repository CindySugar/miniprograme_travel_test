const store = require('../../utils/travel-store.js')
const { formatDate, todayISO } = require('../../utils/util.js')

const tabs = [
  { key: 'team', label: '组队' },
  { key: 'detail', label: '详情' },
  { key: 'advanced', label: '高级' },
]

const decorateMember = (member) => ({
  ...member,
  initial: (member.name || '猫').slice(0, 1),
})

Page({
  data: {
    activeTab: 'team',
    currentUser: store.getCurrentUser(),
    tabs,
    newMemberName: '',
    allowMemberFamilyEdit: true,
    form: {
      title: '',
      destination: '',
      ownerName: '',
      startDate: '',
      advanceAmount: '',
      catFund: '',
    },
    members: [],
    displayStartDate: '',
    ownerInitial: '猫',
  },
  onShow() {
    const currentUser = store.getCurrentUser()
    const ownerName = this.data.form.ownerName || currentUser.name || ''
    const startDate = this.data.form.startDate || todayISO()
    this.setData({
      currentUser,
      'form.ownerName': ownerName,
      'form.startDate': startDate,
      displayStartDate: formatDate(startDate),
      ownerInitial: (ownerName || '猫').slice(0, 1),
      members: this.data.members.length
        ? this.data.members
        : [decorateMember({ id: 'owner_preview', name: ownerName || '使用微信昵称', isOwner: true })],
    })
  },
  switchTab(e) {
    const { tab } = e.currentTarget.dataset
    this.setData({ activeTab: tab })
  },
  onInput(e) {
    const { field } = e.currentTarget.dataset
    const nextData = {
      [`form.${field}`]: e.detail.value,
    }
    if (field === 'ownerName') {
      nextData.ownerInitial = (e.detail.value || '猫').slice(0, 1)
      nextData.members = this.data.members.map((member) => (
        member.isOwner ? decorateMember({ ...member, name: e.detail.value || '使用微信昵称' }) : member
      ))
    }
    if (field === 'startDate') {
      nextData.displayStartDate = formatDate(e.detail.value || todayISO())
    }
    this.setData(nextData)
  },
  onMemberInput(e) {
    this.setData({ newMemberName: e.detail.value })
  },
  addPreviewMember() {
    const name = (this.data.newMemberName || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入同行猫猫昵称', icon: 'none' })
      return
    }
    const exists = this.data.members.some((member) => member.name === name)
    if (exists) {
      wx.showToast({ title: '这只猫猫已在队伍里', icon: 'none' })
      return
    }
    this.setData({
      members: this.data.members.concat({
        id: `preview_${Date.now()}`,
        name,
        isOwner: false,
      }).map(decorateMember),
      newMemberName: '',
    })
  },
  togglePermission(e) {
    this.setData({ allowMemberFamilyEdit: e.detail.value })
  },
  createTravel() {
    const { title, destination, ownerName, startDate } = this.data.form
    if (!title.trim()) {
      wx.showToast({ title: '请输入组队名称', icon: 'none' })
      return
    }
    const travel = store.createTravel({
      title,
      destination,
      ownerName,
      startDate,
      members: this.data.members
        .filter((member) => !member.isOwner)
        .map((member) => ({ name: member.name })),
    })
    wx.showToast({ title: '队伍已创建', icon: 'success' })
    wx.redirectTo({
      url: `/pages/logs/logs?travelId=${travel.id}`,
    })
  },
})
