from datetime import datetime, timezone

from app import db

VALID_STATUSES = ("Open", "In Progress", "Testing", "Closed")
VALID_SEVERITIES = ("critical", "major", "minor", "trivial")


def utcnow():
    return datetime.now(timezone.utc)


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(30), nullable=False, default="Open")
    severity = db.Column(db.String(20), nullable=False, default="minor")
    labels = db.Column(db.String(300), default="")  # comma-separated, simple by design
    assignee = db.Column(db.String(100), default="")
    position = db.Column(db.Float, nullable=False, default=1.0)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    activity = db.relationship(
        "ActivityLog", backref="card", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "severity": self.severity,
            "labels": [l for l in self.labels.split(",") if l] if self.labels else [],
            "assignee": self.assignee,
            "position": self.position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)  # "created", "field_update"
    field = db.Column(db.String(50))  # null for "created" events
    from_value = db.Column(db.String(300))
    to_value = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "card_id": self.card_id,
            "event_type": self.event_type,
            "field": self.field,
            "from_value": self.from_value,
            "to_value": self.to_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
