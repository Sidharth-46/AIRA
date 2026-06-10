"""
AIRA — Input Validation Schemas
Marshmallow schemas for request validation.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re


class SignupSchema(Schema):
    """Validates signup requests."""

    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r"^[a-zA-Z0-9_]+$",
                error="Username must contain only letters, numbers, and underscores.",
            ),
        ],
    )
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
    )




class LoginSchema(Schema):
    """Validates login requests."""

    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))


class ChatCreateSchema(Schema):
    """Validates chat creation."""

    title = fields.String(
        load_default="New Chat",
        validate=validate.Length(max=200),
    )
    folder = fields.String(
        load_default=None,
        validate=validate.Length(max=100),
        allow_none=True,
    )


class MessageSchema(Schema):
    """Validates chat messages."""

    content = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50000),
    )
    workspace_context = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        required=False,
    )



class ChatUpdateSchema(Schema):
    """Validates chat updates."""

    title = fields.String(validate=validate.Length(max=200))
    folder = fields.String(validate=validate.Length(max=100), allow_none=True)


class FileCreateSchema(Schema):
    """Validates file/folder creation."""

    path = fields.String(required=True, validate=validate.Length(min=1, max=500))
    is_directory = fields.Boolean(load_default=False)
    content = fields.String(load_default="")


class ModelSwitchSchema(Schema):
    """Validates model switch requests."""

    model = fields.String(required=True, validate=validate.Length(min=1, max=100))


def validate_request(schema_class, data):
    """Validate request data against a schema. Returns (validated_data, errors)."""
    schema = schema_class()
    try:
        validated = schema.load(data)
        return validated, None
    except ValidationError as err:
        return None, err.messages
