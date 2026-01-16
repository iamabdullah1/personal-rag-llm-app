# FastAPI Beginner Guide for React/Next.js Developers

**For developers coming from React/Next.js/MERN stack** 🚀

---

## 📚 What is FastAPI?

Think of FastAPI as **Next.js API Routes, but for Python**.

### Comparison for React Developers

| Concept | Next.js | FastAPI |
|---------|---------|---------|
| **Framework Type** | Full-stack React | Backend API |
| **Language** | JavaScript/TypeScript | Python |
| **API Routes** | `app/api/route.ts` | `@app.get("/api")` |
| **TypeScript Types** | `interface User {}` | `class User(BaseModel)` |
| **Async/Await** | ✅ Same syntax | ✅ Same syntax |
| **JSON Response** | `Response.json()` | `return {...}` (automatic) |
| **Request Body** | `await req.json()` | Function parameter (automatic) |

---

## 🎯 Core Concept: It's Just Functions!

### In Next.js (API Route):
```javascript
// app/api/hello/route.js
export async function GET(request) {
  return Response.json({ message: "Hello World" })
}

export async function POST(request) {
  const body = await request.json()
  return Response.json({ received: body })
}
```

### In FastAPI (Same Logic):
```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/hello")
async def get_hello():
    return {"message": "Hello World"}

@app.post("/api/hello")
async def post_hello(body: dict):
    return {"received": body}
```

**See? Almost identical logic!**

---

## 📦 Installation

```bash
# Create project folder
mkdir fastapi-learning
cd fastapi-learning

# Create virtual environment (like node_modules)
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install FastAPI (like npm install)
pip install fastapi uvicorn[standard]

# Create main.py
touch main.py
```

---

## 🚀 Your First FastAPI App

### Step 1: Create `main.py`

```python
from fastapi import FastAPI

# Create app (like creating Express app)
app = FastAPI()

# Root route (like app.get("/") in Express)
@app.get("/")
def read_root():
    return {"message": "Hello World"}

# Route with path parameter
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### Step 2: Run the Server

```bash
uvicorn main:app --reload

# --reload = like nodemon (auto-restart on changes)
```

### Step 3: Test It!

Open browser:
- `http://localhost:8000` → See `{"message": "Hello World"}`
- `http://localhost:8000/docs` → **Interactive API Docs!** 🎉
- `http://localhost:8000/items/42` → See `{"item_id": 42}`

---

## 🎨 Understanding the Syntax

### 1. **Decorators** = Route Handlers

**Like React Router or Next.js routing:**

```python
@app.get("/users")        # GET request
@app.post("/users")       # POST request
@app.put("/users/{id}")   # PUT request
@app.delete("/users/{id}") # DELETE request
```

**Comparison:**
```javascript
// Next.js
export async function GET(request) { }
export async function POST(request) { }
```
```python
# FastAPI
@app.get("/api/data")
async def get_data(): 
    return {"data": "value"}

@app.post("/api/data")
async def post_data(body: dict): 
    return {"received": body}
```

### 2. **Path Parameters** (URL params)

```python
# Like /users/:id in Express or [id] in Next.js
@app.get("/users/{user_id}")
def get_user(user_id: int):  # Automatic type conversion!
    return {"user_id": user_id}
```

**Next.js equivalent:**
```javascript
// app/users/[id]/route.js
export async function GET(request, { params }) {
  return Response.json({ user_id: params.id })
}
```

### 3. **Query Parameters** (like ?search=hello)

```python
@app.get("/search")
def search(q: str = None, limit: int = 10):
    return {"query": q, "limit": limit}

# Call: /search?q=python&limit=20
```

**Next.js equivalent:**
```javascript
export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q')
  const limit = searchParams.get('limit') || '10'
  return Response.json({ query: q, limit })
}
```

---

## 📝 Request Body (Like req.body in Express)

### Using Pydantic Models (Like JavaScript Objects with Validation)

**JavaScript Object (no validation):**
```javascript
// In JavaScript, you might do:
const user = {
  name: "John",
  email: "john@example.com",
  age: 25  // optional
}
```

**FastAPI Pydantic Model:**
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int = None  # Optional with default
```

### POST Request with Body

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str
    age: int = None

@app.post("/users")
def create_user(user: User):  # Automatic parsing & validation!
    return {
        "message": "User created",
        "user": user
    }
```

**Test with curl:**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "age": 25}'
```

**Or test in the automatic docs:** `http://localhost:8000/docs`

---

## 🔄 Async/Await (Same as JavaScript!)

```python
import asyncio

@app.get("/slow")
async def slow_endpoint():
    await asyncio.sleep(1)  # Like await delay in JS
    return {"message": "Done waiting"}

@app.get("/fast")
def fast_endpoint():  # Non-async also works
    return {"message": "Instant"}
```

**When to use `async`:**
- Database calls
- API requests
- File operations
- Anything that "waits"

**Just like in JavaScript!** 🎯

---

## 🎨 Complete CRUD Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Data model
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: str = None
    price: float
    in_stock: bool = True

# Fake database (like useState in React)
items_db = []
next_id = 1

# CREATE
@app.post("/items", response_model=Item)
def create_item(item: Item):
    global next_id
    item.id = next_id
    next_id += 1
    items_db.append(item)
    return item

# READ ALL
@app.get("/items", response_model=List[Item])
def read_items(skip: int = 0, limit: int = 10):
    return items_db[skip : skip + limit]

# READ ONE
@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# UPDATE
@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            updated_item.id = item_id
            items_db[i] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

# DELETE
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
```

**Run it:**
```bash
uvicorn main:app --reload
```

**Test in docs:** `http://localhost:8000/docs`

---

## 🗂️ Project Structure (Like Next.js Structure)

### Small Project (Single File)
```
project/
├── venv/              # Like node_modules
├── main.py            # All code here
└── requirements.txt   # Like package.json
```

### Medium Project (Organized)
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app
│   ├── models.py      # Pydantic models (like types.ts)
│   ├── routes.py      # All route handlers
│   └── database.py    # DB connection
├── requirements.txt
└── .env
```

### Large Project (Like Your RAG App)
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI setup
│   ├── config.py         # Environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py    # Pydantic models
│   ├── routers/          # Like Next.js app/api/
│   │   ├── __init__.py
│   │   ├── users.py      # /api/users
│   │   └── chat.py       # /api/chat
│   └── services/         # Business logic
│       ├── __init__.py
│       └── rag_service.py
├── requirements.txt
└── .env
```

---

## 📁 Organizing Routes (Like Next.js API Routes)

### `app/routers/users.py`
```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/users",  # All routes start with /api/users
    tags=["users"]        # Groups in docs
)

@router.get("/")
def get_users():
    return {"users": []}

@router.get("/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@router.post("/")
def create_user(name: str, email: str):
    return {"name": name, "email": email}
```

### `app/main.py`
```python
from fastapi import FastAPI
from app.routers import users

app = FastAPI()

# Include router (like mounting routes)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Welcome"}
```

**Now you have:**
- `GET /api/users/` → Get all users
- `GET /api/users/123` → Get user 123
- `POST /api/users/` → Create user

---

## 🔒 Middleware & CORS (Like Next.js middleware)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your Next.js frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "https://yourapp.vercel.app"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
def get_data():
    return {"data": "Now your Next.js can fetch this!"}
```

---

## 🎯 Key Features for Your RAG Project

### 1. **Dependency Injection** (Advanced but powerful)

```python
from fastapi import Depends

# Like a React Context Provider
def get_db():
    db = connect_to_database()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
def get_users(db = Depends(get_db)):  # Auto-inject db
    return db.query_users()
```

### 2. **Background Tasks** (Like queues)

```python
from fastapi import BackgroundTasks

def send_email(email: str):
    print(f"Sending email to {email}")
    # Actual email logic here

@app.post("/register")
def register(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email)
    return {"message": "User registered, email will be sent"}
```

### 3. **Error Handling**

```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return users_db[user_id]
```

---

## 🧪 Testing Your API

### Option 1: Browser
- Go to `http://localhost:8000/docs`
- Click "Try it out" on any endpoint
- Fill in parameters
- Click "Execute"

### Option 2: Curl
```bash
# GET
curl http://localhost:8000/api/users

# POST
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'
```

### Option 3: Your React Frontend
```javascript
// In your React app
const response = await fetch('http://localhost:8000/api/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'John', email: 'john@example.com' })
})
const data = await response.json()
console.log(data)
```

---

## 📦 Essential Packages for RAG Project

```bash
# Core
pip install fastapi uvicorn[standard]

# Validation & Settings
pip install pydantic pydantic-settings

# Environment Variables (like dotenv)
pip install python-dotenv

# LangChain (for RAG)
pip install langchain langchain-openai

# Vector Store
pip install chromadb pinecone-client

# CORS
pip install python-multipart
```

**Save dependencies:**
```bash
pip freeze > requirements.txt
```

**Install from requirements.txt:**
```bash
pip install -r requirements.txt
```

---

## 🔥 FastAPI vs Express Cheat Sheet

| Task | Express/Node.js | FastAPI |
|------|----------------|---------|
| **Create app** | `const app = express()` | `app = FastAPI()` |
| **GET route** | `app.get("/", (req, res) => {})` | `@app.get("/")` |
| **POST route** | `app.post("/", (req, res) => {})` | `@app.post("/")` |
| **Path params** | `req.params.id` | Function parameter |
| **Query params** | `req.query.search` | Function parameter |
| **Request body** | `req.body` | Function parameter |
| **JSON response** | `res.json({})` | `return {}` |
| **Status code** | `res.status(404)` | `raise HTTPException(404)` |
| **Middleware** | `app.use()` | `app.add_middleware()` |
| **Start server** | `app.listen(3000)` | `uvicorn main:app` |

---

## 💡 Complete Program Examples

### Example 1: Simple Calculator API

**FastAPI Backend (main.py):**
```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalculationRequest(BaseModel):
    num1: float
    num2: float
    operation: str  # "add", "subtract", "multiply", "divide"

@app.post("/calculate")
def calculate(req: CalculationRequest):
    if req.operation == "add":
        result = req.num1 + req.num2
    elif req.operation == "subtract":
        result = req.num1 - req.num2
    elif req.operation == "multiply":
        result = req.num1 * req.num2
    elif req.operation == "divide":
        if req.num2 == 0:
            return {"error": "Cannot divide by zero"}
        result = req.num1 / req.num2
    else:
        return {"error": "Invalid operation"}
    
    return {
        "num1": req.num1,
        "num2": req.num2,
        "operation": req.operation,
        "result": result
    }
```

**React Frontend (Calculator.jsx):**
```javascript
import React, { useState } from 'react';

function Calculator() {
  const [num1, setNum1] = useState('');
  const [num2, setNum2] = useState('');
  const [operation, setOperation] = useState('add');
  const [result, setResult] = useState(null);

  const handleCalculate = async () => {
    const response = await fetch('http://localhost:8000/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num1: parseFloat(num1),
        num2: parseFloat(num2),
        operation: operation
      })
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Calculator</h1>
      <input 
        type="number" 
        value={num1} 
        onChange={(e) => setNum1(e.target.value)} 
        placeholder="Number 1"
      />
      <select value={operation} onChange={(e) => setOperation(e.target.value)}>
        <option value="add">+</option>
        <option value="subtract">-</option>
        <option value="multiply">×</option>
        <option value="divide">÷</option>
      </select>
      <input 
        type="number" 
        value={num2} 
        onChange={(e) => setNum2(e.target.value)} 
        placeholder="Number 2"
      />
      <button onClick={handleCalculate}>Calculate</button>
      
      {result && (
        <div style={{ marginTop: '20px' }}>
          {result.error ? (
            <p style={{ color: 'red' }}>{result.error}</p>
          ) : (
            <h2>Result: {result.result}</h2>
          )}
        </div>
      )}
    </div>
  );
}

export default Calculator;
```

---

### Example 2: Todo List App

**FastAPI Backend (todo_api.py):**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    completed: bool = False

# In-memory database
todos = []
next_id = 1

@app.get("/todos", response_model=List[Todo])
def get_todos():
    return todos

@app.post("/todos", response_model=Todo)
def create_todo(todo: Todo):
    global next_id
    todo.id = next_id
    next_id += 1
    todos.append(todo)
    return todo

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updated_todo: Todo):
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            updated_todo.id = todo_id
            todos[i] = updated_todo
            return updated_todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            todos.pop(i)
            return {"message": "Todo deleted"}
    raise HTTPException(status_code=404, detail="Todo not found")

@app.patch("/todos/{todo_id}/toggle")
def toggle_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            todo.completed = not todo.completed
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")
```

**React Frontend (TodoApp.jsx):**
```javascript
import React, { useState, useEffect } from 'react';

function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');
  const API_URL = 'http://localhost:8000';

  // Fetch todos on mount
  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    const response = await fetch(`${API_URL}/todos`);
    const data = await response.json();
    setTodos(data);
  };

  const addTodo = async () => {
    if (!newTodo.trim()) return;
    
    const response = await fetch(`${API_URL}/todos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTodo, completed: false })
    });
    const data = await response.json();
    setTodos([...todos, data]);
    setNewTodo('');
  };

  const toggleTodo = async (id) => {
    const response = await fetch(`${API_URL}/todos/${id}/toggle`, {
      method: 'PATCH'
    });
    const updatedTodo = await response.json();
    setTodos(todos.map(todo => 
      todo.id === id ? updatedTodo : todo
    ));
  };

  const deleteTodo = async (id) => {
    await fetch(`${API_URL}/todos/${id}`, {
      method: 'DELETE'
    });
    setTodos(todos.filter(todo => todo.id !== id));
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Todo List</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          placeholder="Add a new todo..."
          style={{ padding: '10px', width: '70%' }}
        />
        <button onClick={addTodo} style={{ padding: '10px 20px', marginLeft: '10px' }}>
          Add
        </button>
      </div>

      <ul style={{ listStyle: 'none', padding: 0 }}>
        {todos.map(todo => (
          <li key={todo.id} style={{ 
            padding: '10px', 
            marginBottom: '10px', 
            border: '1px solid #ddd',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span 
              onClick={() => toggleTodo(todo.id)}
              style={{ 
                textDecoration: todo.completed ? 'line-through' : 'none',
                cursor: 'pointer',
                flex: 1
              }}
            >
              {todo.title}
            </span>
            <button 
              onClick={() => deleteTodo(todo.id)}
              style={{ padding: '5px 10px', backgroundColor: '#ff4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
      
      {todos.length === 0 && <p style={{ textAlign: 'center', color: '#999' }}>No todos yet. Add one above!</p>}
    </div>
  );
}

export default TodoApp;
```

---

### Example 3: Simple Weather Dashboard

**FastAPI Backend (weather_api.py):**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock weather data
cities = {
    "new york": {"temp": 72, "condition": "Sunny", "humidity": 65},
    "london": {"temp": 55, "condition": "Cloudy", "humidity": 80},
    "tokyo": {"temp": 68, "condition": "Rainy", "humidity": 75},
    "paris": {"temp": 60, "condition": "Partly Cloudy", "humidity": 70},
    "sydney": {"temp": 78, "condition": "Sunny", "humidity": 60}
}

@app.get("/weather/{city}")
def get_weather(city: str):
    city_lower = city.lower()
    if city_lower in cities:
        weather = cities[city_lower]
        # Add some random variation
        return {
            "city": city.title(),
            "temperature": weather["temp"] + random.randint(-3, 3),
            "condition": weather["condition"],
            "humidity": weather["humidity"] + random.randint(-5, 5)
        }
    else:
        raise HTTPException(status_code=404, detail="City not found")

@app.get("/weather")
def get_all_cities():
    return {
        "cities": [city.title() for city in cities.keys()]
    }
```

**React Frontend (WeatherDashboard.jsx):**
```javascript
import React, { useState, useEffect } from 'react';

function WeatherDashboard() {
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCities();
  }, []);

  const fetchCities = async () => {
    const response = await fetch('http://localhost:8000/weather');
    const data = await response.json();
    setCities(data.cities);
  };

  const fetchWeather = async (city) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/weather/${city}`);
      const data = await response.json();
      setWeather(data);
    } catch (error) {
      console.error('Error fetching weather:', error);
    }
    setLoading(false);
  };

  const handleCityChange = (city) => {
    setSelectedCity(city);
    fetchWeather(city);
  };

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ textAlign: 'center', color: '#333' }}>Weather Dashboard</h1>
      
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <select 
          value={selectedCity} 
          onChange={(e) => handleCityChange(e.target.value)}
          style={{ padding: '10px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ddd' }}
        >
          <option value="">Select a city...</option>
          {cities.map(city => (
            <option key={city} value={city}>{city}</option>
          ))}
        </select>
      </div>

      {loading && <p style={{ textAlign: 'center' }}>Loading...</p>}

      {weather && !loading && (
        <div style={{ 
          padding: '30px', 
          backgroundColor: '#f0f8ff', 
          borderRadius: '10px', 
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <h2>{weather.city}</h2>
          <div style={{ fontSize: '48px', margin: '20px 0' }}>
            {weather.temperature}°F
          </div>
          <p style={{ fontSize: '24px', color: '#666' }}>{weather.condition}</p>
          <p style={{ fontSize: '18px', color: '#888' }}>Humidity: {weather.humidity}%</p>
        </div>
      )}
    </div>
  );
}

export default WeatherDashboard;
```

---

### Example 4: User Authentication System

**FastAPI Backend (auth_api.py):**
```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

# In-memory database
users_db = []
tokens_db = {}  # token -> user_id
next_id = 1

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/register", response_model=UserResponse)
def register(user: User):
    global next_id
    
    # Check if user exists
    for existing_user in users_db:
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = {
        "id": next_id,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)
    }
    next_id += 1
    users_db.append(new_user)
    
    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"]
    )

@app.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    # Find user
    user = None
    for u in users_db:
        if u["email"] == credentials.email:
            user = u
            break
    
    if not user or user["password"] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    tokens_db[token] = user["id"]
    
    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"]
        )
    )

@app.get("/profile")
def get_profile(token: str):
    if token not in tokens_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = tokens_db[token]
    user = next((u for u in users_db if u["id"] == user_id), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"]
    )

@app.post("/logout")
def logout(token: str):
    if token in tokens_db:
        del tokens_db[token]
    return {"message": "Logged out successfully"}
```

**React Frontend (AuthApp.jsx):**
```javascript
import React, { useState } from 'react';

function AuthApp() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const endpoint = isLogin ? 'login' : 'register';
    const body = isLogin 
      ? { email: formData.email, password: formData.password }
      : formData;

    try {
      const response = await fetch(`http://localhost:8000/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }

      const data = await response.json();
      
      if (isLogin) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('token', data.token);
      } else {
        setUser(data);
        alert('Registration successful! Please login.');
        setIsLogin(true);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = async () => {
    await fetch(`http://localhost:8000/logout?token=${token}`, {
      method: 'POST'
    });
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  if (user && token) {
    return (
      <div style={{ padding: '40px', maxWidth: '600px', margin: '0 auto' }}>
        <h1>Welcome, {user.username}!</h1>
        <div style={{ backgroundColor: '#f0f0f0', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
          <p><strong>Username:</strong> {user.username}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>User ID:</strong> {user.id}</p>
        </div>
        <button 
          onClick={handleLogout}
          style={{ marginTop: '20px', padding: '10px 20px', backgroundColor: '#ff4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', maxWidth: '400px', margin: '0 auto' }}>
      <h1>{isLogin ? 'Login' : 'Register'}</h1>
      
      {error && <p style={{ color: 'red', marginBottom: '10px' }}>{error}</p>}
      
      <form onSubmit={handleSubmit}>
        {!isLogin && (
          <input
            type="text"
            placeholder="Username"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
            required
          />
        )}
        
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
          required
        />
        
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
          required
        />
        
        <button 
          type="submit"
          style={{ width: '100%', padding: '10px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}
        >
          {isLogin ? 'Login' : 'Register'}
        </button>
      </form>
      
      <p style={{ textAlign: 'center', marginTop: '20px' }}>
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <button 
          onClick={() => setIsLogin(!isLogin)}
          style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', textDecoration: 'underline' }}
        >
          {isLogin ? 'Register' : 'Login'}
        </button>
      </p>
    </div>
  );
}

export default AuthApp;
```

---

## 🎓 Learning Path for Your RAG Project

### Week 1: Basics ✅
- [x] Install FastAPI
- [x] Create simple GET/POST routes
- [x] Understand Pydantic models
- [x] Test in `/docs`

### Week 2: Intermediate 🔄
- [ ] Organize code into routers
- [ ] Add CORS for Next.js
- [ ] Environment variables with .env
- [ ] Error handling

### Week 3: RAG Integration 🚀
- [ ] Install LangChain
- [ ] Create vector store endpoint
- [ ] Build chat endpoint
- [ ] Stream responses

### Week 4: Deployment 🌐
- [ ] Test locally with Next.js
- [ ] Deploy to Railway
- [ ] Connect production frontend

---

## 🎯 Practice Exercises

### Exercise 1: Todo API
Create a simple todo API with:
- `GET /todos` - List all todos
- `POST /todos` - Create todo
- `PUT /todos/{id}` - Update todo
- `DELETE /todos/{id}` - Delete todo

### Exercise 2: User Authentication
Create:
- `POST /register` - Register user
- `POST /login` - Login user
- `GET /profile` - Get user profile (protected)

### Exercise 3: Chat API
Create your RAG endpoints:
- `POST /api/chat` - Send message, get response
- `GET /api/health` - Health check

---

## 📚 Resources

- **Official Docs**: https://fastapi.tiangolo.com/
- **Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Pydantic**: https://docs.pydantic.dev/
- **Compare to Next.js**: Similar patterns, different language

---

## 🎉 Quick Start Template

Save this as `main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="My API", version="1.0.0")

# CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Message(BaseModel):
    text: str

class Response(BaseModel):
    message: str
    received: str

# Routes
@app.get("/")
def root():
    return {"message": "Welcome to my API!"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/echo", response_model=Response)
def echo(msg: Message):
    return Response(
        message="Echo received",
        received=msg.text
    )

# Run with: uvicorn main:app --reload
# Docs at: http://localhost:8000/docs
```

---

**You're ready to build your RAG application! Start with the basics, then gradually add RAG features.** 🚀

*Created: January 2026*
