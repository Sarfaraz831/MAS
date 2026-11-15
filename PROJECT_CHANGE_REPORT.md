# Project Change Report

## Overview
This report documents the changes made to the research pipeline project in the current workspace. The project is a multi-agent research application with web research, source extraction, report generation, evaluation, and a browser-based UI. It now also includes a separate chatbot for normal conversations and questions about web pages or PDFs.

The work focused on improving reliability, usability, maintainability, and the user experience of the research workflow.

## 1. Project Structure Reviewed
The project contains the core backend files and a React frontend:

- `agents.py` — defines the search agent, reader agent, writer prompt, and critic prompt
- `api_server.py` — FastAPI backend that streams each stage of the research pipeline
- `document_chat.py` — URL/PDF text extraction, source limits, copyright indicators, and safety keyword checks
- `pipeline.py` — script-based terminal pipeline flow
- `tools.py` — Tavily search and URL scraping utilities
- `requirements.txt` — Python dependency manifest
- `research-ui/src/App.jsx` — navigation between the research pipeline and document chat
- `research-ui/src/DocumentChat.jsx` — document ingestion and chat interface
- `research-ui/` — React + Vite frontend

## 2. Key Improvements Made

### 2.1 Frontend API configuration fix
The React frontend originally used a hardcoded remote API URL, which made local development and deployment inconsistent.

Changes made:
- Switched the frontend to use `VITE_API_BASE`
- Added a fallback to `http://localhost:8000`
- Added `.env.example` in the frontend folder
- Updated documentation to describe the proper local configuration

Why this matters:
- Local development works as expected
- Deployments can override the backend URL without editing source code
- Documentation matches the actual app behavior

Files changed:
- `research-ui/src/ResearchUI.jsx`
- `research-ui/.env.example`
- `research-ui/README.md`

### 2.2 Better code documentation
The project now includes clearer inline code comments to explain what each major feature does.

Examples:
- API config behavior
- multi-stage pipeline workflow
- search agent purpose
- scraper purpose
- writer and critic responsibilities
- source extraction and final report actions

Why this matters:
- Easier onboarding for new developers
- Better readability and maintainability
- Clear understanding of how each feature contributes to the research flow

Files changed:
- `research-ui/src/ResearchUI.jsx`
- `agents.py`
- `api_server.py`
- `tools.py`

### 2.3 Search and scrape reliability improvements
The tool layer was enhanced so it handles output more safely and returns more useful content.

Changes made:
- Added safer extraction of search results
- Added default values for missing data
- Truncated text is cleaned and normalized
- Scraped results now include page title and source URL
- Script/style/footer clutter is removed before returning text
- Search and scraping logic is explained clearly in code comments

Why this matters:
- Better output quality for later report generation
- Lower risk of broken parsing when a result is incomplete
- More usable data for the writer agent and final UI

Files changed:
- `tools.py`

### 2.4 Source extraction and source visibility
The system now extracts unique URLs from search and scraped content and includes them in the result state.

Changes made:
- Added URL extraction helper in the API layer
- Combined search sources and scraped sources into one unique list
- Sent source data to the frontend alongside the final report

Why this matters:
- Makes the resulting report more traceable
- Improves source transparency
- Helps users verify claims and trust the generated output

Files changed:
- `api_server.py`
- `research-ui/src/ResearchUI.jsx`

### 2.5 Final report actions in the UI
The frontend was improved with direct output actions for users.

Added features:
- Copy report to clipboard
- Download report as `.txt`
- Display final research summary in a dedicated section
- Show all discovered sources as clickable links

Why this matters:
- Users can easily save or share the output
- The app feels more like a finished research tool rather than a demo
- This improves productivity and user experience

Files changed:
- `research-ui/src/ResearchUI.jsx`

### 2.6 Recent research history feature
A browser-side history system was added so users can access previous results without rerunning the pipeline.

Changes made:
- Saved recent research records in `localStorage`
- Stored topic, report text, source list, and timestamp
- Added a “Recent research” panel in the UI
- Included a “Clear” button to remove history
- Clicking an item restores the previous result in the interface

Why this matters:
- Makes the app more practical for repeated investigations
- Reduces repeated costs and latency
- Provides a simple local research archive

Files changed:
- `research-ui/src/ResearchUI.jsx`

### 2.7 Document chatbot, URL/PDF ingestion, and checks
A second UI view was added for general chat and document-based questions.

Added features:
- Load public HTTP/HTTPS web pages, plain text pages, and linked PDFs
- Upload text-based PDFs (up to 8 MB and 100 pages)
- Extract document text and preserve source title and URL or PDF page markers
- Ask follow-up questions or request a document summary
- Continue normal chat without attaching a document
- Display copyright/license notice indicators and safety keyword warnings
- Reject local/private-network URLs and redirects; reject unsupported or unreadable PDFs

The checks are deliberately advisory:
- Copyright indicators are heuristic notice/license matches, not a rights clearance or legal opinion
- Safety checks use configured keyword patterns, can miss or over-flag content, and do not block the user
- Scanned PDFs without selectable text require OCR, which is not included

Files changed:
- `api_server.py`
- `document_chat.py`
- `requirements.txt` (`pypdf` for PDF text extraction)
- `research-ui/src/App.jsx`
- `research-ui/src/DocumentChat.jsx`
- `research-ui/src/main.jsx`
- `research-ui/src/ResearchUI.jsx`
- `research-ui/README.md`
- `tests/test_document_chat.py`

## 3. Additional Enhancements to the Writer and Critic Workflow
The prompt behavior was improved to make the output more useful for citation-friendly research work.

Changes made:
- Added a “Comparison or Insights” section in the writer prompt
- Added guidance to make the response professionally structured and easy to cite
- Improved the critic prompt role description
- Made the final output more readable and trustworthy for users

Files changed:
- `agents.py`

## 4. Document Chat and LLM Integration

The chatbot uses the same model instance configured in `agents.py`; it does not introduce a separate model. The current configuration creates a `ChatGroq` model using `openai/gpt-oss-120b`. The actual provider/model can be changed in that module, and the required provider credentials must be available to the backend.

### Request flow
1. The React chat view sends a URL to `POST /api/chat/source/url` or a PDF to `POST /api/chat/source/pdf`.
2. FastAPI calls the extraction helpers in `document_chat.py`. Extraction and copyright/safety scans run locally in the backend; the LLM is not called during source loading.
3. The backend returns extracted text, source details, and check results to the UI. The UI shows the notices and warnings.
4. When the user sends a chat message, the UI posts the conversation and (if attached) the extracted source text to `POST /api/chat`.
5. The backend selects relevant passages, adds them and recent conversation messages to a system/user/assistant message list, and calls the configured model using `llm.invoke(...)`.
6. The answer is checked for configured safety keywords and returned with any warnings. The UI displays the answer and flags; warnings do not prevent the response.

With no source attached, the request goes to the same LLM as ordinary chat, without document context. With a source attached, the model receives selected excerpts plus its title and URL (or PDF page markers). Document text is treated as untrusted reference material in the system instructions.

### Current retrieval and limitations
The current passage selection is a lightweight, keyword-based approach in `api_server.py`; it splits the extracted text into overlapping character chunks and chooses chunks based on terms in the question. It is **not yet full semantic RAG**: the project does not currently generate embeddings or store chunks in a vector database. The UI sends the extracted source text with each chat request, and the backend caps the selected model context.

For long-document summaries, the code samples passages across the document; it may not capture every detail. Scanned PDFs, persistent document indexes, and multi-user chat storage are not supported.

Because prompts and selected document passages are passed to the configured LLM provider, those contents leave the application backend for model processing. Configure the provider and data handling policy accordingly.

## 5. Validation Performed
The recent chatbot changes were validated with:

- `npm run build` in `research-ui/`
- `.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Python compile checks for the backend and tests
- API smoke tests with a stub LLM (chat returned successfully; a private URL and invalid PDF were rejected)

Result:
- The frontend production build completed successfully
- All 7 backend unit tests passed
- API smoke tests passed without making an external model call

## 6. Overall Assessment
The project started as a strong research prototype and was improved into a more usable, understandable, and user-friendly research workflow.

The strongest improvements include:
- better local setup configuration
- clearer documentation and comments
- more reliable output generation
- source visibility
- final result export options
- recent research history
- source-aware chat for web pages and text-based PDFs
- advisory copyright and safety indicators

These changes significantly improve the project’s usability and make it easier to extend in future work.

## 7. Recommended Next Enhancements
The following are logical next steps for future work:

1. Replace keyword passage selection with embeddings and a vector store for semantic RAG
2. Add citations linking chatbot claims to exact source pages/passages
3. Add OCR support for scanned PDFs
4. Add persistent document/chat storage with user isolation and deletion controls
5. Improve URL extraction for JavaScript-heavy pages and add source credibility scoring
6. Add multi-source comparison and citation-style report output
7. Add PDF/Markdown export options and backend job persistence for long-running research tasks

## 8. Conclusion
The project is now better organized, easier to run, easier to understand, and more useful as a research tool. The changes made in the workspace improve both the technical quality and the user-facing experience, while also preparing the project for future feature expansion.
