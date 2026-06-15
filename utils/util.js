const formatTime = (date) => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

const formatDate = (value) => {
  const date = value instanceof Date ? value : new Date(value)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const formatMoney = (value) => {
  const number = Number(value || 0)
  return number.toFixed(2)
}

const roundMoney = (value) => {
  return Math.round((Number(value) + Number.EPSILON) * 100) / 100
}

const todayISO = () => {
  const date = new Date()
  return date.toISOString().slice(0, 10)
}

const formatNumber = (n) => {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

module.exports = {
  formatDate,
  formatMoney,
  formatTime,
  roundMoney,
  todayISO,
}
