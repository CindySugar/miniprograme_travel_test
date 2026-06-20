<template>
  <view class="page" v-if="travel">
    <view class="hero">
      <view class="hero-subtitle">{{ travel.title }} · 总花费 {{ travel.summary.totalSpentDisplay }}</view>
    </view>
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">转账建议</view>
          <view class="section-meta">尽量用最少的转账把账平掉。</view>
        </view>
      </view>
      <view class="list">
        <view class="list-item" v-for="(item, index) in travel.summary.transfers" :key="index">
          <view class="list-main">
            <view class="title-line">
              <text class="title">{{ item.fromName }} → {{ item.toName }}</text>
              <text class="amount">{{ item.amountDisplay }}</text>
            </view>
            <view class="subtext">请按这个建议转账即可。</view>
          </view>
        </view>
        <view v-if="!travel.summary.transfers.length" class="subtext">目前已经平账，不需要额外转账。</view>
      </view>
    </view>
    <view class="section">
      <view class="section-head">
        <view>
          <view class="section-title">成员净额</view>
        </view>
      </view>
      <view class="list">
        <view class="list-item" v-for="item in travel.summary.balances" :key="item.memberId">
          <view class="list-main">
            <view class="title-line">
              <text class="title">{{ item.name }}</text>
              <text class="amount" :class="item.netClass">{{ item.netDisplay }}</text>
            </view>
            <view class="subtext">已垫付 {{ item.paidDisplay }} · 应承担 {{ item.owedDisplay }}</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getTravel } from '../../utils/travel-store.js'

export default {
  data() {
    return {
      travelId: '',
      travel: null,
    }
  },
  onLoad(query) {
    this.travelId = query.travelId || ''
  },
  onShow() {
    this.refresh()
  },
  methods: {
    refresh() {
      const travel = getTravel(this.travelId)
      if (travel) {
        this.travel = travel
      }
    },
  },
}
</script>

<style>
@import "./settlement.wxss";
</style>
