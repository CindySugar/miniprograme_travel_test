const store = require('../../utils/travel-store.js')

Page({
  data: {
    travel: null,
  },
  onLoad(query) {
    if (query.travelId) {
      this.refresh(query.travelId)
    }
  },
  refresh(travelId) {
    const travel = store.getTravel(travelId)
    if (travel) {
      this.setData({ travel })
    }
  },
})
