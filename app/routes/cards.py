from flask import Blueprint, jsonify, request

from app import db
from app.models import Card
from app.services import card_service
from app.services.card_service import ValidationError

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@cards_bp.get("")
def list_cards():
    cards = Card.query.order_by(Card.status, Card.position).all()
    return jsonify([c.to_dict() for c in cards])


@cards_bp.post("")
def create_card():
    payload = request.get_json(silent=True) or {}
    try:
        card = card_service.create_card(payload)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(card.to_dict()), 201


@cards_bp.get("/<int:card_id>")
def get_card(card_id):
    card = db.session.get(Card, card_id)
    if card is None:
        return jsonify({"error": "card not found"}), 404
    return jsonify(card.to_dict())


@cards_bp.patch("/<int:card_id>")
def update_card(card_id):
    card = db.session.get(Card, card_id)
    if card is None:
        return jsonify({"error": "card not found"}), 404

    payload = request.get_json(silent=True) or {}
    before_id = payload.pop("before_id", None)
    after_id = payload.pop("after_id", None)

    try:
        card = card_service.update_card(card, payload, before_id, after_id)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(card.to_dict())


@cards_bp.delete("/<int:card_id>")
def delete_card(card_id):
    card = db.session.get(Card, card_id)
    if card is None:
        return jsonify({"error": "card not found"}), 404
    card_service.delete_card(card)
    return "", 204
