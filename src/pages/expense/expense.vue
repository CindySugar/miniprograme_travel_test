<template>
  <view class="page" v-if="travel">
    <view class="hero">
      <view class="hero-subtitle">{{ travel.title }} · 记一笔新的开销</view>
    </view>
    <view class="section">
      <view class="field">
        <text class="label">标题</text>
        <input class="input" placeholder="例如：晚餐" :value="form.title" @input="onInput" data-field="title" />
      </view>
      <view class="field">
        <text class="label">分类</text>
        <input class="input" placeholder="例如：餐饮" :value="form.category" @input="onInput" data-field="category" />
      </view>
      <view class="field">
        <text class="label">金额</text>
        <input class="input" type="digit" placeholder="0.00" :value="form.amount" @input="onInput" data-field="amount" />
      </view>
      <view class="field">
        <text class="label">备注</text>
        <textarea class="textarea" placeholder="可选" :value="form.note" @input="onInput" data-field="note"></textarea>
      </view>
      <view class="field">
        <text class="label">付款人</text>
        <picker mode="selector" :range="travel.memberNames" @change="onPayerChange">
          <view class="picker">{{ travel.payerName }}</view>
        </picker>
      </view>
      <view class="field">
        <text class="label">参与分摊的人</text>
        <view class="row row-wrap">
          <block v-for="item in travel.memberPills" :key="item.id">
            <view class="chip" :class="{ 'chip-soft': item.selected }" :data-id="item.id" @tap="toggleParticipant">{{ item.name }}</view>
          </block>
        </view>
      </view>
      <view class="field">
        <button class="primary-btn" @tap="saveExpense">记录花销</button>
      </view>
    </view>
  </view>
</template>

<script>
import { getTravel, addExpense as storeAddExpense } from '../../utils/travel-store.js'

export default {
  data() {
    return {
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
      const travel = await getTravel(this.travelId).catch(() => null)
      if (!travel) return
      const payerId = this.form.payerId || travel.members[0]?.id || ''
      const payerName = travel.members.find((member) => member.id === payerId)?.name || travel.members[0]?.name || ''
      this.travel = {
        ...travel,
        memberNames: travel.members.map((member) => member.name),
        payerName,
        memberPills: travel.members.map((member) => ({
          ...member,
          selected: this.form.participantIds.length ? this.form.participantIds.includes(member.id) : true,
        })),
      }
      this.form.payerId = payerId
      this.form.participantIds = this.form.participantIds.length ? this.form.participantIds : travel.members.map((member) => member.id)
    },
    onInput(e) {
      const { field } = e.currentTarget.dataset
      this.form[field] = e.detail.value
    },
    onPayerChange(e) {
      const payerId = this.travel.members[Number(e.detail.value)]?.id || ''
      const payerName = this.travel.members.find((member) => member.id === payerId)?.name || ''
      this.form.payerId = payerId
      this.travel.payerName = payerName
    },
    toggleParticipant(e) {
      const memberId = e.currentTarget.dataset.id
      const participantIds = new Set(this.form.participantIds)
      if (participantIds.has(memberId)) participantIds.delete(memberId)
      else participantIds.add(memberId)
      this.form.participantIds = Array.from(participantIds)
      this.travel.memberPills = this.travel.members.map((member) => ({ ...member, selected: participantIds.has(member.id) }))
    },
    async saveExpense() {
      if (!this.travel) {
        uni.showToast({ title: '请先创建旅行', icon: 'none' })
        return
      }
      try {
        await storeAddExpense(this.travel.id, {
          title: this.form.title,
          category: this.form.category,
          amount: this.form.amount,
          note: this.form.note,
          payerId: this.form.payerId,
          participantIds: this.form.participantIds,
        })
        uni.showToast({ title: '花销已记录', icon: 'success' })
        this.form = {
          title: '',
          category: '餐饮',
          amount: '',
          note: '',
          payerId: this.travel.members[0]?.id || '',
          participantIds: this.travel.members.map((member) => member.id),
        }
        await this.refresh()
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
