from marshmallow import fields, Schema


class MessageSchema(Schema):
    id = fields.Integer()
    message = fields.String()
    created_at = fields.DateTime()
    user_sender_id = fields.Integer()
    user_receiver_id = fields.Integer()


class NotificationSchema(Schema):
    id = fields.Integer()
    title = fields.String()
    message = fields.String()
    datetime = fields.DateTime()


class UserNotificationsSchema(Schema):
    notifications = fields.List(fields.Nested(NotificationSchema()))


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.String()
