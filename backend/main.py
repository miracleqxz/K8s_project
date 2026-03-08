from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import Database

app = FastAPI()
db = Database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    done: bool | None = None


@app.get("/api/tasks")
def list_tasks():
    return db.get_all()


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    return db.create(task.title, task.description)


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    task = db.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate):
    task = db.update(task_id, data.model_dump(exclude_none=True))
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not db.delete(task_id):
        raise HTTPException(404, "Task not found")