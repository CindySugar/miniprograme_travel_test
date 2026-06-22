<template>
  <view class="expense-page" catchtouchmove="true" @tap="close">
    <view v-if="travel" class="expense-sheet" @tap.stop="noop">
      <view class="sheet-title">记一笔</view>

      <view class="sheet-row">
        <view class="sheet-field sheet-field--title">
          <text class="sheet-label">账单名称</text>
          <input class="sheet-input" placeholder="比如海景民宿" :value="form.title" data-field="title" @input="onInput" />
        </view>
        <view class="sheet-field sheet-field--amount">
          <text class="sheet-label">金额</text>
          <input class="sheet-input sheet-input--amount" type="digit" placeholder="0" :value="form.amount" data-field="amount" @input="onInput" />
        </view>
      </view>

      <view class="sheet-block">
        <view class="sheet-head">
          <text class="sheet-label">谁先付了钱</text>
        </view>
        <view class="chip-list">
          <view
            v-for="member in members"
            :key="member.id"
            class="choice-chip"
            :class="{ 'choice-chip--active': form.payerId === member.id }"
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
            <view class="split-option" :class="{ 'split-option--active': form.splitType === 'equal' }" @tap="setSplitType('equal')">均摊</view>
            <view class="split-option" :class="{ 'split-option--active': form.splitType === 'amount' }" @tap="setSplitType('amount')">按金额</view>
          </view>
        </view>
        <view class="chip-list">
          <view
            v-for="member in members"
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
        <button class="cancel-btn" @tap="close">取消</button>
        <button class="submit-btn" @tap="saveExpense">记下这笔账单</button>
      </view>
    </view>

    <view v-else class="expense-sheet expense-sheet-loading" @tap.stop="noop">
      <view class="sheet-title">记一笔</view>
      <view class="loading-text">正在打开旅行信息</view>
    </view>
  </view>
</template>

<script>
import { getTravel, addExpense as storeAddExpense } from '../../utils/travel-store.js'

const defaultForm = () => ({
  title: '',
  amount: '',
  payerId: '',
  participantIds: [],
  splitType: 'equal',
})

export default {
  data() {
    return {
      travelId: '',
      travel: null,
      members: [],
      form: {
        ...defaultForm(),
      },
    }
  },
  onLoad(query) {
    this.travelId = query.travelId || ''
  },
  onShow() {
    this.refresh()
  },
  onBackPress() {
    this.close()
    return true
  },
  methods: {
    async refresh() {
      if (!this.travelId) {
        uni.showToast({ title: '缺少旅行信息', icon: 'none' })
        this.close()
        return
      }
      const travel = await getTravel(this.travelId).catch(() => null)
      if (!travel) {
        uni.showToast({ title: '旅行不存在', icon: 'none' })
        this.close()
        return
      }
      this.travel = travel
      this.members = travel.members || []
      const members = this.members
      if (!this.form.payerId || !members.some((member) => member.id === this.form.payerId)) {
        this.form.payerId = members[0]?.id || ''
      }
      if (!this.form.participantIds.length) {
        this.form.participantIds = members.map((member) => member.id)
      }
    },
    onInput(e) {
      const { field } = e.currentTarget.dataset
      this.form[field] = e.detail.value
    },
    selectPayer(memberId) {
      this.form.payerId = memberId
    },
    toggleParticipant(memberId) {
      const participantIds = new Set(this.form.participantIds)
      if (participantIds.has(memberId)) participantIds.delete(memberId)
      else participantIds.add(memberId)
      this.form.participantIds = Array.from(participantIds)
    },
    isParticipant(memberId) {
      return this.form.participantIds.includes(memberId)
    },
    setSplitType(splitType) {
      this.form.splitType = splitType
    },
    noop() {},
    close() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack({ delta: 1 })
        return
      }
      if (this.travelId) {
        uni.redirectTo({ url: `/pages/logs/logs?travelId=${this.travelId}` })
      }
    },
    async saveExpense() {
      if (!this.travel) {
        uni.showToast({ title: '请先打开旅行', icon: 'none' })
        return
      }
      if (!this.form.title.trim()) {
        uni.showToast({ title: '请输入账单名称', icon: 'none' })
        return
      }
      if (!this.form.amount || Number(this.form.amount) <= 0) {
        uni.showToast({ title: '请输入金额', icon: 'none' })
        return
      }
      if (!this.form.payerId) {
        uni.showToast({ title: '请选择付款人', icon: 'none' })
        return
      }
      if (!this.form.participantIds.length) {
        uni.showToast({ title: '至少选择一位分摊成员', icon: 'none' })
        return
      }
      try {
        await storeAddExpense(this.travel.id, {
          title: this.form.title.trim(),
          category: '其他',
          amount: this.form.amount,
          note: '',
          payerMemberId: this.form.payerId,
          participantMemberIds: this.form.participantIds,
          splitType: this.form.splitType,
        })
        uni.showToast({ title: '花销已记录', icon: 'success' })
        setTimeout(() => this.close(), 180)
      } catch (error) {
        uni.showToast({ title: error.message, icon: 'none' })
      }
    },
  },
}
</script>

<style>
@import "./expense.wxss";
</style>
