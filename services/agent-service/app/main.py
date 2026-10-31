from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_database
from app.models import Agent
from app.schemas import AgentCreate, AgentResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Villa Agency Agent Service",
    version="1.0.0",
)


@app.get("/health")
def health_check(database: Session = Depends(get_database)):
    database.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
    }


@app.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(
    agent_data: AgentCreate,
    database: Session = Depends(get_database),
):
    agent_record = Agent(**agent_data.model_dump(mode="json"))
    database.add(agent_record)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=409,
            detail="Agent email already exists",
        )

    database.refresh(agent_record)
    return agent_record


@app.get("/agents", response_model=list[AgentResponse])
def get_agents(database: Session = Depends(get_database)):
    statement = select(Agent).order_by(Agent.agent_id)
    return database.scalars(statement).all()


@app.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    database: Session = Depends(get_database),
):
    agent_record = database.get(Agent, agent_id)

    if agent_record is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent_record


@app.put("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentCreate,
    database: Session = Depends(get_database),
):
    agent_record = database.get(Agent, agent_id)

    if agent_record is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    for field, value in agent_data.model_dump(mode="json").items():
        setattr(agent_record, field, value)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=409,
            detail="Agent email already exists",
        )

    database.refresh(agent_record)
    return agent_record


@app.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_agent(
    agent_id: int,
    database: Session = Depends(get_database),
):
    agent_record = database.get(Agent, agent_id)

    if agent_record is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    database.delete(agent_record)
    database.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)