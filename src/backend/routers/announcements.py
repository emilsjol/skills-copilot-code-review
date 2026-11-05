"""Database-backed public announcements and authenticated management."""

from datetime import date, datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator

from ..database import announcements_collection
from .auth import require_user

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    start_date: Optional[date] = None
    expiration_date: date

    @model_validator(mode="after")
    def validate_content(self):
        self.message = self.message.strip()
        if not self.message:
            raise ValueError("Message is required")
        if self.start_date and self.start_date > self.expiration_date:
            raise ValueError("Start date must not follow expiration date")
        return self

    def document(self):
        return {
            "message": self.message,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "expiration_date": self.expiration_date.isoformat()
        }


def serialize(document):
    return {"id": str(document["_id"]), "message": document["message"],
            "start_date": document.get("start_date"),
            "expiration_date": document["expiration_date"]}


def announcement_id(identifier: str):
    if not ObjectId.is_valid(identifier):
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ObjectId(identifier)


@router.get("")
def active_announcements(response: Response):
    today = datetime.now(timezone.utc).date().isoformat()
    response.headers["Cache-Control"] = "no-store"
    documents = announcements_collection.find({
        "expiration_date": {"$gte": today},
        "$or": [{"start_date": None}, {"start_date": {"$lte": today}}]
    }).sort([("expiration_date", 1), ("_id", 1)])
    return [serialize(document) for document in documents]


@router.get("/manage", dependencies=[Depends(require_user)])
def all_announcements(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return [serialize(document) for document in
            announcements_collection.find().sort([("expiration_date", -1), ("_id", -1)])]


@router.post("", status_code=201, dependencies=[Depends(require_user)])
def create_announcement(announcement: AnnouncementInput):
    document = announcement.document()
    document["_id"] = announcements_collection.insert_one(document).inserted_id
    return serialize(document)


@router.put("/{identifier}", dependencies=[Depends(require_user)])
def update_announcement(identifier: str, announcement: AnnouncementInput):
    identifier_value = announcement_id(identifier)
    document = announcement.document()
    result = announcements_collection.update_one({"_id": identifier_value}, {"$set": document})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return serialize({"_id": identifier_value, **document})


@router.delete("/{identifier}", status_code=204, dependencies=[Depends(require_user)])
def delete_announcement(identifier: str):
    result = announcements_collection.delete_one({"_id": announcement_id(identifier)})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Announcement not found")