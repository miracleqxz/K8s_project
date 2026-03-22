import os
import socket
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
db = Database()


Instrumentator().instrument(app).expose(app, endpoint="/metrics")

tasks_created = Counter("tasks_created_total", "Total tasks created")
tasks_deleted = Counter("tasks_deleted_total", "Total tasks deleted")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


kafka_producer = None
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "task-events")

try:
    from kafka import KafkaProducer
    kafka_host = os.environ.get("KAFKA_HOST")
    if kafka_host:
        kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_host,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        logger.info(f"Kafka connected: {kafka_host}")
except Exception as e:
    logger.warning(f"Kafka not available: {e}")


def send_event(event_type: str, data: dict):
    if kafka_producer:
        try:
            kafka_producer.send(KAFKA_TOPIC, {"event": event_type, **data})
        except Exception as e:
            logger.error(f"Kafka send failed: {e}")



es_client = None

try:
    from elasticsearch import Elasticsearch
    es_host = os.environ.get("ES_HOST")
    if es_host:
        es_client = Elasticsearch(es_host)
        if es_client.ping():
            logger.info(f"Elasticsearch connected: {es_host}")
        else:
            es_client = None
except Exception as e:
    logger.warning(f"Elasticsearch not available: {e}")


def index_task(task: dict):
    if es_client:
        try:
            es_client.index(index="tasks", id=task["id"], document=task)
        except Exception as e:
            logger.error(f"ES index failed: {e}")


def delete_from_index(task_id: int):
    if es_client:
        try:
            es_client.delete(index="tasks", id=task_id, ignore=[404])
        except Exception as e:
            logger.error(f"ES delete failed: {e}")



class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    done: bool | None = None



@app.get("/api/info")
def info():
    return {
        "hostname": socket.gethostname(),
        "pod_ip": os.environ.get("POD_IP", "unknown"),
        "kafka": kafka_producer is not None,
        "elasticsearch": es_client is not None,
    }


@app.get("/api/tasks")
def list_tasks():
    return db.get_all()


@app.get("/api/tasks/search")
def search_tasks(q: str = ""):
    if not q:
        return []
    if es_client:
        try:
            result = es_client.search(
                index="tasks",
                query={"multi_match": {"query": q, "fields": ["title", "description"]}},
            )
            return [hit["_source"] for hit in result["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES search failed: {e}")
    return [t for t in db.get_all() if q.lower() in t["title"].lower() or q.lower() in t["description"].lower()]


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    result = db.create(task.title, task.description)
    tasks_created.inc()
    send_event("task_created", result)
    index_task(result)
    return result


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
    send_event("task_updated", task)
    index_task(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not db.delete(task_id):
        raise HTTPException(404, "Task not found")
    tasks_deleted.inc()
    send_event("task_deleted", {"id": task_id})
    delete_from_index(task_id)