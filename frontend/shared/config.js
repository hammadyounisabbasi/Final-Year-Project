(function configureAcos() {
  // Set this to the public FastAPI origin when frontend and API use different hosts.
  // Example: "https://acos-api.example.com"
  const DEPLOYED_API_BASE_URL = "";
  const host = window.location.hostname;
  const isLocal = !host || host === "localhost" || host === "127.0.0.1";

  // For a separate production API, set window.ACOS_API_BASE_URL before this
  // script loads. Same-origin deployments need no override.
  const configured = String(window.ACOS_API_BASE_URL || DEPLOYED_API_BASE_URL).trim();
  const apiBaseUrl = (configured || (isLocal ? "http://127.0.0.1:8000" : window.location.origin))
    .replace(/\/$/, "");

  window.ACOS_CONFIG = Object.freeze({ API_BASE_URL: apiBaseUrl });
  window.API_BASE_URL = apiBaseUrl;
  window.EXAM_API_BASE_URL = apiBaseUrl;
  window.TIMETABLE_API_BASE_URL = apiBaseUrl;
})();
