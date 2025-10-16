from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Request
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
import base64

# -----------------------------
# CONFIGURACIÓN JWT
# -----------------------------
SECRET_KEY = "mi_clave_secreta_super_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()  # Para JWT Bearer

app = FastAPI()

# -----------------------------
# MODELOS
# -----------------------------
class Student(BaseModel):
    id: int
    name: str
    age: int

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# -----------------------------
# BASE DE DATOS SIMPLIFICADA
# -----------------------------
students_db = [
    {"id": 1, "name": "Ana", "age": 20},
    {"id": 2, "name": "Luis", "age": 22},
]

fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("1234"),
    }
}

# -----------------------------
# API KEY
# -----------------------------
API_KEY = "mi_api_key_secreta"

def api_key_auth(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")

# -----------------------------
# FUNCIONES JWT
# -----------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Protege endpoints con JWT Bearer Token
    """
    token_jwt = credentials.credentials
    try:
        payload = jwt.decode(token_jwt, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = fake_users_db.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

# -----------------------------
# ENDPOINTS
# -----------------------------

# 1. LIBRE (GET /students)
@app.get("/students")
def get_students():
    return students_db

# 2. POST /students con API Key
@app.post("/students", dependencies=[Depends(api_key_auth)])
def create_student(student: Student):
    students_db.append(student.dict())
    return {"msg": "Estudiante agregado", "student": student}

# 3. PUT /students/{id} con JWT Bearer
@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student, current_user: dict = Depends(get_current_user)):
    for s in students_db:
        if s["id"] == student_id:
            s["name"] = student.name
            s["age"] = student.age
            return {"msg": "Estudiante actualizado", "student": s}
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

# 4. DELETE /students/{id} con JWT Bearer
@app.delete("/students/{student_id}")
def delete_student(student_id: int, current_user: dict = Depends(get_current_user)):
    for s in students_db:
        if s["id"] == student_id:
            students_db.remove(s)
            return {"msg": "Estudiante eliminado"}
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

# 5. LOGIN SIMPLE (JSON)
@app.post("/login", response_model=Token)
def login(user: UserLogin):
    auth_user = authenticate_user(user.username, user.password)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": token, "token_type": "bearer"}


# -----------------------------
# NUEVO ENDPOINT: acceso codificado en Base64
# -----------------------------


@app.get("/private/{encoded_credentials}")
def get_private_info(encoded_credentials: str):
    """
    Decodifica credenciales base64 y, si son válidas, retorna información privada
    """
    try:
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_str = decoded_bytes.decode("utf-8")
        username, password = decoded_str.split(":")
    except Exception:
        raise HTTPException(status_code=400, detail="Credenciales mal formadas")

    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    private_info = {
        "student_id": 99,
        "name": "Carlos Test",
        "grades": {"QA": 9.5, "Automation": 8.8},
        "access_granted_to": username
    }
    return {"msg": "Acceso permitido", "data": private_info}

@app.get("/secure-data")
def get_secure_data(request: Request):
    """
    Simula un endpoint protegido por certificado de cliente.
    El nombre común del certificado (CN) debe estar en X-SSL-Client-CN.
    """
    client_cn = request.headers.get("x-ssl-client-cn")
    if not client_cn:
        raise HTTPException(status_code=403, detail="Certificado de cliente requerido")

    return {
        "msg": "Acceso autorizado por certificado de cliente",
        "client_cn": client_cn,
        "data": {
            "proyecto": "API Ultra Segura",
            "nivel": "Confidencial",
            "fecha": str(datetime.utcnow())
        }
    }

@app.get("/ssl-info")
def ssl_info(request: Request):
    cn = request.headers.get("X-SSL-Client-CN")
    verify = request.headers.get("X-SSL-Client-Verify")
    subject = request.headers.get("X-SSL-Client-Subject")
    issuer = request.headers.get("X-SSL-Client-Issuer")

    if not all([cn, verify, subject, issuer]):
        raise HTTPException(status_code=400, detail="Faltan cabeceras SSL necesarias")

    if verify.upper() != "SUCCESS":
        raise HTTPException(status_code=401, detail="Certificado no verificado")

    return {
        "msg": "Certificado cliente válido",
        "client_certificate": {
            "common_name": cn,
            "verification": verify,
            "subject": subject,
            "issuer": issuer,
        }
    }


@app.get("/cors-test")
async def cors_test(request: Request):
    origin = request.headers.get("origin")
    allowed_origins = ["http://localhost", "http://127.0.0.1"]

    if origin is None:
        return JSONResponse(status_code=400, content={"detail": "No Origin header found"})
    if not any(origin.startswith(allowed) for allowed in allowed_origins):
        return JSONResponse(status_code=403, content={"detail": f"Origin {origin} no permitido"})
    response = JSONResponse(content={"msg": "Acceso permitido desde origen local"})
    response.headers["Access-Control-Allow-Origin"] = origin
    return response