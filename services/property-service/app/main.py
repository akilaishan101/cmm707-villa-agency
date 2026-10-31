from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_database
from app.models import Property
from app.schemas import PropertyCreate, PropertyResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Villa Agency Property Service",
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
    "/properties",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_property(
    property_data: PropertyCreate,
    database: Session = Depends(get_database),
):
    property_record = Property(
        **property_data.model_dump(mode="json")
    )

    database.add(property_record)
    database.commit()
    database.refresh(property_record)

    return property_record


@app.get("/properties", response_model=list[PropertyResponse])
def get_properties(database: Session = Depends(get_database)):
    statement = select(Property).order_by(Property.property_id)
    return database.scalars(statement).all()


@app.get(
    "/properties/{property_id}",
    response_model=PropertyResponse,
)
def get_property(
    property_id: int,
    database: Session = Depends(get_database),
):
    property_record = database.get(Property, property_id)

    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    return property_record


@app.put(
    "/properties/{property_id}",
    response_model=PropertyResponse,
)
def update_property(
    property_id: int,
    property_data: PropertyCreate,
    database: Session = Depends(get_database),
):
    property_record = database.get(Property, property_id)

    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    for field, value in property_data.model_dump(mode="json").items():
        setattr(property_record, field, value)

    database.commit()
    database.refresh(property_record)

    return property_record


@app.delete(
    "/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_property(
    property_id: int,
    database: Session = Depends(get_database),
):
    property_record = database.get(Property, property_id)

    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    database.delete(property_record)
    database.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)