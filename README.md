# <span style="color:#2E86C1">Knowledge Base Ingestion + UI server App</span>

This repository contains the terraform infra setup, UI server and ingestion engine for RAG embeddings in OpenWebUI. It monitors local file systems and ensures the knowledge bases are up to date.

## <span style="color:#117A65">Architecture Overview</span>

The project follows a hexagonal architecture, strictly adhering to functional programming principles, immutability, and monadic error handling.

### <span style="color:#D35400">1. Infrastructure Layer</span>

Provides low-level technical capabilities as singleton dependencies:

* **Environment Manager**: Centralized singleton for configuration.
* **File System Access**: Service for safe, consistent local storage interactions.
* **Open Web UI Connector**: Asynchronous client for API communication.

### <span style="color:#D35400">2. Domain Layer</span>

Contains core business logic and models:

* **Knowledge Base Configuration**: Implemented via `KnowledgeBaseConfig` (frozen Pydantic).
* **Domain Service**: Defines logic for mapping directories to specific knowledge bases.

### <span style="color:#D35400">3. Application Layer</span>

Orchestrates the business flow through `KnowledgeBaseIngestionProcess`:

* **Persistence**: Designed to run perpetually.
* **Failure Handling**: Utilizes `returns` monads to handle failures without `try-except`.
* **Ingestion Logic**: Identifies non-embedded files and triggers synchronization.

### <span style="color:#D35400">4. Control Layer</span>

The entry point and configuration hub:

* **Main Module**: Application entry point.
* **App Controller**: orchestrates the application use cases in iisolated processes.
* **Dependency Container**: Utilizes `python-dependency-injector` for wiring.

---

## <span style="color:#117A65">Technical Stack</span>

* **Runtime**: Python 3.11 (Compatibility with Open WebUI)
* **Typing**: Strict typing with Pylance and MyPy
* **Dependency Injection**: `python-dependency-injector`
* **Async IO**: `asyncio` and `httpx`
* **Paradigm**: Functional, immutable, and monadic (`returns` library)
* **Infrastructure**: Open WebUI, LiteLLM, Terraform, Docker

---

## <span style="color:#117A65">Project Structure</span>

```text
src/
├── application/      # Orchestration of ingestion loops
├── control/          # Entry point and Dependency Injection
├── domain/           # Immutable models and mapping logic
└── infrastructure/   # External API and System drivers
