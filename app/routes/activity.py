from flask import Blueprint, jsonify

from app import db
from app.models import Card

activity_bp = Blueprint("activity", __name__, url_prefix="/api/cards")


@activity_bp.get("/<int:card_id>/activity")
def get_card_activity(card_id):
    card = db.session.get(Card, card_id)
    if card is None:
        return jsonify({"error": "card not found"}), 404
    entries = card.activity.order_by(db.desc("timestamp")).all()
    return jsonify([e.to_dict() for e in entries])
