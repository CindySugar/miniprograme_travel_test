<template>
  <view class="page" v-if="travel">
    <view class="page-shell">
      <view class="hero-card">
        <view class="hero-top">
          <view class="hero-copy">
            <view class="status-pill" :class="travel.statusToneClass">{{ travel.status }}</view>
            <view class="hero-date">{{ travel.displayDateLabel }}</view>
          </view>
          <image class="hero-image" src="/static/travel-cat.png" mode="aspectFit"></image>
        </view>

        <view class="summary-card">
          <view class="summary-main">
            <view class="summary-copy">
              <view class="summary-label">{{ travel.summaryLabel }}</view>
              <view class="summary-amount">{{ travel.totalSpentFullDisplay }}</view>
            </view>
            <view class="summary-actions">
              <view class="summary-link" @tap="gotoSettlement">查看结算</view>
              <view v-if="travel.status !== '已结清'" class="summary-sub-link" @tap="finishTravel">标记已结清</view>
            </view>
          </view>
          <view class="summary-meta">{{ travel.expenseCountDisplay }}</view>
        </view>
      </view>

      <button class="primary-entry" @tap="gotoExpense">记一笔</button>

      <view class="detail-section">
        <view class="detail-section-title">同行猫猫</view>

        <view class="member-card">
          <view class="member-stack">
            <block v-for="item in travel.membersDecorated" :key="item.id">
              <view class="member-avatar" :class="item.toneClass">
                <text>{{ item.badgeText }}</text>
                <view v-if="item.isOwner" class="avatar-owner-badge">主</view>
              </view>
            </block>
          </view>

          <view class="member-info-row">
            <view class="member-copy">
              <view class="member-summary">{{ travel.memberSummaryDisplay }}</view>
              <view class="claim-summary">{{ travel.claimSummaryDisplay }}</view>
            </view>
            <view class="member-actions">
              <view class="action-pill action-pill-outline" @tap="inviteMembers">邀请同行</view>
              <button class="action-pill action-pill-soft member-manage-btn" @tap="gotoMemberManage">
                <text class="action-pill-text">管理</text>
              </button>
            </view>
          </view>
        </view>

        <view class="member-manager" v-if="showMemberManager">
          <view class="manager-note">{{ travel.pendingClaimHelp }}</view>
          <view class="manager-list">
            <block v-for="item in travel.membersDecorated" :key="item.id">
              <view class="manager-row">
                <view class="manager-member">
                  <view class="member-avatar-small" :class="item.toneClass">
                    <text>{{ item.badgeText }}</text>
                    <view v-if="item.isOwner" class="avatar-owner-badge">主</view>
                  </view>
                  <view class="manager-copy">
                    <view class="manager-name">{{ item.name }}</view>
                    <view class="manager-sub">{{ item.identityText }}</view>
                  </view>
                </view>
                <view class="claim-pill" :class="item.isPendingClaim ? 'claim-pill-pending' : 'claim-pill-claimed'">{{ item.claimStatusText }}</view>
              </view>
            </block>
          </view>
          <view class="member-adder">
            <input class="manager-input" placeholder="输入同行猫猫昵称" :value="memberName" @input="onMemberInput" />
            <button class="manager-add-btn" @tap="addMember">添加</button>
          </view>
        </view>
      </view>

      <view class="detail-section">
        <view class="detail-section-head">
          <view class="detail-section-title">最近账单</view>
          <view class="detail-section-action-row">
            <view class="filter-pill" @tap="toggleFundPanel">预收/基金</view>
            <view class="filter-pill" @tap="toggleExpenseBook">{{ travel.bookActionText }}</view>
          </view>
        </view>

        <view class="fund-card" v-if="showFundPanel">
          预收款和猫猫基金台账还没单独拆页，当前可以先通过普通账单或备注记录，后续再补专门入口。
        </view>

        <view class="expense-list" v-if="travel.visibleExpenses.length">
          <block v-for="item in travel.visibleExpenses" :key="item.id">
            <view class="expense-card" @tap="showExpenseEditHint">
              <view class="expense-icon" :class="item.payerBadge.toneClass">
                <text>{{ item.payerBadge.badgeText }}</text>
                <view v-if="item.payerBadge.isOwner" class="avatar-owner-badge">主</view>
              </view>
              <view class="expense-content">
                <view class="expense-top">
                  <view class="expense-maincopy">
                    <view class="expense-title-row">
                      <text class="expense-title">{{ item.title }}</text>
                      <text class="expense-edit-tag">{{ item.editableText }}</text>
                      <text class="expense-time">{{ item.createdAtDisplay }}</text>
                    </view>
                  </view>
                  <text class="expense-amount">{{ item.amountFullDisplay }}</text>
                </view>

                <view class="expense-flow">
                  <text class="expense-flow-label">垫付</text>
                  <view class="expense-mini-stack">
                    <view class="expense-mini-avatar" :class="item.payerBadge.toneClass">
                      <text>{{ item.payerBadge.badgeText }}</text>
                    </view>
                  </view>
                  <view class="expense-mini-stack">
                    <block v-for="participant in item.participantBadges" :key="participant.id">
                      <view class="expense-mini-avatar" :class="participant.toneClass">
                        <text>{{ participant.badgeText }}</text>
                      </view>
                    </block>
                  </view>
                  <text class="expense-flow-label">分摊</text>
                </view>
              </view>
            </view>
          </block>
        </view>

        <view v-else class="empty-card">还没有账单，先记一笔吧。</view>
      </view>
    </view>

    <view v-if="showExpenseSheet" class="expense-overlay" catchtouchmove="true" @tap="closeExpenseSheet">
      <view class="expense-sheet" @tap.stop="noop">
        <view class="sheet-title">记一笔</view>

        <view class="sheet-row">
          <view class="sheet-field sheet-field--title">
            <text class="sheet-label">账单名称</text>
            <input class="sheet-input" placeholder="比如海景民宿" :value="expenseForm.title" data-field="title" @input="onExpenseInput" />
          </view>
          <view class="sheet-field sheet-field--amount">
            <text class="sheet-label">金额</text>
            <input class="sheet-input sheet-input--amount" type="digit" placeholder="0" :value="expenseForm.amount" data-field="amount" @input="onExpenseInput" />
          </view>
        </view>

        <view class="sheet-block">
          <view class="sheet-head">
            <text class="sheet-label">谁先付了钱</text>
          </view>
          <view class="chip-list">
            <view
              v-for="member in expenseMembers"
              :key="member.id"
              class="choice-chip"
              :class="{ 'choice-chip--active': expenseForm.payerId === member.id }"
              @tap="selectPayer(member.id)"
            >
              {{ member.name }}
            </view>
          </view>
        </view>

        <view class="sheet-block">
          <view class="sheet-head sheet-head--split">
            <text class="sheet-label">这笔由谁分摊</text>
            <view class="split-switch">
              <view class="split-option" :class="{ 'split-option--active': expenseForm.splitType === 'equal' }" @tap="setSplitType('equal')">均摊</view>
              <view class="split-option" :class="{ 'split-option--active': expenseForm.splitType === 'amount' }" @tap="setSplitType('amount')">按金额</view>
            </view>
          </view>
          <view class="chip-list">
            <view
              v-for="member in expenseMembers"
              :key="member.id"
              class="choice-chip choice-chip--member"
              :class="{ 'choice-chip--member-active': isParticipant(member.id) }"
              @tap="toggleParticipant(member.id)"
            >
              {{ member.name }}
            </view>
          </view>
        </view>

        <view class="sheet-actions">
          <button class="cancel-btn" @tap="closeExpenseSheet">取消</button>
          <button class="submit-btn" @tap="saveExpense">记下这笔账单</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getTravel, addExpense as storeAddExpense, addMember as storeAddMember, markTravelCompleted } from '../../utils/travel-store.js'

const MEMBER_TONES = ['member-tone-coral', 'member-tone-blue', 'member-tone-mint', 'member-tone-gold']
const defaultExpenseForm = () => ({
  title: '',
  amount: '',
  payerId: '',
  participantIds: [],
  splitType: 'equal',
})

const formatNumber = (value) => (`${value}`[1] ? `${value}` : `0${value}`)
const formatDateTime = (value) => {
  if (!value) return '时间待补'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '时间待补'
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
      identityText: member.isOwner ? '管理员' : isPendingClaim ? '临时身份未绑定微信号' : '微信号已绑定',
    }
  })
}

const decorateExpenses = (travel, memberLookup) => {
  return (travel.expenses || [])
    .map((expense) => {
      const payerBadge = memberLookup[expense.payerId] || { badgeText: '垫', toneClass: 'member-tone-owner', isOwner: false }
      const participantBadges = (expense.shareWeights || []).map((share) => memberLookup[share.memberId]).filter(Boolean)
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
    memberSummaryDisplay: familyCount ? `${travel.memberCount}只猫猫 · ${familyCount}个家庭` : `${travel.memberCount}只猫猫`,
    claimSummaryDisplay: pendingClaimCount ? `${pendingClaimCount}位待认领 · 管理员：${owner.name}` : `已全部认领 · 管理员：${owner.name}`,
    pendingClaimHelp: pendingClaimCount ? '待认领表示临时成员还没有绑定微信号。' : '当前同行成员都已经绑定微信号。',
    bookActionText: showAllExpenses && expenses.length > 2 ? '收起账本' : '查看账本',
    hasMoreExpenses: expenses.length > 2,
    membersDecorated: members,
    visibleExpenses: showAllExpenses ? expenses : expenses.slice(0, 2),
  }
}

export default {
  data() {
    return {
      travelId: '',
      travel: null,
      memberName: '',
      showMemberManager: false,
      showAllExpenses: false,
      showFundPanel: false,
      showExpenseSheet: false,
      rawTravel: null,
      expenseForm: defaultExpenseForm(),
    }
  },
  onLoad(query) {
    this.travelId = query.travelId || ''
  },
  onShow() {
    this.refresh()
  },
  methods: {
    async refresh() {
      const rawTravel = await getTravel(this.travelId).catch(() => null)
      if (!rawTravel) return
      this.travelId = rawTravel.id
      this.rawTravel = rawTravel
      this.travel = buildTravelView(rawTravel, { showAllExpenses: this.showAllExpenses })
      uni.setNavigationBarTitle({
        title: this.travel.title || '旅行详情',
      })
    },
    onExpenseInput(e) {
      const { field } = e.currentTarget.dataset
      this.expenseForm[field] = e.detail.value
    },
    selectPayer(memberId) {
      this.expenseForm.payerId = memberId
    },
    toggleParticipant(memberId) {
      const participantIds = new Set(this.expenseForm.participantIds)
      if (participantIds.has(memberId)) participantIds.delete(memberId)
      else participantIds.add(memberId)
      this.expenseForm.participantIds = Array.from(participantIds)
    },
    isParticipant(memberId) {
      return this.expenseForm.participantIds.includes(memberId)
    },
    setSplitType(splitType) {
      this.expenseForm.splitType = splitType
    },
    noop() {},
    openExpenseSheet() {
      const members = this.expenseMembers
      this.expenseForm = {
        ...defaultExpenseForm(),
        payerId: members[0]?.id || '',
        participantIds: members.map((member) => member.id),
      }
      this.showExpenseSheet = true
    },
    closeExpenseSheet() {
      this.showExpenseSheet = false
    },
    async saveExpense() {
      if (!this.rawTravel) {
        uni.showToast({ title: '请先打开旅行', icon: 'none' })
        return
      }
      if (!this.expenseForm.title.trim()) {
        uni.showToast({ title: '请输入账单名称', icon: 'none' })
        return
      }
      if (!this.expenseForm.amount || Number(this.expenseForm.amount) <= 0) {
        uni.showToast({ title: '请输入金额', icon: 'none' })
        return
      }
      if (!this.expenseForm.payerId) {
        uni.showToast({ title: '请选择付款人', icon: 'none' })
        return
      }
      if (!this.expenseForm.participantIds.length) {
        uni.showToast({ title: '至少选择一位分摊成员', icon: 'none' })
        return
      }
      try {
        await storeAddExpense(this.rawTravel.id, {
          title: this.expenseForm.title.trim(),
          category: '其他',
          amount: this.expenseForm.amount,
          note: '',
          payerMemberId: this.expenseForm.payerId,
          participantMemberIds: this.expenseForm.participantIds,
          splitType: this.expenseForm.splitType,
        })
        this.closeExpenseSheet()
        await this.refresh()
        uni.showToast({ title: '花销已记录', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: error.message, icon: 'none' })
      }
    },
    onMemberInput(e) {
      this.memberName = e.detail.value
    },
    async addMember() {
      if (!this.travel) {
        uni.showToast({ title: '请先创建旅行', icon: 'none' })
        return
      }
      try {
        await storeAddMember(this.travel.id, { name: this.memberName })
        this.memberName = ''
        await this.refresh()
        uni.showToast({ title: '成员已添加', icon: 'success' })
      } catch (error) {
        uni.showToast({ title: error.message, icon: 'none' })
      }
    },
    toggleMemberManager() {
      this.showMemberManager = !this.showMemberManager
    },
    toggleExpenseBook() {
      if (!this.travel) return
      if (!this.travel.hasMoreExpenses && !this.showAllExpenses) {
        uni.showToast({ title: '当前已展示全部账单', icon: 'none' })
        return
      }
      this.showAllExpenses = !this.showAllExpenses
      this.refresh()
    },
    toggleFundPanel() {
      this.showFundPanel = !this.showFundPanel
    },
    inviteMembers() {
      if (!this.travel) return
      uni.setClipboardData({
        data: this.travel.inviteCode,
        success: () => uni.showToast({ title: '邀请码已复制', icon: 'none' }),
      })
    },
    gotoMemberManage() {
      if (!this.travel) return
      uni.navigateTo({ url: `/pages/member-manage/member-manage?travelId=${this.travel.id}` })
    },
    showExpenseEditHint() {
      uni.showToast({ title: '编辑账单入口稍后补上', icon: 'none' })
    },
    async finishTravel() {
      if (!this.travel) return
      await markTravelCompleted(this.travel.id)
      uni.showToast({ title: '已结清', icon: 'success' })
      await this.refresh()
    },
    gotoSettlement() {
      if (!this.travel) return
      uni.navigateTo({ url: `/pages/settlement/settlement?travelId=${this.travel.id}` })
    },
    gotoExpense() {
      if (!this.travel) return
      this.openExpenseSheet()
    },
  },
  computed: {
    expenseMembers() {
      return this.rawTravel?.members || []
    },
  },
}
</script>

<style>
@import "./logs.wxss";
</style>
