# API de Test con FastAPI

API hecha en Python para practicar en Postman o cualquier framework de API Testing

## Requisitos

Antes de comenzar, asegúrate de tener lo siguiente instalado:

- Python 3.12 o superior
- pip (gestor de paquetes de Python)


## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/fastapi-test-api.git
cd fastapi-test-api
```
2. Crear y activar un entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate   # En macOS/Linux
venv\Scripts\activate      # En Windows
```
3. Instalar dependencias
```bash
pip install -r requirements.txt
```

Ejecutar la API localmente
Para levantar el servidor de desarrollo y que puedas probar la API de forma local, ejecuta el siguiente comando:
```bash
uvicorn main:app --reload
```
