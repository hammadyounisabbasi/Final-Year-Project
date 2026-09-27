# Connected library

The admin and student library pages use the authenticated `/library` API. The existing six PDFs have been imported into the shared `Library` table. Start or restart the existing FastAPI application after updating the code:

```powershell
cd backend/backend
../../venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Sign in normally, then open the Library page in either portal. The pages use the existing local API address (127.0.0.1:8000); deployments may set `window.API_BASE_URL` before loading `library.js`.

## Books

Admins upload a PDF (maximum 50 MB) with title, author, category, keywords and description. Files receive unique filenames inside `frontend/Admin_dashboard/Books`; metadata is saved in `Library`. Student catalogs read the same database and refresh every 30 seconds or when the window regains focus. `Import Books folder` imports PDFs copied into the folder manually; startup also imports them. Importing is idempotent by stored filename. Existing author/category metadata is not guessed from filenames.

The additive startup migration creates `Library_Activity` without clearing existing catalog or borrowing records. Existing physical borrowing endpoints remain available. The new portal focuses on the shared digital collection.

All library API routes require authentication. Upload, folder import, and analytics require an admin. Downloads only serve PDFs resolved inside the Books directory. Student requests are attributed to the authenticated user, with department captured from the student record. Do not expose the Books directory directly in a production static server: students should download through the authenticated API so requests are tracked.

## Analytics

Reports include per-book download requests and distinct downloaders, searches and chat questions (including unmatched demand), detail views, department/book combinations, student/book combinations, and recent activity. Period selection applies to activity; available-book count reflects the current catalog. UTC is used for event times.

Interest is an explicitly labeled proxy: 3 points per download request, 2 per detail view, and 1 per matching search result (up to 20 books per search). A returned match is not a confirmed preference. Download counts measure requests served, not confirmation that the browser saved the complete file. Activity begins after this feature is enabled; historical file downloads cannot be reconstructed. Admin actions do not count as student interest. The dashboard labels its 500-combination and 300-recent-event display limits.

## Assistant and external discovery

The assistant calls the existing `AIProviderManager`: Groq -> Gemini -> Hugging Face -> Ollama -> catalog response if all fail. Existing environment keys and provider settings are reused. It receives catalog metadata, bounded conversation history and live source evidence; it does not read complete PDF contents. No student identity is sent with discovery queries. Questions and searches are visible to admins, as disclosed on the student page.

Discovery queries public DuckDuckGo HTML search, Wikipedia overview search and Crossref journal-article metadata in parallel, with bounded reads and timeouts. Returned links are rendered separately from model prose. Google Scholar and YouTube destinations are explicitly labeled as search links, not retrieved papers or videos. External search availability can vary; an outage produces an explicit message and usable search destinations. Publisher links may require subscriptions.

API reference: [Crossref search and filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).

## Validation

`venv/Scripts/python.exe -m unittest discover -s tests/api -p test_library.py -v`

Six integration tests passed with isolated database/files: upload/shared catalog, distinct/repeated downloads and department counts, role restrictions, unavailable files/path confinement, idempotent import, conversation fallback/history, search outage and link parsing.

`tmp/browser_library.py` verifies admin upload -> student catalog -> details -> PDF download -> external search -> chat, and desktop/tablet/mobile layout and mobile navigation. Browser external discovery and AI responses are controlled fixtures; live Crossref and Wikipedia discovery were separately verified. AI provider availability depends on the existing runtime configuration. Screenshots are saved as `tmp/library-*.png`.
