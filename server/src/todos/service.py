from sqlalchemy.orm import Session
from src.entities.todo import Todo
from src.todos.models import TodoCreate, TodoUpdate
from fastapi import HTTPException

def get_all_todos(db: Session):
    return db.query(Todo).all()

def create_todo(db: Session, data: TodoCreate):
    todo = Todo(**data.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

def update_todo(db: Session, todo_id: int, data: TodoUpdate):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail='Todo not found')
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)
    db.commit()
    db.refresh(todo)
    return todo

def delete_todo(db: Session, todo_id: int):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail='Todo not found')
    db.delete(todo)
    db.commit()
