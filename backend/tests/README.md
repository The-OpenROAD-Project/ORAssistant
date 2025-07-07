# ORAssistant Backend Testing Framework

This directory contains the comprehensive unit testing framework for the ORAssistant backend, built with pytest and coverage reporting.

## 🚀 Quick Start

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run only unit tests
make test-unit

# Run with verbose output
make test-verbose
```

## 📁 Structure

```
tests/
├── conftest.py              # Global test configuration and fixtures
├── test_api_healthcheck.py  # API endpoint tests
├── test_base_chain.py       # BaseChain class tests
├── test_faiss_vectorstore.py # FAISS vector database tests
├── run_tests.py             # Standalone test runner
├── data/                    # Test data files
│   └── sample.md            # Sample markdown for testing
└── README.md                # This file
```

## 🔧 Configuration

### Pytest Configuration (pyproject.toml)

- **Test Discovery**: Automatically finds `test_*.py` files
- **Coverage**: 15% minimum coverage threshold
- **Markers**: `unit`, `integration`, `slow` for test categorization
- **Async Support**: Auto-mode for async test functions
- **Reports**: HTML, XML, and terminal coverage reports

### Coverage Configuration

- **Source**: `src/` directory
- **Omit**: Test files, cache, virtual environments
- **Reports**: HTML (`htmlcov/`), XML (`coverage.xml`), terminal
- **Exclusions**: Debug code, abstract methods, `__repr__` methods

## 📊 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and classes in isolation
- Use mocking for external dependencies
- Fast execution, no external services

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May use real services in test environment
- Slower execution

### Slow Tests (`@pytest.mark.slow`)
- Performance tests, large data processing
- Can be skipped with `make test-fast`

## 🛠️ Available Make Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage reporting |
| `make test-unit` | Run only unit tests |
| `make test-integration` | Run only integration tests |
| `make test-fast` | Skip slow tests |
| `make test-verbose` | Verbose output with short tracebacks |
| `make test-parallel` | Run tests in parallel |
| `make test-html` | Generate HTML test report |
| `make clean-test` | Clean test artifacts |

## 📋 Test Reports

### Coverage Report
- **HTML**: `htmlcov/index.html` - Interactive coverage report
- **XML**: `coverage.xml` - Machine-readable coverage data
- **Terminal**: Line-by-line coverage summary

### Test Report
- **HTML**: `reports/report.html` - Detailed test execution report
- **Terminal**: Real-time test progress and results

## 🔍 Writing Tests

### Basic Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestMyClass:
    """Test suite for MyClass."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        instance = MyClass()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.unit
    def test_with_mocking(self):
        """Test with mocked dependencies."""
        with patch('module.dependency') as mock_dep:
            mock_dep.return_value = Mock()
            
            # Test implementation
            pass
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function."""
        result = await async_function()
        assert result is not None
```

### Available Fixtures

- `test_data_dir`: Path to test data directory
- `mock_openai_client`: Mocked OpenAI client
- `mock_langchain_llm`: Mocked LangChain LLM
- `mock_faiss_vectorstore`: Mocked FAISS vectorstore
- `temp_dir`: Temporary directory for test files
- `sample_documents`: Sample document data
- `mock_env_vars`: Mocked environment variables

### Test Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow test
@pytest.mark.asyncio       # Async test
```

## 🐛 Debugging Tests

### Run Single Test
```bash
pytest tests/test_base_chain.py::TestBaseChain::test_init_with_all_parameters -v
```

### Run with PDB
```bash
pytest --pdb tests/test_base_chain.py
```

### Show Test Output
```bash
pytest -s tests/test_base_chain.py
```

## 📈 Coverage Goals

- **Current Coverage**: 15.89%
- **Target Coverage**: 80% (long-term goal)
- **Critical Paths**: API endpoints, core business logic
- **Exclude**: Configuration files, external integrations

## 🔄 CI/CD Integration

The testing framework is designed to integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Tests
  run: |
    cd backend
    make test-cov
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

## 📚 Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Mocking**: Mock external dependencies for unit tests
4. **Test Data**: Use fixtures for reusable test data
5. **Coverage**: Aim for high coverage of critical paths
6. **Performance**: Keep unit tests fast, mark slow tests appropriately

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**: Check that `src/` is in Python path (handled by `conftest.py`)
2. **Async Tests**: Use `@pytest.mark.asyncio` for async functions
3. **Coverage Not Found**: Ensure tests are in the correct directory structure
4. **Mocking Issues**: Check that the correct module path is being mocked

### Environment Issues

```bash
# Reinstall test dependencies
pip install -r requirements-test.txt

# Clear pytest cache
rm -rf .pytest_cache

# Clean coverage data
make clean-test
```

## 📞 Support

For questions or issues with the testing framework:

1. Check this README for common solutions
2. Review existing test files for examples
3. Check pytest documentation for advanced features
4. Create an issue in the project repository