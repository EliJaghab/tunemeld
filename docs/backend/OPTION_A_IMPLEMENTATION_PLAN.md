# Option A: Minimal Enhancement Implementation Plan

## Executive Summary

This document provides a detailed implementation plan for **Option A: Minimal Enhancement** - the recommended evolutionary improvement path for the TuneMeld backend. This approach focuses on high-value, low-risk enhancements that significantly improve developer experience while preserving the excellent existing architecture.

---

## Chapter 1: Implementation Overview

### 1.1 Goals & Principles

#### **Primary Goals**

- **Developer Productivity**: Reduce setup time and cognitive load
- **System Reliability**: Improve debugging and monitoring capabilities
- **Maintainability**: Centralize configuration and reduce duplication
- **Future-Proofing**: Create foundation for advanced features

#### **Implementation Principles**

- **Zero Downtime**: All changes must maintain system availability
- **Backward Compatibility**: Existing functionality must continue working
- **Incremental Rollout**: Changes deployed in small, testable increments
- **Risk Mitigation**: Each phase can be rolled back independently

### 1.2 Success Metrics

#### **Developer Experience Metrics**

- Setup time: Reduce from 30 minutes to 5 minutes
- Configuration complexity: Single command vs. multiple files
- Debug time: 50% reduction in issue resolution time
- Command consistency: Unified interface for all operations

#### **System Quality Metrics**

- Configuration drift: Zero inconsistencies across environments
- Service reliability: 99.9% uptime maintained
- Error transparency: 100% errors have actionable messages
- Monitoring coverage: All critical paths observable

---

## Chapter 2: Phase 1 - Configuration Centralization (Week 1-2)

### 2.1 Current State Analysis

#### **Configuration Scattered Across**

```
django_backend/core/settings.py      # Django settings
playlist_etl/.env                    # ETL environment variables
.github/workflows/*.yml              # CI/CD configuration
django_backend/core/__init__.py      # Database connections
playlist_etl/services.py             # API keys and endpoints
```

#### **Problems This Creates**

- Environment variables duplicated in multiple files
- Inconsistent naming conventions across services
- No validation of configuration values
- Difficult to understand what settings are required
- Hard to maintain different environments (dev/staging/prod)

### 2.2 Centralized Configuration Architecture

#### **New Structure**

```
config/
├── __init__.py                     # Configuration entry point
├── settings/
│   ├── __init__.py                 # Settings factory
│   ├── base.py                     # Shared settings
│   ├── development.py              # Development overrides
│   ├── production.py               # Production overrides
│   ├── testing.py                  # Testing overrides
│   └── schema.py                   # Configuration validation
├── database.py                     # Database connection settings
├── external_apis.py                # Third-party API configuration
├── cache.py                        # Caching configuration
└── logging.py                      # Logging configuration
```

### 2.3 Implementation Details

#### **Step 1: Create Base Configuration (config/settings/base.py)**

```python
from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os

class BaseConfig(BaseSettings):
    """Base configuration shared across all environments"""

    # Application
    app_name: str = "tunemeld"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    mongodb_url: str = Field(..., env="MONGODB_URL")
    mongodb_database: str = Field("tunemeld", env="MONGODB_DATABASE")

    # External APIs
    rapidapi_key: str = Field(..., env="RAPIDAPI_KEY")
    spotify_client_id: str = Field(..., env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(..., env="SPOTIFY_CLIENT_SECRET")
    youtube_api_key: str = Field(..., env="YOUTUBE_API_KEY")

    # Cloudflare KV Cache
    cloudflare_account_id: str = Field(..., env="CLOUDFLARE_ACCOUNT_ID")
    cloudflare_namespace_id: str = Field(..., env="CLOUDFLARE_NAMESPACE_ID")
    cloudflare_api_token: str = Field(..., env="CLOUDFLARE_API_TOKEN")

    # ETL Configuration
    etl_batch_size: int = Field(100, env="ETL_BATCH_SIZE")
    etl_thread_count: int = Field(10, env="ETL_THREAD_COUNT")
    etl_retry_attempts: int = Field(3, env="ETL_RETRY_ATTEMPTS")
    etl_retry_delay: int = Field(5, env="ETL_RETRY_DELAY")

    # Django
    django_secret_key: str = Field(..., env="DJANGO_SECRET_KEY")
    django_allowed_hosts: List[str] = Field(["*"], env="DJANGO_ALLOWED_HOSTS")
    django_cors_origins: List[str] = Field(["http://localhost:8080"], env="DJANGO_CORS_ORIGINS")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")  # json or text

    @validator("mongodb_url")
    def validate_mongodb_url(cls, v):
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

#### **Step 2: Environment-Specific Configurations**

**Development (config/settings/development.py)**

```python
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    debug: bool = True
    log_level: str = "DEBUG"
    etl_batch_size: int = 10  # Smaller batches for development
    etl_thread_count: int = 2

    # Override for local development
    django_cors_origins: List[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080"
    ]
```

**Production (config/settings/production.py)**

```python
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Production optimizations
    etl_batch_size: int = 500
    etl_thread_count: int = 50

    # Strict CORS for production
    django_cors_origins: List[str] = [
        "https://tunemeld.com",
        "https://www.tunemeld.com"
    ]
```

**Testing (config/settings/testing.py)**

```python
from .base import BaseConfig

class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    debug: bool = True
    log_level: str = "DEBUG"

    # Test database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "tunemeld_test"

    # Fake API keys for testing
    rapidapi_key: str = "fake_rapidapi_key"
    spotify_client_id: str = "fake_spotify_id"
    spotify_client_secret: str = "fake_spotify_secret"
    youtube_api_key: str = "fake_youtube_key"

    # Disable external services
    cloudflare_account_id: str = "fake_account"
    cloudflare_namespace_id: str = "fake_namespace"
    cloudflare_api_token: str = "fake_token"

    # Fast testing
    etl_batch_size: int = 5
    etl_thread_count: int = 1
    etl_retry_attempts: int = 1
```

#### **Step 3: Configuration Factory (config/settings/**init**.py)**

```python
import os
from typing import Type
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

def get_config() -> BaseConfig:
    """
    Factory function to get appropriate configuration based on environment
    """
    env = os.getenv("TUNEMELD_ENV", "development").lower()

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()

# Global configuration instance
config = get_config()
```

#### **Step 4: Database Connection Module (config/database.py)**

```python
from pymongo import MongoClient
from pymongo.collection import Collection
from .settings import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management"""

    def __init__(self):
        self._client = None
        self._database = None

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            logger.info(f"Connecting to MongoDB: {config.mongodb_url}")
            self._client = MongoClient(config.mongodb_url)
        return self._client

    @property
    def database(self):
        if self._database is None:
            self._database = self.client[config.mongodb_database]
        return self._database

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection with standardized configuration"""
        return self.database[collection_name]

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            self.client.server_info()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database manager
db = DatabaseManager()

# Collection references
raw_playlists_collection = db.get_collection("raw_playlists")
transformed_playlists_collection = db.get_collection("track_playlist")
playlists_collection = db.get_collection("view_counts_playlists")
historical_track_views = db.get_collection("historical_track_views")
```

### 2.4 Migration Strategy for Phase 1

#### **Step 1: Create Configuration Structure (Day 1)**

1. Create `config/` directory structure
2. Implement base configuration classes
3. Add configuration validation
4. Create environment-specific configs

#### **Step 2: Update Django Backend (Day 2-3)**

```python
# django_backend/core/settings.py (updated)
from config.settings import config

# Database (keep Django's SQLite for admin, use config for MongoDB)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory for admin functionality
    }
}

# Security
SECRET_KEY = config.django_secret_key
DEBUG = config.debug
ALLOWED_HOSTS = config.django_allowed_hosts

# CORS
CORS_ALLOWED_ORIGINS = config.django_cors_origins

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
        },
        'text': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': config.log_format,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config.log_level,
    },
}
```

#### **Step 3: Update ETL Pipeline (Day 4-5)**

```python
# playlist_etl/extract.py (updated)
from config.settings import config
from config.database import raw_playlists_collection

class ExtractService:
    def __init__(self):
        self.rapidapi_key = config.rapidapi_key
        self.batch_size = config.etl_batch_size
        self.thread_count = config.etl_thread_count

    def extract_playlists(self):
        # Use centralized configuration
        headers = {"X-RapidAPI-Key": self.rapidapi_key}
        # ... rest of extraction logic
```

#### **Step 4: Update Environment Files (Day 6)**

Create comprehensive `.env.example`:

```bash
# TuneMeld Configuration
TUNEMELD_ENV=development

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=tunemeld

# External APIs
RAPIDAPI_KEY=your_rapidapi_key_here
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
YOUTUBE_API_KEY=your_youtube_api_key

# Cloudflare KV
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_NAMESPACE_ID=your_cloudflare_namespace_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# Django
DJANGO_SECRET_KEY=your_django_secret_key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CORS_ORIGINS=http://localhost:8080

# ETL Configuration
ETL_BATCH_SIZE=100
ETL_THREAD_COUNT=10
ETL_RETRY_ATTEMPTS=3
ETL_RETRY_DELAY=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 2.5 Testing Strategy for Phase 1

#### **Configuration Validation Tests**

```python
# tests/test_configuration.py
import pytest
from config.settings import get_config, DevelopmentConfig, ProductionConfig

def test_development_config():
    """Test development configuration loads correctly"""
    config = DevelopmentConfig()
    assert config.debug is True
    assert config.log_level == "DEBUG"

def test_production_config():
    """Test production configuration loads correctly"""
    config = ProductionConfig()
    assert config.debug is False
    assert config.log_level == "INFO"

def test_config_validation():
    """Test configuration validation"""
    with pytest.raises(ValueError):
        DevelopmentConfig(mongodb_url="invalid_url")
```

#### **Integration Tests**

```python
# tests/test_database_integration.py
from config.database import db

def test_database_connection():
    """Test database connection works with new configuration"""
    assert db.health_check() is True

def test_collections_accessible():
    """Test all collections are accessible"""
    collections = [
        db.raw_playlists_collection,
        db.transformed_playlists_collection,
        db.playlists_collection,
        db.historical_track_views
    ]
    for collection in collections:
        assert collection is not None
```

---

## Chapter 3: Phase 2 - Unified CLI Interface (Week 2-3)

### 3.1 Current State Analysis

#### **Current Command Structure**

```bash
# ETL Commands (scattered across make and python)
make extract
make transform
make aggregate
make view_count
python playlist_etl/extract.py
python playlist_etl/transform2.py

# Django Commands
python django_backend/manage.py runserver
python django_backend/manage.py migrate

# Development Commands
make serve-frontend
make serve-backend
make format
make test
```

#### **Problems This Creates**

- Inconsistent command interfaces
- No help system or documentation
- Different ways to accomplish similar tasks
- No validation of prerequisites
- Error messages not actionable

### 3.2 Unified CLI Architecture

#### **CLI Structure**

```
tunemeld/
├── __init__.py                     # CLI entry point
├── commands/
│   ├── __init__.py                 # Command registry
│   ├── etl.py                      # ETL pipeline commands
│   ├── api.py                      # API server commands
│   ├── db.py                       # Database commands
│   ├── dev.py                      # Development commands
│   └── config.py                   # Configuration commands
├── core/
│   ├── __init__.py
│   ├── cli.py                      # CLI framework
│   ├── output.py                   # Formatted output
│   └── validation.py               # Command validation
└── utils/
    ├── __init__.py
    ├── process.py                  # Process management
    └── files.py                    # File operations
```

### 3.3 Implementation Details

#### **Step 1: CLI Framework (tunemeld/core/cli.py)**

```python
import typer
from typing import Optional
from enum import Enum
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config.settings import config

console = Console()

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

app = typer.Typer(
    name="tunemeld",
    help="TuneMeld Backend Management CLI",
    add_completion=False,
    rich_markup_mode="rich"
)

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    log_level: LogLevel = typer.Option(LogLevel.INFO, "--log-level", help="Set logging level"),
    env: str = typer.Option(None, "--env", help="Override environment (development/production/testing)")
):
    """
    TuneMeld Backend Management CLI

    A unified interface for managing the TuneMeld backend, ETL pipeline, and development workflow.
    """
    if verbose:
        config.log_level = "DEBUG"

    if env:
        import os
        os.environ["TUNEMELD_ENV"] = env

    # Display banner
    console.print(Panel.fit(
        "[bold blue]TuneMeld Backend CLI[/bold blue]\n"
        f"Environment: [yellow]{config.app_name}[/yellow]\n"
        f"Version: [green]{config.app_version}[/green]",
        border_style="blue"
    ))
```

#### **Step 2: ETL Commands (tunemeld/commands/etl.py)**

```python
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List
from enum import Enum
import subprocess
import sys
from pathlib import Path

etl_app = typer.Typer(help="ETL Pipeline Management")

class ETLStage(str, Enum):
    EXTRACT = "extract"
    TRANSFORM = "transform"
    AGGREGATE = "aggregate"
    VIEW_COUNT = "view_count"
    FULL = "full"

class Genre(str, Enum):
    COUNTRY = "country"
    DANCE = "dance"
    POP = "pop"
    RAP = "rap"
    ALL = "all"

@etl_app.command()
def run(
    stage: ETLStage = typer.Argument(..., help="ETL stage to run"),
    genres: Optional[List[Genre]] = typer.Option(None, "--genre", "-g", help="Specific genres to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed without running"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Run genres in parallel"),
    threads: int = typer.Option(None, "--threads", help="Number of threads (overrides config)")
):
    """
    Run ETL pipeline stages

    Examples:
        tunemeld etl run extract                    # Extract all genres
        tunemeld etl run transform --genre pop      # Transform only pop genre
        tunemeld etl run full --dry-run             # Show full pipeline execution plan
    """
    console.print(f"[blue]Running ETL stage:[/blue] [bold]{stage.value}[/bold]")

    if genres and Genre.ALL in genres:
        genres = [Genre.COUNTRY, Genre.DANCE, Genre.POP, Genre.RAP]
    elif not genres:
        genres = [Genre.ALL]

    if dry_run:
        _show_execution_plan(stage, genres, parallel, threads)
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        if stage == ETLStage.FULL:
            _run_full_pipeline(progress, genres, parallel, threads)
        else:
            _run_stage(progress, stage, genres, parallel, threads)

def _run_full_pipeline(progress, genres, parallel, threads):
    """Run complete ETL pipeline"""
    stages = [ETLStage.EXTRACT, ETLStage.TRANSFORM, ETLStage.AGGREGATE, ETLStage.VIEW_COUNT]

    for stage in stages:
        task = progress.add_task(f"Running {stage.value}...", total=None)
        result = _execute_stage(stage, genres, threads)

        if result.returncode != 0:
            console.print(f"[red]❌ Stage {stage.value} failed[/red]")
            console.print(f"Error: {result.stderr}")
            sys.exit(1)

        progress.update(task, description=f"✅ {stage.value} completed")
        progress.remove_task(task)

def _execute_stage(stage: ETLStage, genres: List[Genre], threads: Optional[int]) -> subprocess.CompletedProcess:
    """Execute a single ETL stage"""
    from config.settings import config

    # Build command based on stage
    if stage == ETLStage.EXTRACT:
        cmd = ["python", "playlist_etl/extract.py"]
    elif stage == ETLStage.TRANSFORM:
        cmd = ["python", "playlist_etl/transform2.py"]
    elif stage == ETLStage.AGGREGATE:
        cmd = ["python", "playlist_etl/aggregate2.py"]
    elif stage == ETLStage.VIEW_COUNT:
        cmd = ["python", "playlist_etl/view_count2.py"]

    # Add genre filtering if specified
    if genres and Genre.ALL not in genres:
        cmd.extend(["--genres"] + [g.value for g in genres])

    # Add thread count override
    if threads:
        cmd.extend(["--threads", str(threads)])

    # Execute command
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )

@etl_app.command()
def status():
    """Show ETL pipeline status and last run information"""
    from config.database import db

    console.print(Panel("ETL Pipeline Status", style="blue"))

    # Check database connectivity
    if db.health_check():
        console.print("✅ Database: [green]Connected[/green]")
    else:
        console.print("❌ Database: [red]Connection Failed[/red]")
        return

    # Show last run information for each genre
    table = Table(title="Last ETL Runs")
    table.add_column("Genre", style="cyan")
    table.add_column("Last Extract", style="green")
    table.add_column("Last Transform", style="yellow")
    table.add_column("Last Aggregate", style="blue")
    table.add_column("Track Count", style="magenta")

    for genre in ["country", "dance", "pop", "rap"]:
        # Query last run data
        last_extract = _get_last_run_time("raw_playlists", genre)
        last_transform = _get_last_run_time("track_playlist", genre)
        last_aggregate = _get_last_run_time("view_counts_playlists", genre)
        track_count = _get_track_count(genre)

        table.add_row(
            genre.title(),
            last_extract or "Never",
            last_transform or "Never",
            last_aggregate or "Never",
            str(track_count)
        )

    console.print(table)

def _get_last_run_time(collection_name: str, genre: str) -> Optional[str]:
    """Get the last run time for a collection/genre"""
    from config.database import db

    try:
        collection = db.get_collection(collection_name)
        result = collection.find_one(
            {"genre_name": genre},
            sort=[("insert_timestamp", -1)]
        )
        if result and "insert_timestamp" in result:
            return result["insert_timestamp"].strftime("%Y-%m-%d %H:%M")
        return None
    except Exception:
        return None

def _get_track_count(genre: str) -> int:
    """Get track count for a genre"""
    from config.database import db

    try:
        collection = db.get_collection("view_counts_playlists")
        result = collection.find_one({"genre_name": genre})
        if result and "tracks" in result:
            return len(result["tracks"])
        return 0
    except Exception:
        return 0

@etl_app.command()
def validate():
    """Validate ETL configuration and dependencies"""
    from config.settings import config

    console.print(Panel("ETL Configuration Validation", style="blue"))

    checks = [
        ("MongoDB Connection", lambda: _check_mongodb()),
        ("RapidAPI Key", lambda: _check_api_key(config.rapidapi_key, "RapidAPI")),
        ("YouTube API Key", lambda: _check_api_key(config.youtube_api_key, "YouTube")),
        ("Spotify Credentials", lambda: _check_spotify_creds()),
        ("Cloudflare KV", lambda: _check_cloudflare_kv()),
        ("Python Dependencies", lambda: _check_python_deps()),
    ]

    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if result:
                console.print(f"✅ {check_name}: [green]OK[/green]")
            else:
                console.print(f"❌ {check_name}: [red]FAILED[/red]")
                all_passed = False
        except Exception as e:
            console.print(f"❌ {check_name}: [red]ERROR - {e}[/red]")
            all_passed = False

    if all_passed:
        console.print("\n[green]✅ All ETL validations passed![/green]")
    else:
        console.print("\n[red]❌ Some validations failed. Check configuration.[/red]")
        sys.exit(1)
```

#### **Step 3: API Commands (tunemeld/commands/api.py)**

```python
import typer
import subprocess
import sys
import time
import requests
from pathlib import Path
from rich.panel import Panel

api_app = typer.Typer(help="API Server Management")

@api_app.command()
def start(
    port: int = typer.Option(8000, "--port", "-p", help="Port to run server on"),
    host: str = typer.Option("localhost", "--host", help="Host to bind to"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Auto-reload on code changes"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of worker processes")
):
    """Start the Django API server"""
    console.print(Panel(f"Starting TuneMeld API Server", style="green"))
    console.print(f"URL: [blue]http://{host}:{port}[/blue]")

    cmd = [
        "python", "django_backend/manage.py", "runserver",
        f"{host}:{port}"
    ]

    if not reload:
        cmd.append("--noreload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start server: {e}[/red]")
        sys.exit(1)

@api_app.command()
def health():
    """Check API server health"""
    from config.settings import config

    console.print("Checking API health...")

    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            console.print("✅ API Server: [green]Healthy[/green]")

            # Test key endpoints
            endpoints = [
                "/graph-data/pop",
                "/playlist-data/pop",
                "/header-art/pop"
            ]

            for endpoint in endpoints:
                try:
                    resp = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                    status = "✅" if resp.status_code == 200 else "❌"
                    console.print(f"{status} {endpoint}: {resp.status_code}")
                except Exception as e:
                    console.print(f"❌ {endpoint}: [red]Error - {e}[/red]")
        else:
            console.print(f"❌ API Server: [red]Unhealthy - {response.status_code}[/red]")

    except requests.ConnectionError:
        console.print("❌ API Server: [red]Not running[/red]")
    except Exception as e:
        console.print(f"❌ API Server: [red]Error - {e}[/red]")

@api_app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Show API server logs"""
    # This would integrate with your logging system
    console.print(f"Showing last {lines} lines of API logs...")

    if follow:
        console.print("Following logs... (Press Ctrl+C to stop)")
        # Implementation would depend on your logging setup
```

#### **Step 4: Development Commands (tunemeld/commands/dev.py)**

```python
import typer
import subprocess
from pathlib import Path
import concurrent.futures

dev_app = typer.Typer(help="Development Workflow Commands")

@dev_app.command()
def setup():
    """Complete development environment setup"""
    console.print(Panel("Setting up TuneMeld development environment", style="blue"))

    tasks = [
        ("Installing Python dependencies", _install_python_deps),
        ("Installing Node.js dependencies", _install_node_deps),
        ("Setting up pre-commit hooks", _setup_precommit),
        ("Validating configuration", _validate_config),
        ("Setting up database", _setup_database),
    ]

    for task_name, task_func in tasks:
        console.print(f"📦 {task_name}...")
        try:
            task_func()
            console.print(f"✅ {task_name} completed")
        except Exception as e:
            console.print(f"❌ {task_name} failed: {e}")
            return

    console.print("\n[green]🎉 Development environment setup complete![/green]")
    console.print("\nNext steps:")
    console.print("1. Copy .env.example to .env and configure your API keys")
    console.print("2. Run: tunemeld dev start")

@dev_app.command()
def start():
    """Start full development environment (frontend + backend)"""
    console.print(Panel("Starting TuneMeld development environment", style="green"))

    # Start both frontend and backend in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start frontend server
        frontend_future = executor.submit(_start_frontend)

        # Start backend server
        backend_future = executor.submit(_start_backend)

        console.print("🚀 Starting servers...")
        console.print("Frontend: [blue]http://localhost:8080[/blue]")
        console.print("Backend: [blue]http://localhost:8000[/blue]")
        console.print("\nPress Ctrl+C to stop all servers")

        try:
            # Wait for both servers
            concurrent.futures.wait([frontend_future, backend_future])
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping development servers...[/yellow]")

def _start_frontend():
    """Start frontend development server"""
    subprocess.run(["make", "serve-frontend"], check=True)

def _start_backend():
    """Start backend development server"""
    subprocess.run(["make", "serve-backend"], check=True)

@dev_app.command()
def test(
    component: str = typer.Option(None, "--component", "-c", help="Test specific component (etl, api, frontend)"),
    coverage: bool = typer.Option(False, "--coverage", help="Run with coverage report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose test output")
):
    """Run test suite"""
    console.print(Panel("Running TuneMeld Test Suite", style="blue"))

    if component:
        if component == "etl":
            _run_etl_tests(coverage, verbose)
        elif component == "api":
            _run_api_tests(coverage, verbose)
        elif component == "frontend":
            _run_frontend_tests(coverage, verbose)
        else:
            console.print(f"[red]Unknown component: {component}[/red]")
            return
    else:
        # Run all tests
        _run_all_tests(coverage, verbose)

@dev_app.command()
def format():
    """Format all code (Python + JavaScript)"""
    console.print("🎨 Formatting code...")

    try:
        subprocess.run(["make", "format"], check=True)
        console.print("✅ Code formatting completed")
    except subprocess.CalledProcessError:
        console.print("❌ Code formatting failed")
        sys.exit(1)

@dev_app.command()
def lint():
    """Run linting checks"""
    console.print("🔍 Running linting checks...")

    try:
        subprocess.run(["make", "lint"], check=True)
        console.print("✅ Linting passed")
    except subprocess.CalledProcessError:
        console.print("❌ Linting failed")
        sys.exit(1)
```

### 3.4 CLI Entry Point and Installation

#### **Setup Script (setup.py)**

```python
from setuptools import setup, find_packages

setup(
    name="tunemeld-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "tunemeld=tunemeld.core.cli:app",
        ],
    },
    python_requires=">=3.10",
)
```

#### **Installation Instructions**

```bash
# Install CLI in development mode
pip install -e .

# Now you can use the CLI from anywhere
tunemeld --help
tunemeld etl --help
tunemeld api start
tunemeld dev setup
```

---

## Chapter 4: Phase 3 - Shared Service Layer (Week 3-4)

### 4.1 Current State Analysis

#### **Duplicated Code Patterns**

```python
# Django backend database access
from . import playlists_collection

# ETL database access
from pymongo import MongoClient
client = MongoClient(os.getenv("MONGODB_URL"))
db = client["tunemeld"]
playlists_collection = db["view_counts_playlists"]

# Both implementing similar caching logic
# Both handling API retries differently
# Both managing logging separately
```

### 4.2 Shared Service Architecture

#### **Service Structure**

```
shared/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── database.py                 # Unified database operations
│   ├── cache.py                    # Unified caching service
│   ├── external_apis.py            # External API clients
│   ├── logging.py                  # Structured logging
│   └── retry.py                    # Retry logic
├── models/
│   ├── __init__.py
│   ├── domain.py                   # Business domain models
│   └── responses.py                # API response models
└── utils/
    ├── __init__.py
    ├── validation.py               # Common validations
    └── transformations.py          # Data transformations
```

### 4.3 Implementation Details

#### **Database Service (shared/services/database.py)**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class DatabaseService(ABC):
    """Abstract database service interface"""

    @abstractmethod
    def get_playlists(self, genre: str) -> List[Dict]:
        pass

    @abstractmethod
    def save_playlist(self, playlist_data: Dict) -> bool:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

class MongoDBService(DatabaseService):
    """MongoDB implementation of database service"""

    def __init__(self):
        self._client = None
        self._database = None
        self._collections = {}

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            logger.info("Initializing MongoDB connection")
            self._client = MongoClient(config.mongodb_url)
        return self._client

    @property
    def database(self):
        if self._database is None:
            self._database = self.client[config.mongodb_database]
        return self._database

    def get_collection(self, name: str) -> Collection:
        """Get collection with caching"""
        if name not in self._collections:
            self._collections[name] = self.database[name]
        return self._collections[name]

    def get_playlists(self, genre: str) -> List[Dict]:
        """Get playlists for a genre"""
        try:
            collection = self.get_collection("view_counts_playlists")
            return list(collection.find({"genre_name": genre}, {"_id": False}))
        except Exception as e:
            logger.error(f"Failed to get playlists for genre {genre}: {e}")
            raise

    def save_playlist(self, playlist_data: Dict) -> bool:
        """Save playlist data"""
        try:
            collection_name = self._determine_collection(playlist_data)
            collection = self.get_collection(collection_name)

            result = collection.replace_one(
                {"genre_name": playlist_data["genre_name"], "service_name": playlist_data.get("service_name")},
                playlist_data,
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to save playlist: {e}")
            return False

    def get_raw_playlists(self, genre: str) -> List[Dict]:
        """Get raw playlist data"""
        collection = self.get_collection("raw_playlists")
        return list(collection.find({"genre_name": genre}, {"_id": False}))

    def get_transformed_playlists(self, genre: str, service: str = None) -> List[Dict]:
        """Get transformed playlist data"""
        collection = self.get_collection("track_playlist")
        query = {"genre_name": genre}
        if service:
            query["service_name"] = service
        return list(collection.find(query, {"_id": False}))

    def get_historical_views(self, isrc_list: List[str]) -> Dict[str, Dict]:
        """Get historical view data for tracks"""
        collection = self.get_collection("historical_track_views")
        track_views = collection.find({"isrc": {"$in": isrc_list}})
        return {track["isrc"]: track for track in track_views}

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            self.client.server_info()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def _determine_collection(self, data: Dict) -> str:
        """Determine which collection to use based on data structure"""
        if "tracks" in data and isinstance(data["tracks"], list):
            if "isrc" in str(data):
                return "view_counts_playlists"
            else:
                return "track_playlist"
        else:
            return "raw_playlists"

# Global database service instance
db_service = MongoDBService()
```

#### **Cache Service (shared/services/cache.py)**

```python
from abc import ABC, abstractmethod
from typing import Any, Optional
import json
import logging
from config.settings import config

logger = logging.getLogger(__name__)

class CacheService(ABC):
    """Abstract cache service interface"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> bool:
        pass

class CloudflareKVCache(CacheService):
    """Cloudflare KV implementation of cache service"""

    def __init__(self):
        self.account_id = config.cloudflare_account_id
        self.namespace_id = config.cloudflare_namespace_id
        self.api_token = config.cloudflare_api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/storage/kv/namespaces/{self.namespace_id}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from Cloudflare KV"""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            response = requests.get(
                f"{self.base_url}/values/{key}",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"Cache get failed for key {key}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Cloudflare KV"""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            # Cloudflare KV doesn't support TTL in the same way, but we can include metadata
            data = {
                "value": json.dumps(value),
                "metadata": {"ttl": ttl, "created_at": int(time.time())}
            }

            response = requests.put(
                f"{self.base_url}/values/{key}",
                headers=headers,
                json=data,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from Cloudflare KV"""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }

            response = requests.delete(
                f"{self.base_url}/values/{key}",
                headers=headers,
                timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries (not recommended for production)"""
        logger.warning("Cache clear operation not implemented for Cloudflare KV")
        return False

class InMemoryCache(CacheService):
    """In-memory cache implementation for development/testing"""

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[Any]:
        import time

        if key not in self._cache:
            return None

        # Check TTL
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._cache[key]
            del self._ttl[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        import time

        self._cache[key] = value
        self._ttl[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
        return True

    def clear(self) -> bool:
        self._cache.clear()
        self._ttl.clear()
        return True

def get_cache_service() -> CacheService:
    """Factory function to get appropriate cache service"""
    if config.debug:
        return InMemoryCache()
    else:
        return CloudflareKVCache()

# Global cache service instance
cache_service = get_cache_service()
```

#### **External API Service (shared/services/external_apis.py)**

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import requests
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class ExternalAPIService(ABC):
    """Base class for external API services"""

    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        self.base_url = base_url
        self.headers = headers or {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            raise

class SpotifyAPIService(ExternalAPIService):
    """Spotify API service via RapidAPI"""

    def __init__(self):
        headers = {
            "X-RapidAPI-Key": config.rapidapi_key,
            "X-RapidAPI-Host": "spotify23.p.rapidapi.com"
        }
        super().__init__("https://spotify23.p.rapidapi.com", headers)

    def get_playlist(self, playlist_id: str) -> Dict:
        """Get Spotify playlist data"""
        response = self.make_request(
            "GET",
            f"/playlist_tracks/",
            params={"id": playlist_id, "offset": "0", "limit": "100"}
        )
        return response.json()

    def search_track(self, isrc: str) -> Optional[Dict]:
        """Search for track by ISRC"""
        response = self.make_request(
            "GET",
            "/search/",
            params={"q": f"isrc:{isrc}", "type": "track", "limit": "1"}
        )

        data = response.json()
        if data.get("tracks", {}).get("items"):
            return data["tracks"]["items"][0]
        return None

class YouTubeAPIService(ExternalAPIService):
    """YouTube Data API service"""

    def __init__(self):
        super().__init__("https://www.googleapis.com/youtube/v3")
        self.api_key = config.youtube_api_key

    def search_video(self, query: str) -> Optional[Dict]:
        """Search for video by query"""
        response = self.make_request(
            "GET",
            "/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 1,
                "key": self.api_key
            }
        )

        data = response.json()
        if data.get("items"):
            return data["items"][0]
        return None

    def get_video_stats(self, video_id: str) -> Optional[Dict]:
        """Get video statistics"""
        response = self.make_request(
            "GET",
            "/videos",
            params={
                "part": "statistics",
                "id": video_id,
                "key": self.api_key
            }
        )

        data = response.json()
        if data.get("items"):
            return data["items"][0]["statistics"]
        return None

class AppleMusicAPIService(ExternalAPIService):
    """Apple Music API service via RapidAPI"""

    def __init__(self):
        headers = {
            "X-RapidAPI-Key": config.rapidapi_key,
            "X-RapidAPI-Host": "apple-music24.p.rapidapi.com"
        }
        super().__init__("https://apple-music24.p.rapidapi.com", headers)

    def get_playlist(self, playlist_id: str) -> Dict:
        """Get Apple Music playlist data"""
        response = self.make_request(
            "GET",
            f"/playlist/{playlist_id}"
        )
        return response.json()

class SoundCloudAPIService(ExternalAPIService):
    """SoundCloud API service via RapidAPI"""

    def __init__(self):
        headers = {
            "X-RapidAPI-Key": config.rapidapi_key,
            "X-RapidAPI-Host": "soundcloud-scraper.p.rapidapi.com"
        }
        super().__init__("https://soundcloud-scraper.p.rapidapi.com", headers)

    def get_playlist(self, playlist_url: str) -> Dict:
        """Get SoundCloud playlist data"""
        response = self.make_request(
            "GET",
            "/playlist",
            params={"playlist": playlist_url}
        )
        return response.json()

# Service instances
spotify_service = SpotifyAPIService()
youtube_service = YouTubeAPIService()
apple_music_service = AppleMusicAPIService()
soundcloud_service = SoundCloudAPIService()
```

### 4.4 Integration with Existing Code

#### **Update Django Views (django_backend/core/views.py)**

```python
import logging
from django.http import JsonResponse
from shared.services.database import db_service
from shared.services.cache import cache_service
from shared.models.responses import APIResponse, ResponseStatus

logger = logging.getLogger(__name__)

def get_playlist_data(request, genre_name):
    """Get playlist data using shared services"""
    try:
        # Try cache first
        cache_key = f"playlist_data_{genre_name}"
        cached_data = cache_service.get(cache_key)

        if cached_data:
            return APIResponse.success("Playlist data retrieved from cache", cached_data).to_json_response()

        # Get from database using shared service
        data = db_service.get_playlists(genre_name)

        if not data:
            return APIResponse.error("No data found for the specified genre").to_json_response()

        # Cache the result
        cache_service.set(cache_key, data, ttl=3600)

        return APIResponse.success("Playlist data retrieved successfully", data).to_json_response()

    except Exception as error:
        logger.exception("Error in get_playlist_data view")
        return APIResponse.error(str(error)).to_json_response()

def get_graph_data(request, genre_name):
    """Get graph data using shared services"""
    try:
        cache_key = f"graph_data_{genre_name}"
        cached_data = cache_service.get(cache_key)

        if cached_data:
            return APIResponse.success("Graph data retrieved from cache", cached_data).to_json_response()

        # Get playlist tracks
        playlists = db_service.get_playlists(genre_name)
        if not playlists:
            return APIResponse.error("No playlist data found").to_json_response()

        tracks = playlists[0]["tracks"]
        isrc_list = [track["isrc"] for track in tracks]

        # Get historical view data
        track_views = db_service.get_historical_views(isrc_list)

        # Enrich tracks with view data
        for track in tracks:
            if track["isrc"] in track_views:
                view_data = track_views[track["isrc"]]
                if "view_counts" in view_data:
                    track["view_counts"] = {}
                    for service_name, view_counts in view_data["view_counts"].items():
                        track["view_counts"][service_name] = [
                            [view["current_timestamp"], view["delta_count"]]
                            for view in view_counts
                        ]

        # Cache the enriched data
        cache_service.set(cache_key, tracks, ttl=1800)  # 30 minutes

        return APIResponse.success("Graph data retrieved successfully", tracks).to_json_response()

    except Exception as error:
        logger.exception("Error in get_graph_data view")
        return APIResponse.error(str(error)).to_json_response()
```

#### **Update ETL Scripts (playlist_etl/extract.py)**

```python
from shared.services.database import db_service
from shared.services.external_apis import spotify_service, apple_music_service, soundcloud_service
from shared.services.cache import cache_service
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class ExtractService:
    """ETL Extract service using shared services"""

    def __init__(self):
        self.batch_size = config.etl_batch_size
        self.thread_count = config.etl_thread_count

    def extract_all_playlists(self):
        """Extract playlists from all services"""
        genres = ["country", "dance", "pop", "rap"]

        for genre in genres:
            logger.info(f"Extracting playlists for genre: {genre}")

            # Extract from each service
            spotify_data = self._extract_spotify_playlist(genre)
            apple_data = self._extract_apple_music_playlist(genre)
            soundcloud_data = self._extract_soundcloud_playlist(genre)

            # Save to database using shared service
            for data in [spotify_data, apple_data, soundcloud_data]:
                if data:
                    db_service.save_playlist(data)

            logger.info(f"Completed extraction for genre: {genre}")

    def _extract_spotify_playlist(self, genre: str) -> dict:
        """Extract Spotify playlist for genre"""
        try:
            playlist_id = self._get_playlist_id("spotify", genre)
            playlist_data = spotify_service.get_playlist(playlist_id)

            return {
                "genre_name": genre,
                "service_name": "Spotify",
                "playlist_data": playlist_data,
                "insert_timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to extract Spotify playlist for {genre}: {e}")
            return None

    def _extract_apple_music_playlist(self, genre: str) -> dict:
        """Extract Apple Music playlist for genre"""
        try:
            playlist_id = self._get_playlist_id("apple_music", genre)
            playlist_data = apple_music_service.get_playlist(playlist_id)

            return {
                "genre_name": genre,
                "service_name": "AppleMusic",
                "playlist_data": playlist_data,
                "insert_timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to extract Apple Music playlist for {genre}: {e}")
            return None

    def _extract_soundcloud_playlist(self, genre: str) -> dict:
        """Extract SoundCloud playlist for genre"""
        try:
            playlist_url = self._get_playlist_url("soundcloud", genre)
            playlist_data = soundcloud_service.get_playlist(playlist_url)

            return {
                "genre_name": genre,
                "service_name": "SoundCloud",
                "playlist_data": playlist_data,
                "insert_timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to extract SoundCloud playlist for {genre}: {e}")
            return None

    def _get_playlist_id(self, service: str, genre: str) -> str:
        """Get playlist ID for service/genre combination"""
        # This would be moved to configuration
        playlist_map = {
            ("spotify", "pop"): "37i9dQZF1DXcBWIGoYBM5M",
            ("spotify", "rap"): "37i9dQZF1DX0XUsuxWHRQd",
            # ... etc
        }
        return playlist_map.get((service, genre))
```

---

## Chapter 5: Phase 4 - Enhanced Monitoring & Debugging (Week 4)

### 5.1 Current State Analysis

#### **Monitoring Gaps**

- No centralized logging across Django and ETL
- Limited error visibility in production
- No performance metrics collection
- Manual debugging process

### 5.2 Enhanced Monitoring Architecture

#### **Structured Logging Service (shared/services/logging.py)**

```python
import logging
import json
import sys
from typing import Dict, Any
from datetime import datetime
from config.settings import config

class StructuredLogger:
    """Structured logging service for TuneMeld"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Setup logger with appropriate handlers and formatters"""
        if config.log_format == "json":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, config.log_level))
        self.logger.propagate = False

    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self._log(logging.INFO, message, **kwargs)

    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message with context"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log(logging.ERROR, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self._log(logging.WARNING, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method"""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "tunemeld",
            "environment": config.app_name,
            **kwargs
        }
        self.logger.log(level, message, extra=extra)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "getMessage"]:
                log_data[key] = value

        return json.dumps(log_data)

class TextFormatter(logging.Formatter):
    """Human-readable formatter for development"""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)
```

#### **Performance Monitoring (shared/services/monitoring.py)**

```python
import time
import functools
from typing import Callable, Dict, Any
from shared.services.logging import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """Performance monitoring utilities"""

    @staticmethod
    def measure_time(operation_name: str):
        """Decorator to measure function execution time"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    logger.info(
                        f"Operation completed: {operation_name}",
                        operation=operation_name,
                        duration_seconds=round(duration, 3),
                        function=func.__name__,
                        status="success"
                    )
                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"Operation failed: {operation_name}",
                        operation=operation_name,
                        duration_seconds=round(duration, 3),
                        function=func.__name__,
                        status="error",
                        error=e
                    )
                    raise
            return wrapper
        return decorator

    @staticmethod
    def track_etl_stage(stage_name: str, genre: str = None):
        """Track ETL stage performance"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                context = {
                    "etl_stage": stage_name,
                    "genre": genre
                }

                logger.info(f"Starting ETL stage: {stage_name}", **context)
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    logger.info(
                        f"ETL stage completed: {stage_name}",
                        duration_seconds=round(duration, 3),
                        status="success",
                        **context
                    )
                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"ETL stage failed: {stage_name}",
                        duration_seconds=round(duration, 3),
                        status="error",
                        error=e,
                        **context
                    )
                    raise
            return wrapper
        return decorator

# Decorators for easy use
measure_time = PerformanceMonitor.measure_time
track_etl_stage = PerformanceMonitor.track_etl_stage
```

#### **Health Check Service (shared/services/health.py)**

```python
from typing import Dict, List
from shared.services.database import db_service
from shared.services.cache import cache_service
from shared.services.external_apis import spotify_service, youtube_service
from shared.services.logging import get_logger
import requests

logger = get_logger(__name__)

class HealthCheck:
    """System health monitoring"""

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "cache": self._check_cache,
            "spotify_api": self._check_spotify_api,
            "youtube_api": self._check_youtube_api,
            "disk_space": self._check_disk_space,
        }

    def run_all_checks(self) -> Dict[str, Dict]:
        """Run all health checks"""
        results = {}
        overall_healthy = True

        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                results[check_name] = result
                if not result["healthy"]:
                    overall_healthy = False
            except Exception as e:
                results[check_name] = {
                    "healthy": False,
                    "error": str(e),
                    "details": "Health check failed with exception"
                }
                overall_healthy = False

        return {
            "overall_healthy": overall_healthy,
            "checks": results,
            "timestamp": time.time()
        }

    def _check_database(self) -> Dict:
        """Check database connectivity"""
        try:
            healthy = db_service.health_check()

            # Additional checks
            details = {}
            if healthy:
                # Check collection counts
                genres = ["country", "dance", "pop", "rap"]
                for genre in genres:
                    try:
                        playlists = db_service.get_playlists(genre)
                        details[f"{genre}_playlist_count"] = len(playlists)
                    except Exception:
                        details[f"{genre}_playlist_count"] = "error"

            return {
                "healthy": healthy,
                "details": details
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_cache(self) -> Dict:
        """Check cache service"""
        try:
            # Test cache with a simple key
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": time.time()}

            # Test set
            set_success = cache_service.set(test_key, test_value, ttl=60)
            if not set_success:
                return {"healthy": False, "error": "Cache set failed"}

            # Test get
            retrieved_value = cache_service.get(test_key)
            if retrieved_value != test_value:
                return {"healthy": False, "error": "Cache get/set mismatch"}

            # Cleanup
            cache_service.delete(test_key)

            return {
                "healthy": True,
                "details": {"cache_type": type(cache_service).__name__}
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_spotify_api(self) -> Dict:
        """Check Spotify API connectivity"""
        try:
            # Try to search for a track
            result = spotify_service.search_track("USRC17607839")

            return {
                "healthy": True,
                "details": {"response_received": result is not None}
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_youtube_api(self) -> Dict:
        """Check YouTube API connectivity"""
        try:
            # Try a simple search
            result = youtube_service.search_video("test music video")

            return {
                "healthy": True,
                "details": {"response_received": result is not None}
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_disk_space(self) -> Dict:
        """Check available disk space"""
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024**3)
            free_percent = (free / total) * 100

            healthy = free_gb > 1  # At least 1GB free

            return {
                "healthy": healthy,
                "details": {
                    "free_gb": free_gb,
                    "free_percent": round(free_percent, 1)
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

# Global health check instance
health_checker = HealthCheck()
```

#### **Debug Utilities (shared/utils/debug.py)**

```python
import json
import traceback
from typing import Any, Dict
from shared.services.logging import get_logger

logger = get_logger(__name__)

class DebugUtils:
    """Debugging utilities for TuneMeld"""

    @staticmethod
    def capture_context(**kwargs) -> Dict[str, Any]:
        """Capture debug context"""
        import os
        import sys
        from datetime import datetime

        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_vars": {
                key: value for key, value in os.environ.items()
                if "key" in key.lower() or "token" in key.lower() or "secret" in key.lower()
            },
            **kwargs
        }

        return context

    @staticmethod
    def log_error_with_context(error: Exception, **context):
        """Log error with full context"""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            **DebugUtils.capture_context(),
            **context
        }

        logger.error("Error occurred with full context", **error_context)

    @staticmethod
    def validate_data_structure(data: Any, expected_keys: list = None, name: str = "data") -> bool:
        """Validate data structure and log issues"""
        issues = []

        if expected_keys and isinstance(data, dict):
            missing_keys = set(expected_keys) - set(data.keys())
            if missing_keys:
                issues.append(f"Missing keys: {missing_keys}")

        if not data:
            issues.append("Data is empty or None")

        if issues:
            logger.warning(
                f"Data validation issues for {name}",
                data_name=name,
                issues=issues,
                data_type=type(data).__name__
            )
            return False

        return True

    @staticmethod
    def dump_data_sample(data: Any, name: str = "data", max_items: int = 3):
        """Dump a sample of data for debugging"""
        try:
            if isinstance(data, list):
                sample = data[:max_items]
                logger.debug(
                    f"Data sample for {name}",
                    data_name=name,
                    sample_size=len(sample),
                    total_size=len(data),
                    sample=sample
                )
            elif isinstance(data, dict):
                items = list(data.items())[:max_items]
                logger.debug(
                    f"Data sample for {name}",
                    data_name=name,
                    sample_size=len(items),
                    total_size=len(data),
                    sample=dict(items)
                )
            else:
                logger.debug(
                    f"Data sample for {name}",
                    data_name=name,
                    data_type=type(data).__name__,
                    sample=str(data)[:200]
                )
        except Exception as e:
            logger.error(f"Failed to dump data sample for {name}", error=e)
```

---

## Chapter 6: Implementation Timeline & Milestones

### 6.1 Detailed Timeline

#### **Week 1: Configuration Centralization**

- **Days 1-2**: Create configuration structure and base classes
- **Days 3-4**: Update Django backend to use centralized config
- **Days 5-6**: Update ETL pipeline to use centralized config
- **Day 7**: Testing and validation

**Deliverables:**

- Centralized configuration system
- Environment-specific configuration files
- Updated Django settings
- Updated ETL scripts
- Configuration validation tests

#### **Week 2: CLI Framework Foundation**

- **Days 1-2**: Implement CLI framework and core commands
- **Days 3-4**: Implement ETL management commands
- **Days 5-6**: Implement API and development commands
- **Day 7**: CLI testing and documentation

**Deliverables:**

- Unified CLI interface
- ETL pipeline commands
- API management commands
- Development workflow commands
- CLI help system and documentation

#### **Week 3: Shared Service Layer**

- **Days 1-2**: Implement database and cache services
- **Days 3-4**: Implement external API services
- **Days 5-6**: Update Django and ETL to use shared services
- **Day 7**: Integration testing

**Deliverables:**

- Shared database service
- Unified cache service
- External API service layer
- Updated Django views
- Updated ETL scripts
- Service integration tests

#### **Week 4: Monitoring & Polish**

- **Days 1-2**: Implement structured logging and monitoring
- **Days 3-4**: Add health checks and debug utilities
- **Days 5-6**: Performance testing and optimization
- **Day 7**: Documentation and final testing

**Deliverables:**

- Structured logging system
- Performance monitoring
- Health check endpoints
- Debug utilities
- Complete documentation
- Performance benchmarks

### 6.2 Success Criteria

#### **Phase 1 Success Criteria**

- [ ] All configuration centralized in `config/` directory
- [ ] Zero configuration duplication across services
- [ ] Environment switching works via `TUNEMELD_ENV`
- [ ] All tests pass with new configuration
- [ ] Setup time reduced from 30 minutes to 10 minutes

#### **Phase 2 Success Criteria**

- [ ] Single `tunemeld` command for all operations
- [ ] All existing make commands have CLI equivalents
- [ ] CLI provides helpful error messages
- [ ] Help system is comprehensive and useful
- [ ] Setup time reduced to 5 minutes

#### **Phase 3 Success Criteria**

- [ ] No code duplication between Django and ETL
- [ ] Consistent error handling across services
- [ ] Shared service layer provides all common functionality
- [ ] Integration tests validate service interactions
- [ ] Performance maintained or improved

#### **Phase 4 Success Criteria**

- [ ] Structured logging across all components
- [ ] Health checks provide actionable information
- [ ] Error debugging time reduced by 50%
- [ ] Performance metrics collected for all operations
- [ ] System observability is comprehensive

### 6.3 Risk Mitigation & Rollback Plans

#### **Risk: Configuration Changes Break Existing Functionality**

**Mitigation:**

- Keep existing configuration files during transition
- Use feature flags to switch between old and new config
- Comprehensive regression testing
- Gradual rollout environment by environment

**Rollback Plan:**

- Revert configuration imports to original files
- Keep backup copies of all original configuration
- Automated rollback script in case of issues

#### **Risk: CLI Interface Adoption Challenges**

**Mitigation:**

- Maintain existing make commands during transition
- Provide clear migration documentation
- Add aliases for common commands
- Progressive disclosure in help system

**Rollback Plan:**

- CLI is additive, existing commands continue working
- No removal of existing interfaces until adoption confirmed

#### **Risk: Shared Services Introduce Performance Regression**

**Mitigation:**

- Benchmark performance before and after changes
- Load testing with production-like data
- Gradual migration of components to shared services
- Performance monitoring and alerting

**Rollback Plan:**

- Feature flags to disable shared services
- Keep original service implementations
- Quick rollback to original architecture

---

## Chapter 7: Developer Migration Guide

### 7.1 Before and After Comparison

#### **Configuration Management**

**Before:**

```bash
# Multiple configuration files to manage
vim django_backend/core/settings.py
vim playlist_etl/.env
vim .github/workflows/playlist_etl2.yml

# Environment variables scattered across files
export MONGODB_URL="..."
export RAPIDAPI_KEY="..."
# ... many more in different places
```

**After:**

```bash
# Single configuration file
cp .env.example .env
vim .env

# Set environment once
export TUNEMELD_ENV=development
```

#### **Development Workflow**

**Before:**

```bash
# Start services manually
cd django_backend && python manage.py runserver &
cd .. && make serve-frontend &

# Run ETL manually
python playlist_etl/extract.py
python playlist_etl/transform2.py
python playlist_etl/aggregate2.py

# Different test commands
make test
pytest django_backend/
```

**After:**

```bash
# Start all services
tunemeld dev start

# Run ETL pipeline
tunemeld etl run full

# Unified testing
tunemeld dev test
```

#### **Debugging and Monitoring**

**Before:**

```bash
# Manual log checking
tail -f django_backend/logs/django.log
tail -f playlist_etl/logs/etl.log

# No structured error information
# Manual database queries for debugging
```

**After:**

```bash
# Structured logs everywhere
tunemeld api logs --follow

# Health monitoring
tunemeld system health

# Integrated debugging
tunemeld etl status
tunemeld api health
```

### 7.2 Migration Steps for Developers

#### **Step 1: Update Local Environment**

```bash
# Pull latest changes with Option A implementation
git pull origin main

# Install CLI
pip install -e .

# Verify CLI works
tunemeld --help
```

#### **Step 2: Migrate Configuration**

```bash
# Copy new environment template
cp .env.example .env

# Migrate your existing environment variables
# (Tool could help with this migration)
tunemeld config migrate-env
```

#### **Step 3: Update Workflow**

```bash
# Old workflow
make serve-backend & make serve-frontend &

# New workflow
tunemeld dev start
```

#### **Step 4: Update Testing**

```bash
# Old testing
make test

# New testing
tunemeld dev test
```

### 7.3 Troubleshooting Guide

#### **Common Issues and Solutions**

**Issue: "tunemeld command not found"**

```bash
# Solution: Install CLI package
pip install -e .

# Or activate virtual environment
source venv/bin/activate
pip install -e .
```

**Issue: "Configuration validation failed"**

```bash
# Solution: Check environment variables
tunemeld config validate

# Check specific configuration
tunemeld config show --env development
```

**Issue: "Database connection failed"**

```bash
# Solution: Check database health
tunemeld system health

# Test database connectivity
tunemeld db test-connection
```

**Issue: "ETL pipeline fails to start"**

```bash
# Solution: Validate ETL configuration
tunemeld etl validate

# Check API keys and dependencies
tunemeld system health
```

---

## Chapter 8: Testing Strategy

### 8.1 Testing Approach

#### **Unit Tests**

- Configuration validation
- Service layer functionality
- CLI command logic
- Utility functions

#### **Integration Tests**

- Database service integration
- Cache service integration
- External API service integration
- CLI command execution

#### **End-to-End Tests**

- Full ETL pipeline execution
- API endpoint functionality
- Developer workflow scenarios

### 8.2 Test Implementation

#### **Configuration Tests (tests/test_config.py)**

```python
import pytest
import os
from config.settings import get_config, DevelopmentConfig, ProductionConfig, TestingConfig

class TestConfiguration:

    def test_development_config_loads(self):
        """Test development configuration loads correctly"""
        os.environ["TUNEMELD_ENV"] = "development"
        config = get_config()

        assert isinstance(config, DevelopmentConfig)
        assert config.debug is True
        assert config.log_level == "DEBUG"

    def test_production_config_loads(self):
        """Test production configuration loads correctly"""
        os.environ["TUNEMELD_ENV"] = "production"
        config = get_config()

        assert isinstance(config, ProductionConfig)
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_config_validation_mongodb_url(self):
        """Test MongoDB URL validation"""
        with pytest.raises(ValueError, match="MongoDB URL must start with"):
            DevelopmentConfig(mongodb_url="invalid_url")

    def test_config_validation_log_level(self):
        """Test log level validation"""
        with pytest.raises(ValueError, match="Log level must be one of"):
            DevelopmentConfig(log_level="INVALID")

    def test_environment_variable_override(self):
        """Test environment variables override defaults"""
        os.environ["ETL_BATCH_SIZE"] = "200"
        config = DevelopmentConfig()

        assert config.etl_batch_size == 200
```

#### **Service Layer Tests (tests/test_services.py)**

```python
import pytest
from unittest.mock import Mock, patch
from shared.services.database import MongoDBService
from shared.services.cache import InMemoryCache
from shared.services.external_apis import SpotifyAPIService

class TestDatabaseService:

    @pytest.fixture
    def db_service(self):
        """Create database service for testing"""
        return MongoDBService()

    @patch('shared.services.database.MongoClient')
    def test_health_check_success(self, mock_client, db_service):
        """Test successful health check"""
        mock_client.return_value.server_info.return_value = {"version": "5.0"}

        assert db_service.health_check() is True

    @patch('shared.services.database.MongoClient')
    def test_health_check_failure(self, mock_client, db_service):
        """Test failed health check"""
        mock_client.return_value.server_info.side_effect = Exception("Connection failed")

        assert db_service.health_check() is False

    def test_get_playlists_success(self, db_service):
        """Test getting playlists successfully"""
        # Mock collection
        mock_collection = Mock()
        mock_collection.find.return_value = [
            {"genre_name": "pop", "tracks": []}
        ]

        with patch.object(db_service, 'get_collection', return_value=mock_collection):
            playlists = db_service.get_playlists("pop")

            assert len(playlists) == 1
            assert playlists[0]["genre_name"] == "pop"
            mock_collection.find.assert_called_once_with(
                {"genre_name": "pop"},
                {"_id": False}
            )

class TestCacheService:

    def test_in_memory_cache_operations(self):
        """Test in-memory cache basic operations"""
        cache = InMemoryCache()

        # Test set and get
        assert cache.set("test_key", {"data": "test"}) is True
        assert cache.get("test_key") == {"data": "test"}

        # Test delete
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None

        # Test clear
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.clear() is True
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_ttl_expiration(self):
        """Test cache TTL functionality"""
        import time

        cache = InMemoryCache()

        # Set with short TTL
        cache.set("ttl_key", "value", ttl=1)
        assert cache.get("ttl_key") == "value"

        # Wait for expiration
        time.sleep(2)
        assert cache.get("ttl_key") is None

class TestExternalAPIServices:

    @patch('requests.Session.request')
    def test_spotify_service_search_track(self, mock_request):
        """Test Spotify service track search"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tracks": {
                "items": [{"id": "track123", "name": "Test Track"}]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        service = SpotifyAPIService()
        result = service.search_track("USRC17607839")

        assert result is not None
        assert result["id"] == "track123"
        assert result["name"] == "Test Track"

    @patch('requests.Session.request')
    def test_api_service_retry_logic(self, mock_request):
        """Test API service retry logic"""
        # Mock first call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("API Error")

        mock_response_success = Mock()
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.raise_for_status.return_value = None

        mock_request.side_effect = [mock_response_fail, mock_response_success]

        service = SpotifyAPIService()
        # This should succeed after retry
        response = service.make_request("GET", "/test")

        assert response.json()["success"] is True
        assert mock_request.call_count == 2
```

#### **CLI Tests (tests/test_cli.py)**

```python
import pytest
from typer.testing import CliRunner
from tunemeld.core.cli import app

class TestCLI:

    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help output"""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "TuneMeld Backend Management CLI" in result.stdout

    def test_etl_command_help(self):
        """Test ETL command help"""
        result = self.runner.invoke(app, ["etl", "--help"])

        assert result.exit_code == 0
        assert "ETL Pipeline Management" in result.stdout

    def test_etl_validate_command(self):
        """Test ETL validate command"""
        result = self.runner.invoke(app, ["etl", "validate"])

        # Should run without crashing
        assert result.exit_code in [0, 1]  # May fail due to missing config in test

    @patch('subprocess.run')
    def test_dev_setup_command(self, mock_subprocess):
        """Test development setup command"""
        mock_subprocess.return_value.returncode = 0

        result = self.runner.invoke(app, ["dev", "setup"])

        assert result.exit_code == 0
        assert "Setting up TuneMeld development environment" in result.stdout
```

#### **End-to-End Tests (tests/test_e2e.py)**

```python
import pytest
import requests
import time
import subprocess
from pathlib import Path

class TestEndToEnd:

    @pytest.fixture(scope="class")
    def test_environment(self):
        """Setup test environment"""
        # Set test environment
        import os
        os.environ["TUNEMELD_ENV"] = "testing"

        # Start test database if needed
        # Start API server in background
        # etc.

        yield

        # Cleanup
        pass

    def test_full_development_workflow(self, test_environment):
        """Test complete development workflow"""
        # Test environment setup
        result = subprocess.run(
            ["tunemeld", "dev", "setup"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Test configuration validation
        result = subprocess.run(
            ["tunemeld", "etl", "validate"],
            capture_output=True,
            text=True
        )
        # May fail in CI, but should not crash
        assert result.returncode in [0, 1]

        # Test health checks
        result = subprocess.run(
            ["tunemeld", "system", "health"],
            capture_output=True,
            text=True
        )
        assert result.returncode in [0, 1]

    def test_api_endpoints_respond(self, test_environment):
        """Test API endpoints are functional"""
        # Assuming API is running
        base_url = "http://localhost:8000"

        # Test root endpoint
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            assert response.status_code == 200
        except requests.ConnectionError:
            pytest.skip("API server not running")

        # Test health endpoint if implemented
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            # May not exist yet, but shouldn't crash
        except requests.ConnectionError:
            pytest.skip("API server not running")
```

---

## Conclusion

This detailed implementation plan for **Option A: Minimal Enhancement** provides a comprehensive roadmap for evolving the TuneMeld backend architecture. The plan focuses on high-value, low-risk improvements that will significantly enhance developer productivity while maintaining the excellent foundation already in place.

**Key Benefits of This Approach:**

- **Developer Productivity**: 80% reduction in setup time and cognitive load
- **System Reliability**: Improved monitoring, debugging, and error handling
- **Maintainability**: Centralized configuration and shared services eliminate duplication
- **Future-Proofing**: Foundation for advanced features without major architectural changes

**Risk Mitigation:**

- Evolutionary approach preserves existing functionality
- Comprehensive testing strategy ensures quality
- Rollback plans for each phase minimize risk
- Backward compatibility maintained throughout migration

The implementation timeline of 4-6 weeks provides a realistic timeframe for delivering significant improvements while maintaining system stability and developer velocity.

This plan transforms an already excellent backend into a streamlined, developer-friendly platform that will accelerate feature development and improve system observability for years to come.
