// src/api/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', // 指向我们Python后端的API根路径
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;