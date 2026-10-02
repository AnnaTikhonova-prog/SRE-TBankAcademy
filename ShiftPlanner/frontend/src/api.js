import axios from 'axios';

// Ключ, под которым JWT хранится в localStorage.
export const TOKEN_KEY = 'shiftplanner_token';

// Базовый URL API. В Docker задаётся через VITE_API_URL на этапе сборки
// (по умолчанию '/api' — nginx проксирует этот префикс на бэкенд).
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

// Подставляем JWT в каждый запрос.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// При 401 токен недействителен: чистим хранилище и уведомляем приложение.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event('auth:logout'));
    }
    return Promise.reject(error);
  },
);

// Достаёт человекочитаемый текст ошибки из ответа FastAPI.
export function errorText(error) {
  const detail = error?.response?.data?.detail;
  if (!detail) return 'Нет соединения с сервером';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || d.message || JSON.stringify(d)).join('; ');
  }
  return String(detail);
}

// Названия дней недели (0 — понедельник, как в API).
export const WEEKDAYS = [
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
  'Воскресенье',
];

// 'HH:MM:SS' -> 'HH:MM'
export const shortTime = (t) => (t ? String(t).slice(0, 5) : '');

// '2026-05-04' -> '04.05.2026'
export const formatDate = (d) => (d ? String(d).split('-').reverse().join('.') : '');

export default api;
