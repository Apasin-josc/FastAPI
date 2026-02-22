# TodoApp - Setup Step by Step

Este proyecto usa FastAPI + SQLAlchemy + SQLite en Windows (PowerShell).

## 1. Crear carpeta del proyecto

```powershell
mkdir C:\Users\joseo\Documents\fastapi
cd C:\Users\joseo\Documents\fastapi
```

## 2. Crear entorno virtual

```powershell
python -m venv fastapienv
```

## 3. Activar entorno virtual

```powershell
.\fastapienv\Scripts\Activate.ps1
```

Cuando esta activo, la terminal muestra `(fastapienv)`.

## 4. Instalar dependencias

```powershell
pip install fastapi uvicorn sqlalchemy
```

## 5. Crear carpeta de la aplicacion

```powershell
mkdir TodoApp
cd TodoApp
```

## 6. Crear archivos base

Crea estos archivos dentro de `TodoApp`:

- `__init__.py`
- `database.py`
- `models.py`
- `main.py`

## 7. Configurar base de datos (`database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

Nota: la clave correcta es `check_same_thread` (todo en minusculas).

## 8. Crear modelo (`models.py`)

```python
from database import Base
from sqlalchemy import Column, Integer, String, Boolean

class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
```

## 9. Crear aplicacion inicial (`main.py`)

```python
from fastapi import FastAPI
import models
from database import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
```

`create_all()` crea la tabla en `todos.db` al iniciar la app.

## 10. Session de DB, dependency injection, `single_todo`, `create_todo`, `update_todo` y `delete_todo` en `main.py`

En esta sesion agregaste el manejo de sesion con `SessionLocal`, el dependency provider `get_db()`, endpoints para listar, buscar por id, crear, actualizar y eliminar todos.

```python
from fastapi import FastAPI, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from starlette import status
import models
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from models import Todos

app = FastAPI()

# this is going to run if our todos.db does not exist
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool

@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency):
    return db.query(Todos).all()

@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail='Todo not found buddy.')

@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = Todos(**todo_request.model_dump())
    db.add(todo_model)
    db.commit()

@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    db: db_dependency,
    todo_request: TodoRequest,
    todo_id: int = Path(gt=0)
):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found buddy.')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found buddy.')

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
```

Que hace cada parte:

- `SessionLocal`: fabrica sesiones para conectarte a SQLite.
- `get_db()`: abre una sesion por request y la cierra al terminar.
- `Depends(get_db)`: inyecta la sesion en cada endpoint.
- `read_all`: devuelve todos los registros de la tabla `todos`.
- `read_todo`: devuelve un solo registro por id; si no existe, responde 404.
- `TodoRequest`: esquema de entrada para validar el body del `POST`.
- `create_todo`: crea un registro nuevo en la tabla `todos`.
- `update_todo`: reemplaza los datos de un todo existente por id.
- `delete_todo`: elimina un todo por id.

### Imports explicados

- `FastAPI`: crea la aplicacion web.
- `Depends`: habilita dependency injection (inyectar dependencias como la sesion DB).
- `HTTPException`: lanza errores HTTP controlados (ejemplo: 404).
- `Path`: valida parametros de ruta; `Path(gt=0)` exige id mayor que 0.
- `BaseModel`: clase base de Pydantic para schemas de request/response.
- `Field`: agrega validaciones a cada campo del schema.
- `status` (de `starlette`): constantes para codigos HTTP (`HTTP_200_OK`, etc.).
- `engine`: conexion base a la DB.
- `SessionLocal`: fabrica de sesiones SQLAlchemy.
- `Annotated`: combina tipo + dependencia en `db_dependency`.
- `Session`: tipo de sesion de SQLAlchemy.
- `Todos`: modelo ORM de la tabla `todos`.

## 11. Ejecutar servidor

Desde `C:\Users\joseo\Documents\fastapi\TodoApp`:

```powershell
uvicorn main:app --reload
```

## 12. Abrir en navegador

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## 13. Probar lectura de datos

- `GET /` devuelve todos los todos.
- `GET /todo/1` devuelve el todo con id `1` si existe.
- Si no existe, responde: `404 Todo not found buddy.`
- `POST /todo` crea un todo nuevo.
- `PUT /todo/1` actualiza un todo existente y responde `204 No Content`.
- `DELETE /todo/1` elimina un todo existente y responde `204 No Content`.

Body de ejemplo para `POST /todo`:

```json
{
  "title": "Study FastAPI",
  "description": "Finish todo CRUD tutorial",
  "priority": 3,
  "complete": false
}
```

Body de ejemplo para `PUT /todo/1`:

```json
{
  "title": "Study FastAPI Advanced",
  "description": "Update existing todo with PUT",
  "priority": 4,
  "complete": true
}
```

Notas del `PUT`:

- Debes enviar todos los campos del `TodoRequest`.
- Si el `todo_id` no existe, devuelve `404`.
- Si el body no cumple validaciones, FastAPI devuelve `422`.

Notas del `DELETE`:

- Si el `todo_id` no existe, devuelve `404`.
- Si existe y se elimina correctamente, devuelve `204 No Content`.

## 14. Accediendo a la DB desde terminal (opcional)

```powershell
sqlite3 todos.db
```

Comandos utiles:

```sql
.schema
select * from todos;
.mode table
select * from todos;
```

## 15. Estructura final esperada

```text
fastapi/
  fastapienv/
  TodoApp/
    __init__.py
    database.py
    models.py
    main.py
    readme.md
    todos.db
```

## 16. Como nace `db` en FastAPI (explicacion simple)

Esta es la parte que mas confunde al inicio, y es normal.

### Que hace `__init__.py`

- Le dice a Python que `TodoApp` se comporta como paquete.
- Permite imports entre archivos del proyecto.
- Puede estar vacio y sigue siendo util.

### Que hace `database.py`

- `engine`: conexion principal/configuracion de SQLAlchemy.
- `SessionLocal`: fabrica que crea sesiones de base de datos.
- `Base`: clase base para tus modelos ORM (`Todos`, etc.).

### Como aparece la variable `db` en los endpoints

No aparece de la nada: FastAPI la inyecta con `Depends(get_db)`.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
async def read_all(db: db_dependency):
    return db.query(Todos).all()
```

Flujo por request:

1. Llega una peticion a un endpoint.
2. FastAPI ve `Depends(get_db)`.
3. Ejecuta `get_db()` y crea `db = SessionLocal()`.
4. Inyecta esa `db` como parametro del endpoint.
5. Tu codigo usa `db.query(...)`.
6. Al terminar, se ejecuta `finally` y se cierra con `db.close()`.

Piensalo asi: `database.py` prepara la fabrica, `get_db()` crea una sesion por request, y FastAPI te la entrega en `db`.

## Errores comunes

- `TypeError: 'check_Same_thread' is an invalid keyword argument for Connection()`

Causa: typo en `database.py`.

Solucion:

- incorrecto: `check_Same_thread`
- correcto: `check_same_thread`
