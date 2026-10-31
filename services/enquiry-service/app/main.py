from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Response,
    status,
)
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_database
from app.models import Enquiry
from app.notifier import invoke_notification
from app.schemas import EnquiryCreate, EnquiryResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Villa Agency Enquiry Service",
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
    "/enquiries",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enquiry(
    enquiry_data: EnquiryCreate,
    background_tasks: BackgroundTasks,
    database: Session = Depends(get_database),
):
    enquiry_record = Enquiry(
        **enquiry_data.model_dump(mode="json")
    )

    database.add(enquiry_record)
    database.commit()
    database.refresh(enquiry_record)

    count_statement = (
        select(func.count())
        .select_from(Enquiry)
        .where(Enquiry.property_id == enquiry_record.property_id)
    )
    enquiry_count = database.scalar(count_statement)

    if enquiry_count == 11:
        background_tasks.add_task(
            invoke_notification,
            enquiry_record.property_id,
            enquiry_count,
        )

    return enquiry_record


@app.get("/enquiries", response_model=list[EnquiryResponse])
def get_enquiries(database: Session = Depends(get_database)):
    statement = select(Enquiry).order_by(Enquiry.enquiry_id)
    return database.scalars(statement).all()


@app.get("/properties/{property_id}/enquiry-count")
def get_property_enquiry_count(
    property_id: int,
    database: Session = Depends(get_database),
):
    statement = (
        select(func.count())
        .select_from(Enquiry)
        .where(Enquiry.property_id == property_id)
    )

    return {
        "property_id": property_id,
        "enquiry_count": database.scalar(statement),
    }


@app.get(
    "/enquiries/{enquiry_id}",
    response_model=EnquiryResponse,
)
def get_enquiry(
    enquiry_id: int,
    database: Session = Depends(get_database),
):
    enquiry_record = database.get(Enquiry, enquiry_id)

    if enquiry_record is None:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    return enquiry_record


@app.put(
    "/enquiries/{enquiry_id}",
    response_model=EnquiryResponse,
)
def update_enquiry(
    enquiry_id: int,
    enquiry_data: EnquiryCreate,
    database: Session = Depends(get_database),
):
    enquiry_record = database.get(Enquiry, enquiry_id)

    if enquiry_record is None:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    for field, value in enquiry_data.model_dump(mode="json").items():
        setattr(enquiry_record, field, value)

    database.commit()
    database.refresh(enquiry_record)

    return enquiry_record


@app.delete(
    "/enquiries/{enquiry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enquiry(
    enquiry_id: int,
    database: Session = Depends(get_database),
):
    enquiry_record = database.get(Enquiry, enquiry_id)

    if enquiry_record is None:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    database.delete(enquiry_record)
    database.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
