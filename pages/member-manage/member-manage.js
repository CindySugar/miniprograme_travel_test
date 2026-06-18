const store = require('../../utils/travel-store.js')

const MEMBER_TONES = ['member-tone-coral', 'member-tone-blue', 'member-tone-mint', 'member-tone-gold']

const createFamilyId = () => `family_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`

const countExpenseForMember = (travel, memberId) => {
  return (travel.expenses || []).filter((expense) => (
    expense.payerId === memberId || (expense.shareWeights || []).some((share) => share.memberId === memberId)
  )).length
}

const decorateMembers = (travel, disabledLookup, draftNames = {}) => {
  let toneIndex = 0
  return (travel.members || []).map((member) => {
    const isOwner = !!member.isOwner
    const isClaimed = !!member.openid
    const disabledBookkeeping = !!disabledLookup[member.id]
    const toneClass = isOwner ? 'member-tone-owner' : MEMBER_TONES[toneIndex++ % MEMBER_TONES.length]
    return {
      ...member,
      draftName: draftNames[member.id] || member.name,
      initial: (member.name || '猫').slice(0, 1),
      toneClass,
      isClaimed,
      bindingText: isClaimed ? '已绑定微信' : '未绑定微信，可被邀请人认领',
      claimText: isClaimed ? '已绑定微信' : '待认领',
      billCount: countExpenseForMember(travel, member.id),
      bookkeepingText: disabledBookkeeping ? '禁用记账' : isClaimed ? '可记账' : '认领后可记账',
      disabledBookkeeping,
      tags: [
        ...(isOwner ? ['我自己', '创建者', '管理员'] : []),
        ...(member.familyName ? [member.familyName] : []),
        ...(member.isFamilyOwner ? ['家主'] : []),
      ],
    }
  })
}

const buildView = (travel, pageState) => {
  const disabledLookup = pageState.disabledBookkeeping || {}
  const members = decorateMembers(travel, disabledLookup, pageState.draftNames || {})
  const pendingCount = members.filter((member) => !member.isClaimed).length
  const selectedLookup = Object.fromEntries((pageState.selectedFamilyMemberIds || []).map((id) => [id, true]))
  const selectedFamilyMembers = members
    .filter((member) => selectedLookup[member.id])
    .map((member) => ({
      ...member,
      selectedAsOwner: pageState.familyOwnerId === member.id,
    }))

  return {
    ...travel,
    membersDecorated: members,
    memberCountText: `${members.length} 只猫猫`,
    pendingAddText: pendingCount ? '未绑定微信，待认领' : '已全部绑定微信',
    inviteStatusText: pageState.allowInvite ? '邀请开启中' : '邀请关闭',
    inviteButtonText: pageState.allowInvite ? '关闭邀请' : '开启邀请',
    familyCandidates: members.filter((member) => !member.isOwner).map((member) => ({
      ...member,
      selectedForFamily: !!selectedLookup[member.id],
    })),
    selectedFamilyMembers,
    canCreateFamily: selectedFamilyMembers.length >= 2 && !!pageState.familyOwnerId,
  }
}

Page({
  data: {
    travelId: '',
    travel: null,
    allowInvite: true,
    newMemberName: '',
    selectedFamilyMemberIds: [],
    familyOwnerId: '',
    families: [],
    disabledBookkeeping: {},
    draftNames: {},
  },
  onLoad(query) {
    this.setData({ travelId: query.travelId || '' })
  },
  onShow() {
    this.refresh()
  },
  refresh() {
    const travel = store.getTravel(this.data.travelId) || store.listTravels()[0] || null
    if (!travel) {
      return
    }
    this.setData({
      travelId: travel.id,
      travel: buildView(travel, this.data),
    })
  },
  toggleInvite() {
    this.setData({
      allowInvite: !this.data.allowInvite,
    }, () => {
      this.refresh()
    })
  },
  onMemberInput(e) {
    this.setData({ newMemberName: e.detail.value })
  },
  addMember() {
    const name = (this.data.newMemberName || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入成员昵称', icon: 'none' })
      return
    }
    try {
      store.addMember(this.data.travel.id, { name })
      this.setData({ newMemberName: '' })
      this.refresh()
      wx.showToast({ title: '成员已添加', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },
  toggleFamilyMember(e) {
    const memberId = e.currentTarget.dataset.id
    const selected = new Set(this.data.selectedFamilyMemberIds)
    if (selected.has(memberId)) {
      selected.delete(memberId)
    } else {
      selected.add(memberId)
    }
    const nextSelected = Array.from(selected)
    this.setData({
      selectedFamilyMemberIds: nextSelected,
      familyOwnerId: nextSelected.includes(this.data.familyOwnerId) ? this.data.familyOwnerId : '',
    })
  },
  chooseFamilyOwner(e) {
    const memberId = e.currentTarget.dataset.id
    if (!this.data.selectedFamilyMemberIds.includes(memberId)) {
      return
    }
    this.setData({ familyOwnerId: memberId })
  },
  createFamily() {
    const { selectedFamilyMemberIds, familyOwnerId, travel } = this.data
    if (selectedFamilyMemberIds.length < 2 || !familyOwnerId) {
      wx.showToast({ title: '先选择至少两只猫猫和家主', icon: 'none' })
      return
    }

    const memberLookup = Object.fromEntries(travel.membersDecorated.map((member) => [member.id, member]))
    const familyOwner = memberLookup[familyOwnerId]
    const familyName = familyOwner ? `${familyOwner.name}家` : '猫猫家庭'
    const family = {
      id: createFamilyId(),
      name: familyName,
      ownerId: familyOwnerId,
      memberIds: selectedFamilyMemberIds,
      membersText: selectedFamilyMemberIds.map((id) => memberLookup[id]?.name).filter(Boolean).join('、'),
      ownerName: familyOwner?.name || '未指定',
    }

    this.setData({
      families: this.data.families.concat(family),
      selectedFamilyMemberIds: [],
      familyOwnerId: '',
    }, () => {
      this.refresh()
    })
  },
  removeFamily(e) {
    const familyId = e.currentTarget.dataset.id
    this.setData({
      families: this.data.families.filter((family) => family.id !== familyId),
    }, () => {
      this.refresh()
    })
  },
  onDraftNameInput(e) {
    const { id } = e.currentTarget.dataset
    this.setData({
      draftNames: {
        ...this.data.draftNames,
        [id]: e.detail.value,
      },
    })
  },
  saveMemberName(e) {
    const { id } = e.currentTarget.dataset
    const member = this.data.travel.membersDecorated.find((item) => item.id === id)
    const draftName = (this.data.draftNames[id] ?? member?.draftName ?? '').trim()
    if (!member || !draftName) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }
    wx.showToast({ title: '昵称已保存', icon: 'success' })
  },
  toggleBookkeeping(e) {
    const { id } = e.currentTarget.dataset
    this.setData({
      disabledBookkeeping: {
        ...this.data.disabledBookkeeping,
        [id]: !this.data.disabledBookkeeping[id],
      },
    }, () => {
      this.refresh()
    })
  },
  clearClaim(e) {
    const { id } = e.currentTarget.dataset
    try {
      store.clearMemberClaim(this.data.travel.id, id)
      this.refresh()
      wx.showToast({ title: '已回退为待认领', icon: 'none' })
    } catch (error) {
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },
  removeMember(e) {
    const { id } = e.currentTarget.dataset
    const member = this.data.travel.membersDecorated.find((item) => item.id === id)
    if (member?.isOwner) {
      wx.showToast({ title: '管理员不能移出组队', icon: 'none' })
      return
    }
    wx.showToast({ title: '移出组队稍后接入', icon: 'none' })
  },
})
