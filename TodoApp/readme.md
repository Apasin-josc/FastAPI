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

## 23. Auth Persisting User in DB (Dependency + Commit)

En esta sesion mejoramos el endpoint de auth para que ya no solo construya el objeto `Users`, sino que tambien lo guarde de verdad en la base de datos.

Cambios que hicimos en `TodoApp/routers/auth.py`:

- agregamos `Depends`, `Annotated`, `SessionLocal` y `Session`
- creamos `get_db()` dentro del router de auth
- definimos `db_dependency = Annotated[Session, Depends(get_db)]`
- el `POST /auth` ahora recibe `db: db_dependency`
- agregamos `status_code=status.HTTP_201_CREATED`
- guardamos el usuario con `db.add(...)` y `db.commit()`

Codigo actual (resumen):

```python
from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from typing import Annotated
from database import SessionLocal
from sqlalchemy.orm import Session
from starlette import status

router = APIRouter()
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True
    )

    db.add(create_user_model)
    db.commit()
```

Que ganamos con este paso:

- el endpoint ya persiste datos en `users` (antes solo retornaba el objeto)
- seguimos guardando password hasheada, no texto plano
- auth queda alineado con el mismo patron de sesion DB que usamos en `todos`

## 24. Login Check with `OAuth2PasswordRequestForm` (`/token`)

En esta sesion agregamos la primera validacion de login en auth.

Que agregamos en `TodoApp/routers/auth.py`:

- import de `OAuth2PasswordRequestForm`
- funcion `authenticate_user(username, password, db)`
- endpoint `POST /token` para validar credenciales
- validacion con `bcrypt_context.verify(...)`

Codigo clave:

```python
from fastapi.security import OAuth2PasswordRequestForm

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return True

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return 'Failed Authentication'
    return 'Successful Authentication'
```

### Que significa este paso

- `OAuth2PasswordRequestForm` espera credenciales tipo formulario (`username` y `password`).
- buscamos al usuario por `username` en DB.
- comparamos password enviada vs `hashed_password` usando `verify`.
- si no coincide: falla autenticacion.
- si coincide: login correcto.

### Nota importante

En este punto todavia no estamos generando JWT real; solo validamos si las credenciales son correctas. El siguiente paso normalmente es crear y devolver un access token.

## 25. JWT Access Token Generation (`/token`)

En esta sesion completamos el login para devolver un access token real (JWT) cuando las credenciales son validas.

Que agregamos en `TodoApp/routers/auth.py`:

- import de `datetime`, `timedelta`, `timezone`
- import de `jwt` desde `python-jose`
- `SECRET_KEY` y `ALGORITHM`
- modelo `Token` con `access_token` y `token_type`
- funcion `create_access_token(...)`
- `response_model=Token` en `POST /token`

Codigo clave:

```python
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = '...'
ALGORITHM = 'HS256'

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return 'Failed Authentication'

    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
```

### Que significa este paso

- si username/password son correctos, ahora devolvemos JWT.
- el token incluye:
  - `sub`: username
  - `id`: user_id
  - `exp`: fecha de expiracion
- definimos expiracion de 20 minutos en este avance.

### Nota practica

- `SECRET_KEY` debe mantenerse privada (idealmente en variables de entorno).
- este token luego se usa en endpoints protegidos con `Authorization: Bearer <token>`.

## 26. Decode JWT + Current User Dependency (`get_current_user`)

En esta sesion agregamos la validacion del token bearer para poder obtener al usuario actual desde el JWT.

Que agregamos en `TodoApp/routers/auth.py`:

- `OAuth2PasswordBearer(tokenUrl='token')`
- import de `JWTError`
- funcion `get_current_user(...)` con `Depends(oauth2_bearer)`
- decode del token con `jwt.decode(...)`
- validacion de claims `sub` e `id`
- `HTTPException(401)` cuando el token es invalido

Codigo clave:

```python
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='could not validate user.'
            )

        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='could not validate user.'
        )
```

### Que significa este paso

- `oauth2_bearer` lee el token desde header `Authorization: Bearer <token>`.
- `get_current_user` decodifica el JWT y extrae datos del usuario.
- si el token falla, responde `401 Unauthorized`.
- esta dependencia se reutiliza en endpoints protegidos del proyecto.

### Nota practica

El `tokenUrl='token'` indica a Swagger/OpenAPI donde pedir el token de login para el flujo OAuth2 password.

## 27. Auth Router Prefix + Better Unauthorized Handling

En esta sesion ordenamos mejor las rutas de auth y alineamos OAuth2 con ese prefijo.

Cambios que hicimos en `TodoApp/routers/auth.py`:

- configuramos el router con:
  - `prefix='/auth'`
  - `tags=['auth']`
- cambiamos `oauth2_bearer` a:
  - `OAuth2PasswordBearer(tokenUrl='auth/token')`
- actualizamos endpoints:
  - crear usuario: `POST /auth/`
  - login token: `POST /auth/token`
- mejoramos el error de login fallido:
  - antes devolviamos string (`'Failed Authentication'`)
  - ahora lanzamos `HTTPException(status_code=401, detail='could not validate user.')`

Codigo clave:

```python
router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='could not validate user.'
        )

    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
```

### Que ganamos con este paso

- rutas de auth mas limpias y agrupadas bajo `/auth`.
- documentacion Swagger mas clara por `tags=['auth']`.
- manejo HTTP correcto para credenciales invalidas (`401` en lugar de string).
- `tokenUrl` consistente para el flujo OAuth2.

## 28. Link Todo Creation to Authenticated User (`owner_id`)

En esta sesion conectamos `todos.py` con auth para que cada todo nuevo quede asociado al usuario autenticado.

Cambios que hicimos en `TodoApp/routers/todos.py`:

- importamos `get_current_user` desde `auth.py`
- creamos la dependencia:
  - `user_dependency = Annotated[dict, Depends(get_current_user)]`
- en `create_todo(...)` recibimos `user: user_dependency`
- validamos usuario autenticado (`401` si falla)
- guardamos `owner_id=user.get('id')` al crear el todo

Codigo clave:

```python
from .auth import get_current_user

user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: TodoRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))
    db.add(todo_model)
    db.commit()
```

### Que ganamos con este paso

- los todos dejan de ser anonimos y ahora quedan ligados a un usuario real.
- empezamos a aplicar autorizacion por ownership (`owner_id`).
- la base queda lista para filtrar endpoints por usuario (ej: ver solo mis todos).

### Siguiente mejora natural

Proteger tambien `GET /`, `GET /todo/{id}`, `PUT` y `DELETE` para que solo trabajen con todos del usuario autenticado.

## 29. Protect `GET /` and Return Only My Todos

En esta sesion dimos otro paso en autorizacion: ahora el listado de todos ya no devuelve todo global, sino solo los todos del usuario autenticado.

Cambios que hicimos en `TodoApp/routers/todos.py`:

- agregamos `user: user_dependency` en `read_all(...)`
- filtramos query por `owner_id == user.get('id')`

Codigo clave:

```python
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
```

### Que ganamos con este paso

- cada usuario ve solo sus propios todos.
- dejamos de exponer todos de otros usuarios en el endpoint de lista.
- reforzamos el modelo de ownership con JWT + `owner_id`.

### Nota

`read_todo`, `update_todo` y `delete_todo` todavia no filtran por `owner_id` en este punto. Ese seria el siguiente hardening para que todo CRUD quede consistente con autorizacion por usuario.

## 30. Protect `GET /todo/{todo_id}` by Owner

En esta sesion seguimos endureciendo autorizacion en `todos.py`.

Cambios que hicimos:

- en `read_all(...)` agregamos validacion explicita:
  - `if user is None: raise HTTPException(401, 'Authentication Failed')`
- en `read_todo(...)` ahora pedimos `user: user_dependency`
- en `read_todo(...)` filtramos por:
  - `Todos.id == todo_id`
  - `Todos.owner_id == user.get('id')`

Codigo clave:

```python
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get('id')).first()

    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail='Todo not found buddy.')
```

### Que ganamos con este paso

- un usuario ya no puede leer por id un todo que no le pertenece.
- reforzamos ownership en lectura de lista y lectura individual.
- respuesta de auth queda consistente (`401`) cuando falta/expira token.

### Siguiente mejora natural

Aplicar la misma logica de ownership a `PUT /todo/{todo_id}` y `DELETE /todo/{todo_id}` para cerrar todo el CRUD protegido.

## 31. Protect `PUT /todo/{todo_id}` by Owner

En esta sesion seguimos cerrando autorizacion en el CRUD y ahora protegimos el update por ownership.

Cambios que hicimos en `TodoApp/routers/todos.py`:

- en `update_todo(...)` agregamos `user: user_dependency`
- validamos token/usuario:
  - `if user is None: raise HTTPException(401, 'Authentication Failed')`
- buscamos el todo por:
  - `Todos.id == todo_id`
  - `Todos.owner_id == user.get('id')`
- si no existe ese registro para ese usuario: `404`

Codigo clave:

```python
@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: TodoRequest,
    todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found buddy.')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()
```

### Que ganamos con este paso

- ya no se puede editar un todo de otro usuario.
- update queda alineado con la seguridad que ya teniamos en lectura.
- ownership del modelo (`owner_id`) se respeta tambien en escritura.

### Siguiente mejora natural

Aplicar la misma regla en `DELETE /todo/{todo_id}` para completar el CRUD protegido por usuario.

## 32. Protect `DELETE /todo/{todo_id}` by Owner (CRUD Fully Secured)

En esta sesion cerramos el hardening del CRUD: ahora delete tambien valida usuario autenticado y ownership.

Cambios que hicimos en `TodoApp/routers/todos.py`:

- en `delete_todo(...)` agregamos `user: user_dependency`
- validamos token/usuario:
  - `if user is None: raise HTTPException(401, 'Authentication Failed')`
- buscamos el todo por:
  - `Todos.id == todo_id`
  - `Todos.owner_id == user.get('id')`
- eliminamos con el mismo filtro de ownership

Codigo clave:

```python
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get('id')).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found buddy.')

    db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get('id')).delete()
    db.commit()
```

### Que ganamos con este paso

- ya no se puede borrar un todo de otro usuario.
- CRUD queda consistente con autorizacion por ownership:
  - `GET /`
  - `GET /todo/{todo_id}`
  - `POST /todo`
  - `PUT /todo/{todo_id}`
  - `DELETE /todo/{todo_id}`
- modelo multiusuario mas seguro y listo para seguir escalando.

## 33. Admin Router (`/admin`) + Role-Based Access

En esta sesion creamos un router exclusivo para admin con endpoints que pueden ver/borrar todos los todos sin filtro por owner.

Archivos tocados:

- `TodoApp/routers/admin.py`
- `TodoApp/main.py`

Cambios que hicimos en `admin.py`:

- creamos router con:
  - `prefix='/admin'`
  - `tags=['admin']`
- reutilizamos `get_current_user` como dependencia de auth
- validamos rol admin antes de ejecutar acciones
- agregamos endpoints:
  - `GET /admin/todo` -> devuelve todos los todos
  - `DELETE /admin/todo/{todo_id}` -> elimina cualquier todo por id

Codigo clave:

```python
router = APIRouter(
    prefix='/admin',
    tags=['admin']
)

@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None or user.get("user_role", "").lower() != "admin":
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return db.query(Todos).all()

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None or user.get('user_role').lower() != 'admin':
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
```

Conexion en `main.py`:

```python
from routers import auth, todos, admin

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
```

### Que ganamos con este paso

- separamos funciones administrativas del flujo normal de usuario.
- dejamos una base clara para control de acceso por rol (RBAC).
- mantenemos `todos.py` enfocado en operaciones del dueño del recurso.

### Nota importante

Para que la validacion de rol funcione al 100%, el `get_current_user` debe devolver `user_role` (o leerlo desde DB/JWT) porque en este punto la validacion usa `user.get("user_role")`.

## 34. User Router (`/user`) + Profile + Change Password

En esta sesion agregamos un router para acciones del usuario autenticado (perfil y cambio de password).

Archivos tocados:

- `TodoApp/routers/users.py`
- `TodoApp/main.py`
- `TodoApp/routers/auth.py`

### 1. Nuevo router de usuario

Creamos `APIRouter` con:

- `prefix='/user'`
- `tags=['user']`

Y lo conectamos en `main.py`:

```python
from routers import auth, todos, admin, users

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
```

### 2. Endpoint para ver mi perfil

En `users.py`:

```python
@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    return db.query(Users).filter(Users.id == user.get('id')).first()
```

Con esto, `GET /user/` devuelve la fila del usuario autenticado.

### 3. Endpoint para cambiar password

Schema:

```python
class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)
```

Endpoint:

```python
@router.put("change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail='Error on password change')

    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
```

Que hace:

- valida usuario autenticado
- verifica password actual contra hash guardado
- hashea el `new_password`
- guarda el nuevo hash en DB

### 4. Ajuste en JWT para soporte de rol

Tambien dejamos `auth.py` devolviendo role en el token y en `get_current_user`:

- `create_access_token(..., role, ...)` guarda claim `role`
- `get_current_user(...)` retorna:
  - `username`
  - `id`
  - `user_role`

Esto alimenta tanto rutas admin como rutas user.

### Nota rapida

En tu codigo actual, el decorator de cambio de password esta como `@router.put("change-password", ...)` (sin `/` inicial). Si quieres mantener consistencia de rutas, normalmente se usa `@router.put("/change-password", ...)`.

## 35. Migracion de SQLite a PostgreSQL (`database.py`)

En esta sesion cambiamos la conexion principal de la app para usar PostgreSQL en lugar de SQLite.

Cambio principal en `TodoApp/database.py`:

```python
# SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:***@127.0.0.1/TodoApplicationDatabase'

# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
engine = create_engine(SQLALCHEMY_DATABASE_URL)
```

### Que cambia al pasar a Postgres

- ya no usamos `connect_args={"check_same_thread": False}` (eso era solo para SQLite).
- la URL ahora apunta a un servidor DB real (`postgresql://...`).
- los datos ya no viven en archivo local `.db`, ahora viven en la instancia de Postgres.

### Dependencia importante

Para conectar SQLAlchemy con PostgreSQL necesitas un driver de Postgres en el entorno (por ejemplo `psycopg2-binary` o `psycopg`).

Ejemplo rapido:

```powershell
pip install psycopg2-binary
```

### Recomendacion de seguridad

Evitar credenciales hardcodeadas en el repo.

Mejor opcion:

- mover `SQLALCHEMY_DATABASE_URL` a variable de entorno (ej: `.env`)
- leerla desde `os.getenv(...)`

### Nota de migracion

Si vienes de SQLite y quieres conservar datos, esta migracion requiere export/import o migraciones (Alembic). Si estas aprendiendo y no te importa perder data de prueba, puedes recrear esquema en Postgres desde cero.

## 36. Opcion alternativa: MySQL con `pymysql`

En esta sesion tambien dejamos comentada una opcion de conexion a MySQL usando SQLAlchemy + `pymysql`.

Linea que dejaste en `TodoApp/database.py`:

```python
# SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:test1234!@127.0.0.1:3306/TodoApplicationDatabase'
```

Formato general:

```text
mysql+pymysql://<usuario>:<password>@<host>:<puerto>/<database>
```

Dependencia necesaria:

```powershell
pip install pymysql
```

Uso practico:

1. descomentar la linea de MySQL
2. comentar la linea activa de Postgres
3. ejecutar la app para que SQLAlchemy conecte al motor MySQL

Nota: igual que en Postgres, evita dejar user/password hardcodeados en código y usa variables de entorno.

## Errores comunes

- `TypeError: 'check_Same_thread' is an invalid keyword argument for Connection()`

Causa: typo en `database.py`.

Solucion:

- incorrecto: `check_Same_thread`
- correcto: `check_same_thread`
