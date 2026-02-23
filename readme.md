## Creating Environment

```powershell
python -m venv fastapienv
```

## Activating Environment

PowerShell:

```powershell
.\fastapienv\Scripts\Activate.ps1
```

Command Prompt (CMD):

```cmd
fastapienv\Scripts\activate.bat
```

Deactivate (both shells):

```text
deactivate
```

## Spinning the Application (Uvicorn)

From project folder (example: `TodoApp`):

```powershell
uvicorn main:app --reload
```

Useful variants:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
uvicorn main:app --port 9000 --reload
```

## Useful Commands (Short Cheat Sheet)

Install deps:

```powershell
pip install fastapi uvicorn sqlalchemy
```

Freeze deps:

```powershell
pip freeze > requirements.txt
```

Install from requirements:

```powershell
pip install -r requirements.txt
```

Show installed packages:

```powershell
pip list
```

Run from repo root without `cd`:

```powershell
uvicorn TodoApp.main:app --reload
```

## What is Uvicorn? (brief)

- Uvicorn is an ASGI server used to run FastAPI apps.
- FastAPI is the framework; Uvicorn is the server process that serves requests.
- Name origin: "Uvicorn" comes from **uvloop** + **httptools** (the high-performance components it was built around).
