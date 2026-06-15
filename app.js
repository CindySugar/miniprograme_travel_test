const store = require('./utils/travel-store.js')

App({
  onLaunch() {
    store.ensureState()
    wx.login({
      success: () => {
        // 后端接入后，这里会把 code 交换成 openid/session。
      },
    })
  },
  globalData: {
    currentUser: store.getCurrentUser(),
  },
})
