<template>
  <view class="weui-navigation-bar" :class="extClass">
    <view
      class="weui-navigation-bar__inner"
      :class="ios ? 'ios' : 'android'"
      :style="{
        color,
        background,
        ...displayStyle,
        ...innerPaddingRight,
        ...safeAreaTop,
      }"
    >
      <view class="weui-navigation-bar__left" :style="leftWidth">
        <template v-if="back || homeButton">
          <view v-if="back" class="weui-navigation-bar__buttons weui-navigation-bar__buttons_goback">
            <view
              class="weui-navigation-bar__btn_goback_wrapper"
              hover-class="weui-active"
              hover-stay-time="100"
              aria-role="button"
              aria-label="返回"
              @tap="backPage"
            >
              <view class="weui-navigation-bar__button weui-navigation-bar__btn_goback"></view>
            </view>
          </view>
        </template>
        <template v-else>
          <slot name="left"></slot>
        </template>
      </view>

      <view class="weui-navigation-bar__center">
        <view v-if="loading" class="weui-navigation-bar__loading" aria-role="alert">
          <view class="weui-loading" aria-role="img" aria-label="加载中"></view>
        </view>
        <text v-if="title">{{ title }}</text>
        <slot v-else name="center"></slot>
      </view>

      <view class="weui-navigation-bar__right">
        <slot name="right"></slot>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CatNavigationBar',
  props: {
    extClass: { type: String, default: '' },
    title: { type: String, default: '' },
    background: { type: String, default: '' },
    color: { type: String, default: '' },
    back: { type: Boolean, default: true },
    loading: { type: Boolean, default: false },
    homeButton: { type: Boolean, default: false },
    animated: { type: Boolean, default: true },
    show: { type: Boolean, default: true },
    delta: { type: Number, default: 1 },
  },
  data() {
    return {
      ios: true,
      displayStyle: {},
      innerPaddingRight: {},
      leftWidth: {},
      safeAreaTop: {},
    }
  },
  watch: {
    show: {
      immediate: true,
      handler(value) {
        this._showChange(value)
      },
    },
  },
  mounted() {
    const rect = wx.getMenuButtonBoundingClientRect()
    wx.getSystemInfo({
      success: (res) => {
        const isAndroid = res.platform === 'android'
        const isDevtools = res.platform === 'devtools'
        this.ios = !isAndroid
        this.innerPaddingRight = { paddingRight: `${res.windowWidth - rect.left}px` }
        this.leftWidth = { width: `${res.windowWidth - rect.left}px` }
        this.safeAreaTop = isDevtools || isAndroid
          ? { height: `calc(var(--height) + ${res.safeArea.top}px)`, paddingTop: `${res.safeArea.top}px` }
          : {}
      },
    })
  },
  methods: {
    _showChange(show) {
      if (this.animated) {
        this.displayStyle = {
          opacity: show ? '1' : '0',
          transition: 'opacity 0.5s',
        }
      } else {
        this.displayStyle = { display: show ? '' : 'none' }
      }
    },
    backPage() {
      if (this.delta) {
        wx.navigateBack({ delta: this.delta })
      }
      this.$emit('back', { delta: this.delta })
    },
  },
}
</script>

<style>
@import "./cat-navigation-bar.wxss";
</style>
