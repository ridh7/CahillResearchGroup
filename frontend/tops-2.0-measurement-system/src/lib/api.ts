/**
 * API configuration for both production (same-origin) and development (separate servers) modes.
 *
 * Production: Frontend is served by FastAPI, so all URLs are relative (same origin).
 * Development: Frontend runs on localhost:3000, backend on localhost:8000.
 *   Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.development.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
