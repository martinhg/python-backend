from flask_classy import FlaskView, route
from flask import jsonify, request
from schemas import UserSchema, NotificationSchema, UserNotificationsSchema, MessageSchema
from models import User, Notification, Messages
from werkzeug.exceptions import Unauthorized, BadRequest, InternalServerError, Conflict
from database import db, push_service
from utils import MESSAGE_TITLE, MESSAGE_BODY


def validate_auth():
    auth = request.authorization
    if not auth:
        raise BadRequest("Authorization data was not provided")
    username = auth.username
    user = User.query.filter_by(username=username).first()
    if user is None or user.password != auth.password:
        raise Unauthorized("Incorrect username or password. Please try again.")
    return user


class UsersView(FlaskView):
    user_schema = UserSchema()
    notification_schema = NotificationSchema()
    user_notifications_schema = UserNotificationsSchema()
    messages_schema = MessageSchema()

    def index(self):
        users = User.query.all()
        users_data = self.user_schema.dump(users, many=True).data
        return jsonify({'users': users_data}), 200

    def get(self, id_user):
        user = User.query.filter(User.id == int(id_user)).first()
        user_data = self.user_schema.dump(user).data
        return jsonify({'user': user_data})

    # Notification functionalities

    @route('/notification', methods=['POST'])
    def notification(self):
        user_tokens = []
        notifications_to_users = []
        notification_data = request.json
        message_title = notification_data.get('message_title')
        message_body = notification_data.get('message_body')
        users_notifications = notification_data.get('users', None)
        notification = Notification(message_title, message_body)

        if users_notifications is None:
            user_tokens_result = User.query.filter(User.fcm_token is not None).with_entities(User.fcm_token).all()
            user_tokens = [token[0] for token in user_tokens_result]
            users_data = User.query.all()
            for user in users_data:
                notifications_to_users.append(user)
        else:
            for user in users_notifications:
                check_user = User.query.filter(User.username == user).first()
                notifications_to_users.append(check_user)
                get_token = check_user.fcm_token
                if get_token is not None:
                    user_tokens.append(get_token)

        notification.users = notifications_to_users

        try:
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise InternalServerError("Internal Server Error")

        try:
            push_service.notify_multiple_devices(registration_ids=user_tokens, message_title=message_title,
                                                 message_body=message_body)
        except Exception as e:
            raise BadRequest("Bad Request")

        return "", 204

    def user_notifications(self):
        user = validate_auth()
        user_id = user.id
        notifications_user = User.query.filter(User.id == user_id).first()
        notification_data = self.user_notifications_schema.dump(notifications_user).data
        return jsonify(notification_data)

    # User login

    def login(self):
        user = validate_auth()
        token = request.headers.get('fcm_token', None)
        if token:
            user.fcm_token = token
            try:
                db.session.merge(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise InternalServerError("Internal Server Error")
        user_data = self.user_schema.dump(user).data
        return jsonify({'user': user_data})

    # User logout

    @route('/logout', methods=['POST'])
    def logout(self):
        user = validate_auth()
        user.fcm_token = None
        try:
            db.session.merge(user)
            db.session.commit()
        except Exception as e:
            raise InternalServerError("User can't be properly logged out")
        return "", 204

    # User creation

    def post(self):
        user_data = request.json
        username = user_data.get('username', None)
        password = user_data.get('password', None)
        if user_data is not None and username is not None and password is not None:
            existing_user = User.query.filter(User.username == username).first()
            if existing_user is None:
                user = User(username, password)
                try:
                    db.session.add(user)
                    db.session.commit()
                    check_user = User.query.filter(User.username == username).first()
                    user_data = self.user_schema.dump(check_user).data
                except Exception as e:
                    db.session.rollback()
                    raise InternalServerError("User cannot be added to the database")
            else:
                raise Conflict("User already exists")
        else:
            raise BadRequest("The user or password were not sent correctly")
        return jsonify({'user': user_data})

    # Functionalities related to messages

    @route('/messages', methods=['POST'])
    def messsages(self):
        user = validate_auth()
        data = request.json
        message = data.get('message', None)
        user_friend = data.get('user_friend', None)
        if message and user_friend:
            existing_user = User.query.filter(User.username == user_friend).first()
            friend_token = existing_user.fcm_token
            if existing_user:
                message_data = Messages(message=message, user_sender_id=user.id, user_receiver_id=existing_user.id)
                try:
                    db.session.add(message_data)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    raise InternalServerError("Message cannot be registered")
                try:
                    push_service.notify_single_device(message_title=MESSAGE_TITLE,
                                                      message_body=MESSAGE_BODY.format(user.username),
                                                      registration_id=friend_token)
                except Exception as e:
                    raise InternalServerError("Message could not be sent")
            else:
                raise BadRequest("User entered does not exist")
        else:
            raise BadRequest("The data or user were not sent correctly")
        return "", 200

    @route('/user_messages', methods=['GET'])
    def user_messages(self):
        user = validate_auth()
        friend_id = request.headers.get('friend_id', None)
        if friend_id:
            user_messages = Messages.query.filter(Messages.user_receiver_id == friend_id).order_by(
                Messages.created_at.desc()).all()
        else:
            raise BadRequest("The data were not sent correctly")
        messages_data = self.messages_schema.dump(user_messages, many=True).data
        return jsonify({'messages': messages_data})

    @route('/user_conversations', methods=['GET'])
    def user_conversations(self):
        user = validate_auth()
        user_conversations = Messages.query.filter(
            Messages.user_sender_id == user.id).filter(Messages.user_receiver_id == user.id).group_by(
            Messages.user_sender_id, Messages.user_receiver_id).order_by(
            Messages.created_at.desc()).all()
        conversations_data = self.messages_schema.dump(user_conversations, many=True).data
        return jsonify({'conversations': conversations_data})
