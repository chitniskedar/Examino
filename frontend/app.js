// app.js — Examino frontend helpers & shared utilities
// The main logic lives in index.html for single-file simplicity.
// Add reusable helpers here as the project grows.

/**
 * Format a number as a percentage string.
 * @param {number} val - value between 0–100
 * @returns {string}
 */
export function formatPct(val) {
  if (val == null || isNaN(val)) return '—';
  return `${Number(val).toFixed(1)}%`;
}
const API = window.location.protocol === 'file:'
  ? 'http://localhost:8000'
  : window.location.origin;
/**
 * Truncate a string to maxLen characters.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
export function truncate(str, maxLen = 80) {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

/**
 * Debounce a function call.
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Simple local storage wrapper with JSON support.
 */
export const store = {
  get: (key, fallback = null) => {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
    catch { return fallback; }
  },
  set: (key, val) => {
    try { localStorage.setItem(key, JSON.stringify(val)); }
    catch {}
  },
  remove: (key) => localStorage.removeItem(key),
};

/**
 * API base URL — change this if you deploy the backend remotely.
 */
export const API_BASE = 'http://localhost:8000';

/**
 * Fetch wrapper that throws a readable error on non-2xx responses.
 * @param {string} path - API path, e.g. '/questions'
 * @param {RequestInit} opts
 */
export async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}