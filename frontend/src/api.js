/**
 * API helper utilities for AI Dietitian frontend.
 * Backend: http://localhost:8000
 */

const BASE_URL = 'http://localhost:8000';

/**
 * POST JSON to an endpoint. Returns parsed JSON or null on failure.
 * Uses 600 000 ms timeout for /generate-meal-plan, 180 000 ms otherwise.
 */
export async function postJSON(endpoint, body) {
  const url = `${BASE_URL}${endpoint}`;
  const timeout = endpoint.includes('/generate-meal-plan') ? 600000 : 180000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`Server ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    const msg = err.name === 'AbortError'
      ? `Request timed out after ${timeout / 1000}s — ${endpoint}`
      : `Request failed — ${endpoint}: ${err.message}`;
    console.error(msg, err);
    alert(msg);
    return null;
  }
}

/**
 * POST a file via multipart/form-data. Returns parsed JSON or null.
 */
export async function postFile(endpoint, file, field = 'file') {
  const url = `${BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 180000);

  try {
    const formData = new FormData();
    formData.append(field, file);

    const res = await fetch(url, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`Server ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    const msg = err.name === 'AbortError'
      ? `File upload timed out — ${endpoint}`
      : `File upload failed — ${endpoint}: ${err.message}`;
    console.error(msg, err);
    alert(msg);
    return null;
  }
}

/**
 * POST a file with additional form-data fields. Returns parsed JSON or null.
 */
export async function postFileWithData(endpoint, file, field, data) {
  const url = `${BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 180000);

  try {
    const formData = new FormData();
    formData.append(field, file);
    if (data && typeof data === 'object') {
      for (const [key, value] of Object.entries(data)) {
        formData.append(key, value);
      }
    }

    const res = await fetch(url, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`Server ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    const msg = err.name === 'AbortError'
      ? `Upload timed out — ${endpoint}`
      : `Upload failed — ${endpoint}: ${err.message}`;
    console.error(msg, err);
    alert(msg);
    return null;
  }
}

/**
 * GET JSON from an endpoint. Returns parsed JSON or null.
 */
export async function getJSON(endpoint) {
  const url = `${BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 180000);

  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);

    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`Server ${res.status}: ${errText}`);
    }
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    const msg = err.name === 'AbortError'
      ? `Request timed out — ${endpoint}`
      : `Request failed — ${endpoint}: ${err.message}`;
    console.error(msg, err);
    alert(msg);
    return null;
  }
}

/**
 * Escape HTML entities to prevent XSS when inserting user content.
 */
export function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return str.replace(/[&<>"']/g, (ch) => map[ch]);
}
