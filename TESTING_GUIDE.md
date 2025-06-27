# TuneMeld Testing & Development Guide

This guide explains how to test and run the TuneMeld music playlist aggregation platform locally.

## 🚀 Quick Start

**Start the website locally:**

```bash
make serve
```

Visit: `http://localhost:8080`

**Run all tests:**

```bash
make test
```

## 🧪 Testing Commands

### Basic Testing

| Command              | Purpose                         | When to Use                                 |
| -------------------- | ------------------------------- | ------------------------------------------- |
| `make test`          | Run all unit tests              | Daily development, before commits           |
| `make test-unit`     | Fast unit tests only            | Quick feedback loop (63 tests, ~10 seconds) |
| `make test-coverage` | Tests with HTML coverage report | Before releases, checking test completeness |

### Advanced Testing

| Command                 | Purpose                         | When to Use                                            |
| ----------------------- | ------------------------------- | ------------------------------------------------------ |
| `make test-integration` | End-to-end ETL pipeline tests   | Testing complete data flow Extract→Transform→Aggregate |
| `make test-slow`        | Performance benchmarks          | Before production deployment                           |
| `make test-all`         | Everything including slow tests | Pre-release validation                                 |
| `make test-ci`          | Exactly as CI pipeline runs     | Debugging CI failures locally                          |

### Test Categories

Tests are organized with markers for different scenarios:

- **Unit Tests**: Fast, isolated component tests
- **Integration Tests** (`@pytest.mark.integration`): End-to-end pipeline validation
- **Slow Tests** (`@pytest.mark.slow`): Performance benchmarks (>10 seconds)
- **External API Tests** (`@pytest.mark.external_api`): Real Spotify/Apple Music calls (skipped by default)

## 🌐 Website & Development

### Local Development

| Command               | Purpose                  | When to Use                                   |
| --------------------- | ------------------------ | --------------------------------------------- |
| `make serve`          | Start frontend website   | View playlist aggregation results             |
| `make serve-frontend` | Same as above (explicit) | Alternative command                           |
| `make build_locally`  | Start Django backend     | API development (has config issues currently) |

### Code Quality

| Command                   | Purpose                     | When to Use                              |
| ------------------------- | --------------------------- | ---------------------------------------- |
| `make format`             | Auto-format code with ruff  | Before commits (or use pre-commit hooks) |
| `make lint`               | Check code quality & style  | Before pull requests                     |
| `make install-pre-commit` | Set up automatic formatting | One-time setup for development           |

## 📊 Understanding Test Results

### Test Structure

```
tests/
├── aggregate_test.py      # Cross-service track aggregation (19 tests)
├── extract_test.py        # API data extraction (34 tests)
├── transform_test.py      # Data transformation (25 tests)
├── integration_test.py    # End-to-end pipeline (5 tests)
├── utils_test.py          # WebDriver utilities (4 tests)
└── conftest.py           # Test fixtures & mock data
```

### Expected Results

- **Total Tests**: 87 tests
- **Passing**: 78+ tests (should be 100% for unit tests)
- **Skipped**: External API tests (run with `-m external_api` to include)
- **Coverage**: 80%+ for core modules

## 🎯 Common Workflows

### Daily Development

```bash
# Quick test cycle
make test-unit          # ~10 seconds
make serve             # View results

# Full validation
make test-coverage     # ~30 seconds with report
```

### Before Committing

```bash
make format            # Auto-format code
make lint              # Check quality
make test              # Full test suite
```

### Debugging ETL Pipeline

```bash
# Test individual components
pytest tests/extract_test.py -v          # Data extraction
pytest tests/transform_test.py -v        # Data transformation
pytest tests/aggregate_test.py -v        # Cross-service aggregation

# Test end-to-end flow
make test-integration
```

### Testing with Real Data

```bash
# Analyze current MongoDB data structure
python analyze_mongo_data.py

# Run integration tests with realistic data patterns
make test-integration

# View results on website
make serve
```

## 🔧 ETL Pipeline Testing

The TuneMeld ETL pipeline processes music data in three stages:

1. **Extract** (`playlist_etl/extract.py`): Fetch playlists from Spotify, Apple Music, SoundCloud
2. **Transform** (`playlist_etl/transform2.py`): Normalize data formats, resolve ISRCs
3. **Aggregate** (`playlist_etl/aggregate2.py`): Cross-service matching and ranking

### Pipeline Test Coverage

| Component          | Tests    | Coverage                                                |
| ------------------ | -------- | ------------------------------------------------------- |
| **Extraction**     | 34 tests | API clients, service configs, error handling            |
| **Transformation** | 25 tests | Data conversion, ISRC resolution, concurrent processing |
| **Aggregation**    | 19 tests | Cross-service matching, ranking algorithms              |
| **Integration**    | 5 tests  | End-to-end pipeline, performance benchmarks             |

### Integration Test Scenarios

```bash
# Test complete ETL pipeline
pytest tests/integration_test.py::TestETLPipelineIntegration::test_complete_etl_pipeline_single_genre -v

# Test multi-genre scalability
pytest tests/integration_test.py::TestETLPipelineIntegration::test_multi_genre_pipeline_integration -v

# Test error recovery
pytest tests/integration_test.py::TestETLPipelineIntegration::test_error_recovery_and_resilience -v
```

## 🐛 Troubleshooting

### Common Issues

**Tests failing locally but pass in CI:**

```bash
make test-ci    # Run exactly as CI does
```

**WebDriver tests hanging:**

```bash
# Skip external API tests (default behavior)
make test-unit

# Or run them specifically (requires Chrome)
pytest tests/utils_test.py -m external_api -v
```

**MongoDB connection errors in tests:**

```bash
# Tests use mocked MongoDB - no real connection needed
# If seeing connection errors, check test fixtures in conftest.py
```

**Django backend won't start:**

```bash
# Use frontend only (recommended for viewing results)
make serve

# For Django backend, set environment variables:
ALLOWED_HOSTS="localhost,127.0.0.1" MONGO_DB_NAME="tunemeld" make build_locally
```

### Test Data

Tests use realistic mock data based on actual MongoDB structure:

- **ISRCs**: Real format (e.g., "USA2P2446028")
- **Track Data**: Actual song names and artists
- **Service APIs**: Mocked with realistic response formats
- **Cross-Service Matching**: Tests with overlapping track data

## 📈 Performance Expectations

| Test Type         | Duration      | Purpose                |
| ----------------- | ------------- | ---------------------- |
| Unit Tests        | 10-30 seconds | Fast feedback          |
| Integration Tests | 30-60 seconds | Pipeline validation    |
| Slow Tests        | 1-5 minutes   | Performance benchmarks |
| Full Suite        | 1-2 minutes   | Complete validation    |

## 🎵 Website Features

When running `make serve`, you'll see:

- **Genre Pages**: dance, pop, rap, country music aggregation
- **Service Playlists**: Spotify, Apple Music, SoundCloud data
- **Cross-Platform Matching**: Tracks appearing on multiple services
- **Cover Art & Metadata**: Visual playlist browsing
- **Ranking Algorithms**: Service priority and track positioning

## 📝 Contributing

Before submitting changes:

1. **Format code**: `make format`
2. **Run tests**: `make test-coverage`
3. **Check quality**: `make lint`
4. **Test website**: `make serve`
5. **Verify integration**: `make test-integration`

The pre-commit hooks will automatically format code on commit, ensuring consistent style across the codebase.

---

## 💡 Pro Tips

- Use `make test-unit` for rapid development cycles
- Use `make serve` to see your data processing results visually
- Use `make test-integration` to validate end-to-end data flow
- Check `coverage.html` after `make test-coverage` for detailed test coverage
- Integration tests simulate realistic cross-service data scenarios

Happy testing! 🎉
