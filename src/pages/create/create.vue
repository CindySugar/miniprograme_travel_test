<template>
  <view class="create-page">
    <cat-navigation-bar title="创建猫猫组队" :back="true" color="#2b343d" background="transparent" />
    <scroll-view class="create-scroll" scroll-y enhanced :show-scrollbar="false">
      <view class="hero-panel">
        <view class="hero-copy">
          <view class="hero-badge">新的出游账本</view>
          <view class="hero-title">给这次组队取个名字</view>
          <view class="hero-subtitle">一起出去玩，也要软软地算清。</view>
        </view>
        <image class="hero-image" src="/static/travel-cat.png" mode="aspectFit"></image>
      </view>

      <view class="tabs">
        <button class="tab" :class="{ 'tab-active': activeTab === 'team' }" hover-class="none" @tap="showTeamTab">组队</button>
        <button class="tab" :class="{ 'tab-active': activeTab === 'detail' }" hover-class="none" @tap="showDetailTab">详情</button>
        <button class="tab" :class="{ 'tab-active': activeTab === 'advanced' }" hover-class="none" @tap="showAdvancedTab">高级</button>
      </view>

      <view v-if="activeTab === 'team'" class="tab-panel">
        <view class="form-card team-card">
          <view class="field">
            <text class="label">组队标题</text>
            <input class="input" placeholder="比如海边晒太阳小分队" :value="form.title" @input="onInput" data-field="title" />
          </view>
          <view class="team-divider"></view>
          <view class="section-head">
            <view>
              <view class="team-title-row">
                <view class="section-title">队伍名单</view>
                <text class="tag">{{ members.length }} 只猫猫</text>
              </view>
              <view class="section-desc">先确认管理员，同行猫猫可继续添加</view>
            </view>
            <view class="head-tags">
              <text class="tag tag-green">{{ currentUser.openid ? '已登录' : '未登录' }}</text>
            </view>
          </view>

          <view class="owner-row">
            <button class="avatar-wrap" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
              <view class="avatar-dot">
                <image v-if="form.ownerAvatarUrl" class="avatar-image" :src="form.ownerAvatarUrl" mode="aspectFill"></image>
                <text v-else class="avatar-text">{{ ownerInitial }}</text>
              </view>
              <view class="avatar-btn">选头像</view>
            </button>
            <view class="owner-main">
              <text class="label">管理员昵称</text>
              <input
                v-if="!form.ownerName"
                class="input"
                type="nickname"
                placeholder="使用微信昵称"
                :value="form.ownerName"
                @input="onInput"
                @blur="onOwnerNameBlur"
                data-field="ownerName"
              />
              <input
                v-else
                class="input"
                type="text"
                placeholder="使用微信昵称"
                :value="form.ownerName"
                @input="onInput"
                @blur="onOwnerNameBlur"
                data-field="ownerName"
              />
            </view>
          </view>

          <view class="helper-text team-hint">建议先把这次同行猫猫都加进名单，记账时就能直接选择分摊人。</view>

          <view class="add-member">
            <input class="input add-input" placeholder="输入同行猫猫昵称" :value="newMemberName" @input="onMemberInput" />
            <button class="add-btn" @tap="addPreviewMember">添加</button>
          </view>

          <view class="team-divider"></view>
          <view class="section-head family-head">
            <view class="team-title-row">
              <view class="section-title">猫猫家庭</view>
              <view class="section-desc inline-desc">结算时按家庭合并转账</view>
            </view>
          </view>
          <view class="family-preview">添加同行猫猫后，可以提前把同一个家庭组合好。</view>
        </view>
      </view>

      <view v-else-if="activeTab === 'detail'" class="tab-panel">
        <view class="form-card detail-card">
          <view class="section-head">
            <view>
              <view class="section-title">账本详情</view>
              <view class="section-desc">这些都不是创建必填项，可稍后在设置里修改。</view>
            </view>
          </view>

          <view class="field">
            <text class="label">活动日期</text>
            <picker mode="date" :value="form.startDate" @change="onInput" data-field="startDate">
              <view class="picker-field">{{ displayStartDate || '6月15日' }}</view>
            </picker>
          </view>

          <view class="field">
            <text class="label">地点/备注</text>
            <textarea class="textarea" placeholder="比如周末去海边，顺路吃下午茶" :value="form.destination" @input="onInput" data-field="destination"></textarea>
          </view>
        </view>
      </view>

      <view v-else class="tab-panel">
        <view class="inline-section-head advanced-head">
          <view class="section-title">账务规则</view>
          <view class="section-meta">创建后可修改</view>
        </view>

        <view class="form-card rules-card">
          <view class="field">
            <text class="label">每只猫猫预收金额</text>
            <input class="input" type="digit" placeholder="比如 1000" :value="form.advanceAmount" @input="onInput" data-field="advanceAmount" />
            <view class="helper-text">默认由管理员统一收取和保管。结算时会计入每只猫猫的已付款，多退少补。如中途统一追加预收款，直接改为累计金额即可。</view>
          </view>

          <view class="field">
            <text class="label">猫猫基金</text>
            <input class="input" placeholder="如打牌充公、共同活动基金" :value="form.catFund" @input="onInput" data-field="catFund" />
            <view class="helper-text">默认由管理员保管。结算时会公平抵扣大家的分摊金额，并合并进最终转账建议。</view>
          </view>
        </view>

        <view class="inline-section-head permission-head">
          <view class="section-title">协作权限</view>
          <view class="section-meta">创建后可修改</view>
        </view>

        <view class="permission-list">
          <view class="permission-item">
            <view class="permission-copy">
              <view class="permission-title">允许普通成员管理猫猫家庭</view>
              <view class="permission-desc">默认开启，成员也能调整猫猫家庭</view>
            </view>
            <switch :checked="permissions.allowMemberFamilyEdit" color="#72c7a7" @change="togglePermission" data-field="allowMemberFamilyEdit" />
          </view>
          <view class="permission-item">
            <view class="permission-copy">
              <view class="permission-title">允许被邀请人创建新身份</view>
              <view class="permission-desc">默认开启，关闭时只能认领上方名单里的身份</view>
            </view>
            <switch :checked="permissions.allowInvitedIdentity" color="#72c7a7" @change="togglePermission" data-field="allowInvitedIdentity" />
          </view>
          <view class="permission-item permission-item-muted">
            <view class="permission-copy">
              <view class="permission-title">加入/创建时必须上传头像</view>
              <view class="permission-desc">默认关闭，开启后新身份和认领身份都要选择微信头像</view>
            </view>
            <switch :checked="permissions.requireAvatar" color="#72c7a7" @change="togglePermission" data-field="requireAvatar" />
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="bottom-bar">
      <button class="create-submit" @tap="createTravel">建好队伍，邀请同行</button>
      <view class="bottom-note">创建后先发给同行猫猫，详情和权限可先跳过。</view>
    </view>
  </view>
</template>

<script>
import { createTravel as storeCreateTravel, getCurrentUser } from '../../utils/travel-store.js'
import { formatDate, todayISO } from '../../utils/util.js'
import NavigationBar from '../../components/cat-navigation-bar/cat-navigation-bar.vue'

const decorateMember = (member) => ({
  ...member,
  initial: (member.name || '猫').slice(0, 1),
})

export default {
  components: { NavigationBar },
  data() {
    return {
      activeTab: 'team',
      currentUser: getCurrentUser(),
      newMemberName: '',
      permissions: {
        allowMemberFamilyEdit: true,
        allowInvitedIdentity: true,
        requireAvatar: false,
      },
      form: {
        title: '',
        destination: '',
        ownerName: '',
        ownerAvatarUrl: '',
        startDate: '',
        advanceAmount: '',
        catFund: '',
      },
      members: [],
      displayStartDate: '',
      ownerInitial: '猫',
    }
  },
  onShow() {
    const currentUser = getCurrentUser()
    const ownerName = this.form.ownerName || ''
    const ownerAvatarUrl = this.form.ownerAvatarUrl || currentUser.avatarUrl || ''
    const previewOwnerName = ownerName || '使用微信昵称'
    const startDate = this.form.startDate || todayISO()
    this.currentUser = currentUser
    this.form.ownerName = ownerName
    this.form.ownerAvatarUrl = ownerAvatarUrl
    this.form.startDate = startDate
    this.displayStartDate = formatDate(startDate)
    this.ownerInitial = (ownerName || '管').slice(0, 1)
    this.members = this.members.length
      ? this.members
      : [decorateMember({ id: 'owner_preview', name: previewOwnerName, avatarUrl: ownerAvatarUrl, isOwner: true })]
  },
  methods: {
    showTeamTab() {
      this.activeTab = 'team'
    },
    showDetailTab() {
      this.activeTab = 'detail'
    },
    showAdvancedTab() {
      this.activeTab = 'advanced'
    },
    onInput(e) {
      const { field } = e.currentTarget.dataset
      const value = e.detail.value || ''
      this.form[field] = value
      if (field === 'ownerName') {
        this.ownerInitial = (value || '猫').slice(0, 1)
        this.members = this.members.map((member) => (member.isOwner ? decorateMember({ ...member, name: value || '使用微信昵称' }) : member))
      }
      if (field === 'startDate') {
        this.displayStartDate = formatDate(value || todayISO())
      }
    },
    onOwnerNameBlur(e) {
      const value = e.detail.value || ''
      this.form.ownerName = value
      this.ownerInitial = (value || '猫').slice(0, 1)
      this.members = this.members.map((member) => (member.isOwner ? decorateMember({ ...member, name: value || '使用微信昵称' }) : member))
    },
    onMemberInput(e) {
      this.newMemberName = e.detail.value
    },
    onChooseAvatar(e) {
      const { avatarUrl } = e.detail
      if (!avatarUrl) return
      this.form.ownerAvatarUrl = avatarUrl
      this.members = this.members.map((member) => (member.isOwner ? decorateMember({ ...member, avatarUrl }) : member))
    },
    addPreviewMember() {
      const name = (this.newMemberName || '').trim()
      if (!name) {
        uni.showToast({ title: '请输入同行猫猫昵称', icon: 'none' })
        return
      }
      const exists = this.members.some((member) => member.name === name)
      if (exists) {
        uni.showToast({ title: '这只猫猫已在队伍里', icon: 'none' })
        return
      }
      this.members = this.members.concat({
        id: `preview_${Date.now()}`,
        name,
        isOwner: false,
      }).map(decorateMember)
      this.newMemberName = ''
    },
    togglePermission(e) {
      const { field } = e.currentTarget.dataset
      this.permissions[field] = e.detail.value
    },
    createTravel() {
      const { title, destination, ownerName, ownerAvatarUrl, startDate } = this.form
      if (!title.trim()) {
        uni.showToast({ title: '请输入组队名称', icon: 'none' })
        return
      }
      const travel = storeCreateTravel({
        title,
        destination,
        ownerName,
        ownerAvatarUrl,
        startDate,
        members: this.members.filter((member) => !member.isOwner).map((member) => ({ name: member.name })),
      })
      uni.showToast({ title: '队伍已创建', icon: 'success' })
      uni.redirectTo({ url: `/pages/logs/logs?travelId=${travel.id}` })
    },
  },
}
</script>

<style>
@import "../../../pages/create/create.wxss";
</style>
