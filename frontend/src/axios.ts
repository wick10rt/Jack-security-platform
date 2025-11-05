import axios from 'axios'

axios.defaults.baseURL = 'http://127.0.0.1:8000/api'

// 配置axios
// 取出 B1-登入驗證服務 分配的Token
const accessToken = localStorage.getItem('accessToken')
if (accessToken) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
}

export default axios
