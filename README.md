# Python Calculator

## Run

- Interactive mode:

```bash
python calculator.py
```

- One-shot expression:

```bash
python calculator.py "sqrt(9) + 2**3"
```

## View in a browser (HTML)

1) Start the local web server:

```bash
python web_calculator.py
```

2) Open this in your browser:

- `http://127.0.0.1:8000/`

Notes:
- If you open `calculator.html` using another server (e.g. VS Code / Cursor “Live Server” on `:5500`), it will still work as long as `web_calculator.py` is running.

## Supported

- Operators: `+ - * / % **` and parentheses `()`
- Functions: `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `ln`, `exp`, `abs`, `round`, `floor`, `ceil`
- Constants: `pi`, `e`, `tau`
- In interactive mode, use `_` for the previous result
