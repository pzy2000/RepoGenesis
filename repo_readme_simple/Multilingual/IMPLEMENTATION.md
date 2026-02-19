# Implementation Guide

This document provides guidance for implementing the Multilingual and Multi-Timezone Support Service API.

## Overview

You need to implement a Flask web service with 4 RESTful API endpoints that handle multilingual translation and timezone operations.

## API Endpoints to Implement

### 1. POST /api/translate
Translate text between languages.

**Required functionality:**
- Accept JSON with `text`, `source_lang`, and `target_lang`
- Translate the text using a translation library (e.g., googletrans)
- Return JSON with translation results
- Handle errors gracefully

### 2. POST /api/timezone
Convert datetime between timezones.

**Required functionality:**
- Accept JSON with `datetime`, `from_timezone`, and `to_timezone`
- Parse the ISO format datetime string
- Convert between timezones using pytz
- Return JSON with converted datetime
- Handle errors gracefully

### 3. POST /api/localize
Format datetime according to locale.

**Required functionality:**
- Accept JSON with `datetime`, `timezone`, and `locale`
- Parse and localize the datetime
- Format according to locale preferences
- Return JSON with formatted datetime
- Handle errors gracefully

### 4. GET /api/languages
Return list of supported languages.

**Required functionality:**
- Return a dictionary of supported language codes and names
- No input parameters required
- Format: `{"language_code": "language_name", ...}`

## Suggested Implementation Structure

```
Multilingual/
├── app.py                 # Main Flask application (TO BE IMPLEMENTED)
├── README.md              # Project documentation (PROVIDED)
├── requirements.txt       # Dependencies (PROVIDED)
├── IMPLEMENTATION.md      # This file
└── tests/                 # Test suite (PROVIDED)
    ├── __init__.py
    ├── README.md
    ├── test_translate.py
    ├── test_timezone.py
    ├── test_localize.py
    ├── test_languages.py
    └── run_all_tests.py
```

## Sample Code Structure

Here's a basic structure for `app.py`:

```python
from flask import Flask, request, jsonify
from googletrans import Translator
import pytz
from datetime import datetime

app = Flask(__name__)
translator = Translator()

@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        # Validate required fields
        text = data.get('text')
        source_lang = data.get('source_lang')
        target_lang = data.get('target_lang')
        
        if not all([text, source_lang, target_lang]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Perform translation
        # ... implementation ...
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/timezone', methods=['POST'])
def convert_timezone():
    try:
        data = request.get_json()
        # Validate and convert timezone
        # ... implementation ...
        
        return jsonify({
            'success': True,
            'original_datetime': original_dt_str,
            'converted_datetime': converted_dt_str,
            'from_timezone': from_tz,
            'to_timezone': to_tz
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/localize', methods=['POST'])
def localize_datetime():
    try:
        data = request.get_json()
        # Validate and localize datetime
        # ... implementation ...
        
        return jsonify({
            'success': True,
            'formatted_datetime': formatted_str,
            'timezone': timezone,
            'locale': locale
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    try:
        # Return supported languages
        languages = {
            'en': 'English',
            'zh-cn': 'Chinese (Simplified)',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            # Add more languages...
        }
        
        return jsonify({
            'success': True,
            'languages': languages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Implementation Tips

### Translation Endpoint
1. Use the `googletrans` library for translation
2. Handle the case where source and target languages are the same
3. Validate language codes before attempting translation
4. Handle empty strings appropriately

### Timezone Endpoint
1. Use `pytz` for timezone operations
2. Parse ISO format datetime strings using `datetime.fromisoformat()`
3. Use `pytz.timezone()` to get timezone objects
4. Convert using `.astimezone()` method
5. Format output as ISO strings with timezone info

### Localization Endpoint
1. Combine timezone conversion with locale formatting
2. Use `datetime.strftime()` for basic formatting
3. Consider using `babel` library for more sophisticated locale formatting
4. Different locales may have different date/time formats

### Languages Endpoint
1. Provide a comprehensive but manageable list of languages
2. Include at least common languages: English, Chinese, Spanish, French, German, Japanese
3. Use standard ISO 639-1 language codes
4. Format should be simple key-value pairs

## Error Handling

All endpoints should handle errors gracefully and return appropriate HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid input (missing fields, invalid format)
- **500 Internal Server Error**: Server-side errors

Error response format:
```json
{
  "success": false,
  "error": "Description of the error"
}
```

## Testing Your Implementation

1. Start your service:
```bash
python app.py
```

2. Run the test suite:
```bash
cd tests
python run_all_tests.py
```

3. Check individual endpoints:
```bash
python test_translate.py
python test_timezone.py
python test_localize.py
python test_languages.py
```

## Success Criteria

Your implementation should:
- ✓ Pass all 33 test cases
- ✓ Achieve 100% test case pass rate
- ✓ Achieve 100% repository pass rate
- ✓ Handle all error cases gracefully
- ✓ Follow the API specification in README.md
- ✓ Return responses in the correct JSON format

## Common Pitfalls

1. **Timezone conversion errors**: Make sure to properly handle timezone-aware and timezone-naive datetimes
2. **Translation library limitations**: The googletrans library may have rate limits or connection issues
3. **Locale formatting**: Not all locales may be available on all systems
4. **Error handling**: Don't let exceptions crash the server; catch and return error responses
5. **Input validation**: Always validate required fields before processing

## Additional Resources

- Flask documentation: https://flask.palletsprojects.com/
- pytz documentation: https://pythonhosted.org/pytz/
- googletrans documentation: https://py-googletrans.readthedocs.io/
- ISO 639-1 language codes: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
- IANA timezone database: https://www.iana.org/time-zones

## Next Steps

1. Read the API specification in README.md
2. Install dependencies: `pip install -r requirements.txt`
3. Implement `app.py` following this guide
4. Run tests to verify your implementation
5. Iterate until all tests pass

