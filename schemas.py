from marshmallow import Schema
from marshmallow import fields
from marshmallow import validate


class BusSchema(Schema):
    busId = fields.String(required=True)
    lat = fields.Float(required=True)
    lng = fields.Float(required=True)
    route = fields.String(required=True)


class WindowBoundDataSchema(Schema):
    east_lng = fields.Float(required=True)
    north_lat = fields.Float(required=True)
    south_lat = fields.Float(required=True)
    west_lng = fields.Float(required=True)


class WindowBoundSchema(Schema):
    msgType = fields.String(
        required=True,
        validate=validate.OneOf(["newBounds"])
    )
    data = fields.Nested("WindowBoundDataSchema", required=True)
