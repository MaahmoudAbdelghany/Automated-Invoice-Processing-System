# Task Checklist — Automated Invoice Processing System (Arabic-First)

## 1. Project Scaffolding (Backend)
- [x] Create backend directory structure (`src/`)
- [x] Create `requirements.txt`
- [x] Create `.env.example`
- [x] Create `src/config.py`
- [x] Create backend `__init__.py` files

## 2. Arabic Preprocessing Module (الوحدة الرئيسية)
- [x] `src/arabic/numerals.py` — Eastern Arabic ↔ Western numeral conversion
- [ ] `src/arabic/normalizer.py` — Arabic text normalization (hamza, tashkeel)
- [ ] `src/arabic/hijri.py` — Hijri date detection & Gregorian conversion
- [ ] `src/arabic/field_mapper.py` — Arabic field label → schema field mapping
- [ ] `src/arabic/currencies.py` — MENA currency detection
- [ ] `src/arabic/preprocessor.py` — Unified Arabic preprocessing pipeline

## 3. OCR Module
- [ ] `src/ocr/textract_client.py` — Textract AnalyzeExpense + AnalyzeDocument
- [ ] `src/ocr/ocr_tool.py` — LangChain Tool wrapper

## 4. NLP Module
- [ ] `src/nlp/bedrock_client.py` — Bedrock Claude 3.5 Sonnet client
- [ ] `src/nlp/prompts.py` — Arabic-first prompt templates
- [ ] `src/nlp/extractor_tool.py` — LangChain Tool wrapper

## 5. Validation Module
- [ ] `src/validation/rules.py` — 6 validation rules with bilingual messages
- [ ] `src/validation/validation_tool.py` — LangChain Tool wrapper

## 6. Confidence Scoring
- [ ] `src/utils/confidence.py` — Composite confidence scoring
- [ ] `src/utils/logging.py` — Structured logging

## 7. Storage Module
- [ ] `src/storage/dynamodb_client.py` — DynamoDB operations
- [ ] `src/storage/s3_client.py` — S3 operations
- [ ] `src/storage/export.py` — JSON/CSV export

## 8. Notification & Localization
- [ ] `src/notification/ses_client.py` — Arabic-first SES emails
- [ ] `src/localization/templates_ar.py` — Arabic email templates
- [ ] `src/localization/templates_en.py` — English fallback templates

## 9. Agent Orchestration & Handlers
- [ ] `src/agent/state.py` — Agent state schema
- [ ] `src/agent/tools.py` — Tool registry
- [ ] `src/agent/graph.py` — LangGraph workflow
- [ ] `src/handler.py` — S3 Trigger Lambda entry point
- [ ] `src/api_handler.py` — API Gateway Lambda entry point (Frontend API)

## 10. AWS SAM Template (IaC)
- [ ] `template.yaml` — AWS Resources (Lambda, DynamoDB, API Gateway, S3)
- [ ] `samconfig.toml` — Deployment config

## 11. Frontend Scaffolding & Setup (React + Vite)
- [ ] Initialize Vite project (`frontend/`)
- [ ] Install dependencies (React Router, Tailwind CSS, Axios)
- [ ] Configure Tailwind CSS for RTL (Right-to-Left) support
- [ ] Setup API client (`frontend/src/services/api.js`)

## 12. Frontend Pages & Components
- [ ] `App.jsx` — Routing setup
- [ ] `pages/Upload.jsx` — Drag & drop upload interface
- [ ] `pages/ReviewQueue.jsx` — Side-by-side HITL review UI
- [ ] `pages/Dashboard.jsx` — Analytics and Data Table

## 13. Backend Tests
- [ ] `tests/conftest.py` — Shared fixtures
- [ ] `tests/unit/test_arabic.py`
- [ ] `tests/unit/test_ocr.py`
- [ ] `tests/unit/test_nlp.py`
- [ ] `tests/unit/test_validation.py`
- [ ] `tests/unit/test_confidence.py`
- [ ] `tests/unit/test_storage.py`
- [ ] `tests/integration/test_pipeline.py`

## 14. Documentation
- [ ] `README.md`
- [ ] `docs/architecture.md`
