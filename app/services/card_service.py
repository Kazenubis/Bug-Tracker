from app import db
from app.models import Card, ActivityLog, VALID_STATUSES, VALID_SEVERITIES

# Fields we track in the activity log when they change.
# title/description are excluded deliberately -- logging every keystroke-adjacent
# edit would make the timeline noisy rather than useful.
TRACKED_FIELDS = ("status", "severity", "assignee", "labels")

# Fields a client is allowed to set via create/update. Never blindly unpack
# a request body onto the model (mass-assignment risk).
ALLOWED_FIELDS = ("title", "description", "status", "severity", "labels", "assignee")


class ValidationError(Exception):
    pass


def _labels_to_str(labels):
    if labels is None:
        return ""
    if isinstance(labels, list):
        return ",".join(l.strip() for l in labels if l.strip())
    return str(labels)


def compute_new_position(before_pos, after_pos):
    """
    Fractional positioning: the new card's position is the midpoint of its
    neighbors. Dropped at the top of a column -> half the first card's
    position. Dropped at the bottom -> one more than the last card's
    position. Empty column -> 1.0.
    """
    if before_pos is None and after_pos is None:
        return 1.0
    if before_pos is None:
        return after_pos / 2
    if after_pos is None:
        return before_pos + 1
    return (before_pos + after_pos) / 2


def create_card(payload):
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValidationError("title is required")

    status = payload.get("status", "Open")
    if status not in VALID_STATUSES:
        raise ValidationError(f"status must be one of {VALID_STATUSES}")

    severity = payload.get("severity", "minor")
    if severity not in VALID_SEVERITIES:
        raise ValidationError(f"severity must be one of {VALID_SEVERITIES}")

    # new cards land at the bottom of their column
    max_pos = (
        db.session.query(db.func.max(Card.position))
        .filter(Card.status == status)
        .scalar()
    )
    position = (max_pos + 1) if max_pos is not None else 1.0

    card = Card(
        title=title,
        description=payload.get("description", ""),
        status=status,
        severity=severity,
        labels=_labels_to_str(payload.get("labels")),
        assignee=payload.get("assignee", ""),
        position=position,
    )
    db.session.add(card)
    db.session.flush()  # get card.id before we log against it

    db.session.add(
        ActivityLog(card_id=card.id, event_type="created", field=None,
                    from_value=None, to_value=None)
    )
    db.session.commit()
    return card


def update_card(card, payload, before_id=None, after_id=None):
    """
    Applies field updates and/or a column move in one transaction.
    Diffs TRACKED_FIELDS against their previous values and writes an
    ActivityLog row per changed field. Update + log succeed or fail together.
    """
    if "status" in payload and payload["status"] not in VALID_STATUSES:
        raise ValidationError(f"status must be one of {VALID_STATUSES}")
    if "severity" in payload and payload["severity"] not in VALID_SEVERITIES:
        raise ValidationError(f"severity must be one of {VALID_SEVERITIES}")

    changes = []  # (field, old, new) for anything that actually changed

    for field in ALLOWED_FIELDS:
        if field not in payload:
            continue
        new_value = payload[field]
        if field == "labels":
            new_value = _labels_to_str(new_value)
        old_value = getattr(card, field)
        if old_value != new_value:
            if field in TRACKED_FIELDS:
                changes.append((field, old_value, new_value))
            setattr(card, field, new_value)

    # Reordering: caller supplies the ids of the cards that will end up
    # immediately before/after this one in the target column (either may
    # be None for top/bottom/empty-column drops).
    if before_id is not None or after_id is not None or "status" in payload:
        before_pos = (
            db.session.get(Card, before_id).position if before_id else None
        )
        after_pos = (
            db.session.get(Card, after_id).position if after_id else None
        )
        card.position = compute_new_position(before_pos, after_pos)

    for field, old_value, new_value in changes:
        db.session.add(
            ActivityLog(
                card_id=card.id,
                event_type="field_update",
                field=field,
                from_value=str(old_value) if old_value is not None else None,
                to_value=str(new_value) if new_value is not None else None,
            )
        )

    db.session.commit()
    return card


def delete_card(card):
    db.session.delete(card)  # cascades to activity_log via relationship config
    db.session.commit()
