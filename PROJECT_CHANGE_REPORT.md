# Project Change Report

## Overview
This report documents the changes made to the research pipeline project in the current workspace. The project is a multi-agent research application that combines web search, content extraction, report generation, evaluation, and a browser-based user interface.

The work focused on improving reliability, usability, maintainability, and the user experience of the research workflow.

## 1. Project Structure Reviewed
The project contains the core backend files and a React frontend:

- `agents.py` — defines the search agent, reader agent, writer prompt, and critic prompt
- `api_server.py` — FastAPI backend that streams each stage of the research pipeline
- `pipeline.py` — script-based terminal pipeline flow
- `tools.py` — Tavily search and URL scraping utilities
- `requirements.txt` — Python dependency manifest
- `research-ui/` — React + Vite frontend for displaying the pipeline and final output

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

## 3. Additional Enhancements to the Writer and Critic Workflow
The prompt behavior was improved to make the output more useful for citation-friendly research work.

Changes made:
- Added a “Comparison or Insights” section in the writer prompt
- Added guidance to make the response professionally structured and easy to cite
- Improved the critic prompt role description
- Made the final output more readable and trustworthy for users

Files changed:
- `agents.py`

## 4. Validation Performed
To confirm the frontend still works after the changes, the project was validated using a production build.

Command used:
- `npm install`
- `npm run build`

Result:
- Build completed successfully
- No blocking frontend errors were found during the build process

## 5. Overall Assessment
The project started as a strong research prototype and was improved into a more usable, understandable, and user-friendly research workflow.

The strongest improvements include:
- better local setup configuration
- clearer documentation and comments
- more reliable output generation
- source visibility
- final result export options
- recent research history

These changes significantly improve the project’s usability and make it easier to extend in future work.

## 6. Recommended Next Enhancements
The following are logical next steps for future work:

1. Add source credibility scoring
2. Add multi-source comparison mode
3. Support citation-style references in the report output
4. Add PDF/Markdown export options
5. Improve the scraper with retries and browser-based extraction
6. Add user authentication and saved workspaces
7. Add backend job persistence for long-running research tasks

## 7. Conclusion
The project is now better organized, easier to run, easier to understand, and more useful as a research tool. The changes made in the workspace improve both the technical quality and the user-facing experience, while also preparing the project for future feature expansion.
