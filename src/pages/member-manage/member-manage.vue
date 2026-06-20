<template>
  <view class="manage-page" v-if="travel">
    <scroll-view class="manage-scroll" scroll-y enhanced :show-scrollbar="false">
      <view class="intro-card">
        管理员可以维护预置成员、清除错误认领、禁用记账权限或移出组队，也可以修改自己的昵称和头像。
      </view>

      <view class="section-head">
        <view class="section-title">邀请设置</view>
        <view class="section-meta">{{ travel.inviteStatusText }}</view>
      </view>
      <view class="setting-card">
        <view class="setting-copy">
          <view class="setting-title">允许新成员加入</view>
          <view class="setting-desc">关闭后，未加入的猫猫不能再通过分享卡片加入；已加入成员不受影响。</view>
        </view>
        <button class="light-button" @tap="toggleInvite">{{ travel.inviteButtonText }}</button>
      </view>

      <view class="section-head family-head">
        <view class="section-title">猫猫家庭</view>
        <view class="section-meta">最终按家庭转账</view>
      </view>
      <view class="family-card">
        <view class="field-label">选择同一个家庭的猫猫</view>
        <view class="choice-row">
          <block v-for="item in travel.familyCandidates" :key="item.id">
            <view class="choice-pill" :class="{ 'choice-pill-selected': item.selectedForFamily }" @tap="toggleFamilyMember" :data-id="item.id">{{ item.name }}</view>
          </block>
        </view>

        <view class="field-label owner-label">选择家主</view>
        <view class="owner-select-box" v-if="selectedFamilyMemberIds.length < 2">先选择至少两只猫猫。</view>
        <view v-else class="choice-row">
          <block v-for="item in travel.selectedFamilyMembers" :key="item.id">
            <view class="choice-pill" :class="{ 'choice-pill-owner-active': item.selectedAsOwner }" @tap="chooseFamilyOwner" :data-id="item.id">{{ item.name }}</view>
          </block>
        </view>

        <button class="family-submit" :class="{ 'family-submit-active': travel.canCreateFamily }" @tap="createFamily">组成家庭</button>

        <block v-for="item in families" :key="item.id">
          <view class="family-item">
            <view class="family-avatars">
              <block v-for="memberId in item.memberIds" :key="memberId">
                <view class="mini-avatar">猫</view>
              </block>
            </view>
            <view class="family-copy">
              <view class="family-name">{{ item.name }}</view>
              <view class="family-desc">{{ item.membersText }} · 家主 {{ item.ownerName }}</view>
            </view>
            <view class="remove-pill" @tap="removeFamily" :data-id="item.id">移除</view>
          </view>
        </block>
      </view>

      <view class="section-head add-head">
        <view class="section-title">添加成员</view>
        <view class="section-meta">{{ travel.pendingAddText }}</view>
      </view>
      <view class="add-card">
        <input class="add-input" placeholder="输入猫猫昵称" :value="newMemberName" @input="onMemberInput" />
        <button class="add-button" @tap="addMember">添加</button>
      </view>

      <view class="section-head list-head">
        <view class="section-title">成员列表</view>
        <view class="section-meta">{{ travel.memberCountText }}</view>
      </view>

      <block v-for="item in travel.membersDecorated" :key="item.id">
        <view class="member-card">
          <view class="member-top">
            <view class="avatar" :class="item.toneClass">
              <text v-if="!item.avatarUrl">{{ item.initial }}</text>
              <image v-else class="avatar-img" :src="item.avatarUrl" mode="aspectFill"></image>
              <view v-if="item.isOwner" class="avatar-mark">换</view>
            </view>
            <view class="member-main">
              <view class="name-row">
                <input class="name-input" :value="draftNames[item.id] ?? item.draftName" :data-id="item.id" @input="onDraftNameInput" />
                <view class="role-pill">{{ item.isOwner ? '管理员' : item.claimText }}</view>
              </view>
              <view class="status-row">
                <text>{{ item.billCount }} 笔账单 · {{ item.bookkeepingText }}</text>
                <text class="bind-text">{{ item.bindingText }}</text>
              </view>
              <view class="tag-row">
                <block v-for="tag in item.tags" :key="tag">
                  <text class="tag" :class="tag === '我自己' ? 'tag-green' : tag === '创建者' ? 'tag-blue' : tag === '家主' ? 'tag-yellow' : 'tag-red'">{{ tag }}</text>
                </block>
              </view>
            </view>
          </view>
          <view class="operation-row" v-if="!item.isOwner">
            <button class="operation-button" :data-id="item.id" @tap="saveMemberName">保存昵称</button>
            <button class="operation-button" :data-id="item.id" @tap="toggleBookkeeping">{{ disabledBookkeeping[item.id] ? '恢复记账' : '禁用记账' }}</button>
            <button class="operation-button operation-disabled" :class="{ 'operation-muted': !item.isClaimed }" :data-id="item.id" @tap="clearClaim" :disabled="!item.isClaimed">清除认领</button>
            <button class="operation-button operation-danger" :data-id="item.id" @tap="removeMember">移出组队</button>
          </view>
        </view>
      </block>
    </scroll-view>
  </view>
</template>

<script>
import { getTravel, addMember as storeAddMember, clearMemberClaim } from '../../utils/travel-store.js'

const MEMBER_TONES = ['member-tone-coral', 'member-tone-blue', 'member-tone-mint', 'member-tone-gold']
const createFamilyId = () => `family_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`
const countExpenseForMember = (travel, memberId) => (travel.expenses || []).filter((expense) => expense.payerId === memberId || (expense.shareWeights || []).some((share) => share.memberId === memberId)).length

const decorateMembers = (travel, disabledLookup, draftNames = {}, familyLookup = {}) => {
  let toneIndex = 0
  return (travel.members || []).map((member) => {
    const isOwner = !!member.isOwner
    const isClaimed = !!member.openid
    const disabledBookkeeping = !!disabledLookup[member.id]
    const family = familyLookup[member.id] || null
    const familyName = family?.name || ''
    const isFamilyOwner = !!family && family.ownerId === member.id
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
      familyId: family?.id || '',
      familyName,
      familyMemberIds: family?.memberIds || [],
      isFamilyOwner,
      tags: [...(isOwner ? ['我自己', '创建者', '管理员'] : []), ...(familyName ? [familyName] : []), ...(isFamilyOwner ? ['家主'] : [])],
    }
  })
}

const buildView = (travel, pageState) => {
  const disabledLookup = pageState.disabledBookkeeping || {}
  const families = Array.isArray(pageState.families) ? pageState.families : []
  const familyLookup = {}
  families.forEach((family) => {
    (family.memberIds || []).forEach((memberId) => {
      familyLookup[memberId] = family
    })
  })
  const members = decorateMembers(travel, disabledLookup, pageState.draftNames || {}, familyLookup)
  const pendingCount = members.filter((member) => !member.isClaimed).length
  const selectedLookup = Object.fromEntries((pageState.selectedFamilyMemberIds || []).map((id) => [id, true]))
  const selectedFamilyMembers = members.filter((member) => selectedLookup[member.id]).map((member) => ({ ...member, selectedAsOwner: pageState.familyOwnerId === member.id }))
  return {
    ...travel,
    membersDecorated: members,
    memberCountText: `${members.length} 只猫猫`,
    pendingAddText: pendingCount ? '未绑定微信，待认领' : '已全部绑定微信',
    inviteStatusText: pageState.allowInvite ? '邀请开启中' : '邀请关闭',
    inviteButtonText: pageState.allowInvite ? '关闭邀请' : '开启邀请',
    familyCandidates: members.filter((member) => !member.familyId).map((member) => ({ ...member, selectedForFamily: !!selectedLookup[member.id] })),
    selectedFamilyMembers,
    canCreateFamily: selectedFamilyMembers.length >= 2 && !!pageState.familyOwnerId,
  }
}

export default {
  data() {
    return {
      travelId: '',
      travel: null,
      allowInvite: true,
      newMemberName: '',
      selectedFamilyMemberIds: [],
      familyOwnerId: '',
      families: [],
      disabledBookkeeping: {},
      draftNames: {},
    }
  },
  onLoad(query) {
    this.travelId = query.travelId || ''
  },
  onShow() {
    this.refresh()
  },
  methods: {
    refresh(stateOverrides = {}) {
      const travel = getTravel(this.travelId) || null
      if (!travel) return
      this.travelId = travel.id
      this.travel = buildView(travel, {
        allowInvite: this.allowInvite,
        selectedFamilyMemberIds: this.selectedFamilyMemberIds,
        familyOwnerId: this.familyOwnerId,
        families: this.families,
        disabledBookkeeping: this.disabledBookkeeping,
        draftNames: this.draftNames,
        ...stateOverrides,
      })
    },
    toggleInvite() {
      this.allowInvite = !this.allowInvite
      this.refresh({ allowInvite: this.allowInvite })
    },
    onMemberInput(e) {
      this.newMemberName = e.detail.value
    },
    addMember() {
      const name = (this.newMemberName || '').trim()
      if (!name) {
        uni.showToast({ title: '请输入成员昵称', icon: 'none' })
        return
      }
      try {
        storeAddMember(this.travel.id, { name })
        this.newMemberName = ''
        this.refresh()
        uni.showToast({ title: '成员已添加', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: error.message, icon: 'none' })
      }
    },
    toggleFamilyMember(e) {
      const memberId = e.currentTarget.dataset.id
      const selected = new Set(this.selectedFamilyMemberIds)
      if (selected.has(memberId)) selected.delete(memberId)
      else selected.add(memberId)
      const nextSelected = Array.from(selected)
      const nextFamilyOwnerId = nextSelected.includes(this.familyOwnerId) ? this.familyOwnerId : ''
      this.selectedFamilyMemberIds = nextSelected
      this.familyOwnerId = nextFamilyOwnerId
      this.refresh({
        selectedFamilyMemberIds: nextSelected,
        familyOwnerId: nextFamilyOwnerId,
      })
    },
    chooseFamilyOwner(e) {
      const memberId = e.currentTarget.dataset.id
      if (!this.selectedFamilyMemberIds.includes(memberId)) return
      this.familyOwnerId = memberId
      this.refresh({ familyOwnerId: memberId })
    },
    createFamily() {
      const { selectedFamilyMemberIds, familyOwnerId, travel } = this
      if (selectedFamilyMemberIds.length < 2 || !familyOwnerId) {
        uni.showToast({ title: '先选择至少两只猫猫和家主', icon: 'none' })
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
      const nextFamilies = this.families.concat(family)
      this.families = nextFamilies
      this.selectedFamilyMemberIds = []
      this.familyOwnerId = ''
      this.refresh({
        families: nextFamilies,
        selectedFamilyMemberIds: [],
        familyOwnerId: '',
      })
    },
    removeFamily(e) {
      const familyId = e.currentTarget.dataset.id
      const nextFamilies = this.families.filter((family) => family.id !== familyId)
      this.families = nextFamilies
      this.refresh({ families: nextFamilies })
    },
    onDraftNameInput(e) {
      const { id } = e.currentTarget.dataset
      this.draftNames = {
        ...this.draftNames,
        [id]: e.detail.value,
      }
    },
    saveMemberName(e) {
      const { id } = e.currentTarget.dataset
      const member = this.travel.membersDecorated.find((item) => item.id === id)
      const draftName = (this.draftNames[id] ?? member?.draftName ?? '').trim()
      if (!member || !draftName) {
        uni.showToast({ title: '昵称不能为空', icon: 'none' })
        return
      }
      uni.showToast({ title: '昵称已保存', icon: 'success' })
    },
    toggleBookkeeping(e) {
      const { id } = e.currentTarget.dataset
      const nextDisabledBookkeeping = {
        ...this.disabledBookkeeping,
        [id]: !this.disabledBookkeeping[id],
      }
      this.disabledBookkeeping = nextDisabledBookkeeping
      this.refresh({ disabledBookkeeping: nextDisabledBookkeeping })
    },
    clearClaim(e) {
      const { id } = e.currentTarget.dataset
      try {
        clearMemberClaim(this.travel.id, id)
        this.refresh()
        uni.showToast({ title: '已回退为待认领', icon: 'none' })
      } catch (error) {
        uni.showToast({ title: error.message, icon: 'none' })
      }
    },
    removeMember(e) {
      const { id } = e.currentTarget.dataset
      const member = this.travel.membersDecorated.find((item) => item.id === id)
      if (member?.isOwner) {
        uni.showToast({ title: '管理员不能移出组队', icon: 'none' })
        return
      }
      uni.showToast({ title: '移出组队稍后接入', icon: 'none' })
    },
  },
}
</script>

<style>
@import "./member-manage.wxss";
</style>
