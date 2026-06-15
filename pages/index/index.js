const store = require('../../utils/travel-store.js')

Page({
  data: {
    currentUser: store.getCurrentUser(),
    travels: [],
  },
  onShow() {
    this.setData({
      currentUser: store.getCurrentUser(),
      travels: store.listTravels(),
    })
  },
  goCreateTravel() {
    wx.navigateTo({
      url: '/pages/create/create',
    })
  },
  openTravel(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/logs/logs?travelId=${id}`,
    })
  },
})
