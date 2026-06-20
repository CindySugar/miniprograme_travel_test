<template>
  <view class="index-page">
    <scroll-view class="home-page" scroll-y enhanced :show-scrollbar="false">
      <view class="home-shell">
        <view class="hero-card">
          <view class="hero-copy">
            <view class="hero-badge">一起出去玩，也要软软地算清。</view>
            <view class="hero-desc">邀请同行猫猫加入，大家各自记录垫付账单，最后自动算清。</view>
          </view>
          <view class="hero-illustration">
            <image class="hero-image" src="/static/travel-cat.png" mode="aspectFit"></image>
          </view>
        </view>

        <button class="create-entry" @tap="goCreateTravel">创建组队</button>
        <view class="entry-hint">加入队伍请打开好友发来的邀请卡片。</view>

        <view class="trip-header">
          <view class="trip-header-title">我的猫猫组队</view>
          <view class="trip-header-right">
            <text class="trip-header-meta">最近 {{ travels.length }} 个</text>
            <view class="trip-link">查看全部</view>
          </view>
        </view>

        <block v-if="travels.length">
          <view
            v-for="item in travels"
            :key="item.id"
            class="trip-card"
            @tap="openTravel(item.id)"
          >
            <view class="trip-card-top">
              <view>
                <view class="trip-card-kicker">猫猫组队 {{ item.displayDate }}</view>
                <view class="trip-card-title">{{ item.title }}</view>
              </view>
              <view class="trip-actions">
                <view class="trip-pill trip-pill-muted">归档</view>
                <view class="trip-pill trip-pill-warn">删除</view>
              </view>
            </view>

            <view class="trip-stats">
              <view class="trip-stat">总金额：¥{{ item.summary.totalSpentDisplay }}</view>
              <view class="trip-stat">{{ item.memberCount }} 只猫猫</view>
              <view class="trip-stat">{{ item.expenseCount }} 笔账单</view>
              <view class="trip-stat trip-status">{{ item.status }}</view>
            </view>

            <view class="trip-card-footer">
              <view class="member-stack">
                <view
                  v-for="member in item.visibleMembers"
                  :key="member.id"
                  class="member-badge"
                  :class="member.badgeClass"
                >{{ member.initial }}</view>
              </view>
              <view class="updated-at">{{ item.updatedAtDisplay }} 更新</view>
            </view>
          </view>
        </block>

        <view v-else class="trip-card trip-card-empty">
          <view class="trip-card-title">还没有旅行</view>
          <view class="trip-card-empty-text">点上面的按钮创建第一组旅行。</view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { listTravels } from '../../utils/travel-store.js'

export default {
  data() {
    return {
      travels: [],
    }
  },
  onShow() {
    this.travels = listTravels()
  },
  methods: {
    goCreateTravel() {
      uni.navigateTo({ url: '/pages/create/create' })
    },
    openTravel(id) {
      uni.navigateTo({ url: `/pages/logs/logs?travelId=${id}` })
    },
  },
}
</script>

<style>
@import "../../app.wxss";
@import "./index.wxss";
</style>
