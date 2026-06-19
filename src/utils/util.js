export const formatTime = (date) => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

export const formatDate = (value) => {
  const date = value instanceof Date ? value : new Date(value)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

export const formatMoney = (value) => {
  const number = Number(value || 0)
  return number.toFixed(2)
}

export const roundMoney = (value) => Math.round((Number(value) + Number.EPSILON) * 100) / 100

export const todayISO = () => new Date().toISOString().slice(0, 10)

const formatNumber = (n) => {
  const text = `${n}`
  return text[1] ? text : `0${text}`
}
