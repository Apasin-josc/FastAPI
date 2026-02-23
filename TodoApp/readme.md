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

En esta sesion agregamos el manejo de sesion con `SessionLocal`, el dependency provider `get_db()` y endpoints para listar, buscar por id, crear, actualizar y eliminar todos.

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

## 17. Starting Authentication & Authorization

En esta parte empezaste la estructura de autenticacion/autorizacion separando rutas en un router dedicado.

Objetivo de este paso:

- preparar un archivo de auth separado del `main.py`
- escalar mejor la app por modulos
- dejar lista la base para agregar login, JWT, y proteccion de endpoints despues

## 18. Routers Scale Authentication File

### 1. Crear carpeta y archivo de router

Ruta usada:

- `TodoApp/routers/auth.py`
- `TodoApp/routers/__init__.py`

Codigo actual en `TodoApp/routers/auth.py`:

```python
from fastapi import APIRouter

"""
APIRouter will allow us to be able to route from our main.py file to our auth.py file
"""

router = APIRouter()

@router.get("/auth/")
async def get_user():
    return {'user': 'authenticated'}
```

### 2. Conectar el router en `main.py`

Agregaste import e inclusion del router:

```python
from routers import auth

app.include_router(
    auth.router
)
```

Con esto, el endpoint de auth ya queda disponible en:

- `GET /auth/`

Respuesta esperada:

```json
{
  "user": "authenticated"
}
```

Nota: en esta fase todavia no hay validacion real de usuario (no JWT/no password hash). Es una base para el modulo de auth que sigue en el curso.

## 19. FastAPI Project: Router Scale Todos File

En esta sesion moviste todo el CRUD de todos fuera de `main.py` para dejar la aplicacion mas limpia y escalable.

### 1. Crear router de todos

Archivo usado:

- `TodoApp/routers/todos.py`

En este archivo dejamos:

- `router = APIRouter()`
- `get_db()` y `db_dependency`
- `TodoRequest` (schema de Pydantic)
- endpoints CRUD:
  - `GET /`
  - `GET /todo/{todo_id}`
  - `POST /todo`
  - `PUT /todo/{todo_id}`
  - `DELETE /todo/{todo_id}`

### 2. Limpiar `main.py`

Ahora `main.py` queda como punto de arranque y registro de routers:

```python
from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos

app = FastAPI()

# this is going to run if our todos.db does not exist
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)
```

### 3. Resultado de esta refactorizacion

- `main.py` queda corto y facil de leer.
- Cada modulo maneja su responsabilidad (`auth.py`, `todos.py`).
- Es mas facil crecer el proyecto (ejemplo: `users.py`, `admin.py`, `health.py`).

Nota: en este punto los endpoints no cambian, solo cambia la organizacion del codigo.

## 20. Users Table + Foreign Key (One-to-Many)

En esta sesion agregamos una tabla `users` y conectamos `todos` con `users` usando una clave foranea.

Cambios en `TodoApp/models.py`:

- nuevo modelo `Users`
- nuevo campo `owner_id` en `Todos`
- `owner_id` apunta a `users.id` con `ForeignKey("users.id")`

Codigo actual (resumen):

```python
class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)

class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
```

### Que significa One-to-Many

- One (`Users`): un usuario.
- Many (`Todos`): muchos todos.

Interpretacion:

- un usuario puede tener muchos todos
- cada todo pertenece a un solo usuario (por `owner_id`)

### Diagrama rapido (ERD)

```text
users
-----
id (PK)
email (UNIQUE)
username (UNIQUE)
first_name
last_name
hashed_password
is_active
role
   1
   |
   |  (owner_id -> users.id)
   |
   * 
todos
-----
id (PK)
title
description
priority
complete
owner_id (FK)
```

### Ejemplo de relacion

Si existe:

- `users.id = 3`

Entonces todos estos registros pueden ser del mismo usuario:

- `todos.owner_id = 3` (todo A)
- `todos.owner_id = 3` (todo B)
- `todos.owner_id = 3` (todo C)

### Nota importante para SQLite local

Si ya tenia creado `todos.db` antes de este cambio, es posible que mi DB vieja no tenga la estructura nueva.

Opciones rapidas durante aprendizaje:

1. borrar `todos.db` y volver a correr la app para recrear tablas
2. usar migraciones (Alembic) cuando quieras manejar cambios sin borrar datos

## 21. First User Creation (Auth) and Why Not `model_dump`

En esta sesion creaste tu primer endpoint para registrar usuario en `TodoApp/routers/auth.py`.

Modelo request actual:

```python
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
```

Endpoint actual:

```python
@router.post("/auth/")
async def create_user(create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=create_user_request.password,
        is_active=True
    )

    return create_user_model
```

### Por que aqui no usaste `**todo_request.model_dump()`

En `todos`, el request se parece mucho a la tabla y podia hacer unpack directo.

En `users`, la logica cambia:

- el cliente envia `password`
- en DB guardas `hashed_password`

Entonces no conviene copiar todo directo. Es mejor mapear campo por campo para transformar datos sensibles.

### Nota de seguridad (siguiente paso del curso)

Ahora mismo `hashed_password` esta recibiendo `password` sin hash real.

Lo correcto es:

- hashear con `bcrypt` (o similar)
- guardar solo el hash en `hashed_password`
- nunca guardar el password plano en la DB

## 22. Password Hashing with `passlib` + `bcrypt==4.0.1`

En esta sesion agregamos hashing real para contrasenas de usuarios.

Instalacion que hice:

```powershell
pip install passlib
pip install bcrypt==4.0.1
```

Nota del curso: fijamos la version `bcrypt==4.0.1` para evitar problemas de compatibilidad con `passlib` en este entorno.

Cambios en `TodoApp/routers/auth.py`:

- import de `CryptContext`
- creacion de `bcrypt_context`
- uso de `bcrypt_context.hash(...)` al crear usuario

```python
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@router.post("/auth")
async def create_user(create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True
    )

    return create_user_model
```

### Que gano esta mejora

- ya no guardas passwords en texto plano
- en DB se guarda solo `hashed_password`
- mejora base de seguridad para login/autorizacion en los siguientes pasos

## Errores comunes

- `TypeError: 'check_Same_thread' is an invalid keyword argument for Connection()`

Causa: typo en `database.py`.

Solucion:

- incorrecto: `check_Same_thread`
- correcto: `check_same_thread`
