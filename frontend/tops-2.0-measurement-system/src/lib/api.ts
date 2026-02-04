/**
 * API configuration for both production (same-origin) and development (separate servers) modes.
 *
 * Production: Frontend is served by FastAPI, so all URLs are relative (same origin).
 * Development: Frontend runs on localhost:3000, backend on localhost:8000.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL ||
  `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}`;
