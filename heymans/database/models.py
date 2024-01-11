from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    active_conversation_id = db.Column(
        db.Integer, db.ForeignKey('conversation.conversation_id'))


class Conversation(db.Model):
    __tablename__ = 'conversation'

    conversation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    data = db.Column(db.LargeBinary)


class Attachment(db.Model):
    __tablename__ = 'attachment'

    attachment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    data = db.Column(db.LargeBinary)


class Activity(db.Model):
    __tablename__ = 'activity'

    activity_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    time = db.Column(db.DateTime)
    tokens_consumed = db.Column(db.Integer)


class Subscription(db.Model):
    __tablename__ = 'subscription'

    subscription_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    from_date = db.Column(db.DateTime)
    to_date = db.Column(db.DateTime)
