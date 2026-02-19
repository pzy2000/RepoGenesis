# Quick Start Guide

This guide helps you get started with implementing and testing the Multilingual API benchmark project.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- pytz (timezone handling)
- googletrans (translation)
- requests (HTTP client for tests)
- pytest (testing framework)

## Step 2: Implement the Service

Create a file named `app.py` in the project root with the following endpoints:

1. `POST /api/translate` - Translate text between languages
2. `POST /api/timezone` - Convert datetime between timezones
3. `POST /api/localize` - Format datetime with locale
4. `GET /api/languages` - Get supported languages

See `IMPLEMENTATION.md` for detailed implementation guidance and code examples.

## Step 3: Run Your Service

```bash
python app.py
```

The service should start on `http://localhost:5000`

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
```

## Step 4: Test in Another Terminal

Open a new terminal window and run:

```bash
cd tests
python run_all_tests.py
```

## Expected Output

If all tests pass, you should see:

```
======================================================================
METRICS
======================================================================
Test Case Pass Rate:
  - Total Tests: 33
  - Passed: 33
  - Failed: 0
  - Pass Rate: 100.00%

Repository Pass Rate:
  - Total Test Files: 4
  - Passed: 4
  - Failed: 0
  - Pass Rate: 100.00%
======================================================================

✓ All tests passed!
```

## Quick Test Individual Endpoints

### Test Translation
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_lang": "en", "target_lang": "zh-cn"}'
```

### Test Timezone Conversion
```bash
curl -X POST http://localhost:5000/api/timezone \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2025-10-30T12:00:00", "from_timezone": "UTC", "to_timezone": "Asia/Shanghai"}'
```

### Test Localization
```bash
curl -X POST http://localhost:5000/api/localize \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2025-10-30T12:00:00", "timezone": "UTC", "locale": "en_US"}'
```

### Test Languages List
```bash
curl http://localhost:5000/api/languages
```

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, either:
1. Stop the other service using port 5000
2. Modify the port in `app.py` and update `BASE_URL` in test files

### Import Errors
Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Translation Not Working
The `googletrans` library sometimes has connectivity issues. If you encounter problems:
1. Check your internet connection
2. Try using a different translation library
3. Implement a simple mock translator for testing purposes

### Tests Fail Immediately
Make sure your service is running before running tests:
```bash
# Terminal 1
python app.py

# Terminal 2
cd tests
python run_all_tests.py
```

## Next Steps

1. ✓ Install dependencies
2. ✓ Read API specification in `README.md`
3. ✓ Review implementation guide in `IMPLEMENTATION.md`
4. ✓ Implement `app.py`
5. ✓ Run the service
6. ✓ Run tests
7. ✓ Fix any failing tests
8. ✓ Achieve 100% pass rate

## Tips for Success

- Start with the `/api/languages` endpoint (easiest)
- Test each endpoint manually with curl before running the full test suite
- Read error messages carefully - they tell you what's expected
- Use the test files as examples of expected behavior
- Don't forget error handling - many tests check error cases
- Validate all required fields before processing

## Getting Help

- Check `README.md` for API specifications
- Check `IMPLEMENTATION.md` for implementation examples
- Check `tests/README.md` for test documentation
- Look at individual test files to understand expected behavior
- Review `PROJECT_OVERVIEW.md` for project context

## Time Estimate

- Installation: 5 minutes
- Reading documentation: 15-20 minutes
- Implementation: 30-120 minutes (depending on experience)
- Testing and debugging: 15-30 minutes

**Total**: 1-3 hours for a complete implementation

Good luck! 🚀

