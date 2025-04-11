import logging
import os
logger = logging.getLogger('sigmund')
# Depending on whether we are running inside a Flask app or not, we need to
# instantiate the database model differently. It is difficult to determine
# automatically whether Flask is running, because at this point we're still
# in the initialization phase. Therefore, we're explicitly setting an 
# environment variable when creating the Flask app.
if os.environ.get('USE_FLASK_SQLALCHEMY', False):
    logger.info('using flask_sqlachemy')
    from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy
    db = _BaseSQLAlchemy()
    Column = db.Column
    Integer = db.Integer
    String = db.String
    ForeignKey = db.ForeignKey
    LargeBinary = db.LargeBinary
    DateTime = db.DateTime
    Model = db.Model
else:
    from sqlalchemy import create_engine, Column, Integer, String, \
        ForeignKey, LargeBinary, DateTime
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import scoped_session, sessionmaker
    import logging
    logger.info('using standalone_sqlachemy')
    engine = create_engine('sqlite:///:memory:')
    session = scoped_session(sessionmaker(autocommit=False, autoflush=False,
                                          bind=engine))
    Base = declarative_base()
    # Create a db object that mimics Flask-SQLAlchemy's, with Model as an 
    # attribute
    class SQLAlchemy:
        def __init__(self, metadata):
            self.Model = declarative_base(metadata=metadata)
    db = SQLAlchemy(metadata=Base.metadata)
    db.session = session
    Model = db.Model
    Model.query = session.query_property()
    def init_db(): Model.metadata.create_all(bind=engine)
    def drop_db(): Model.metadata.drop_all(bind=engine)


class User(Model):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    active_conversation_id = Column(
        Integer, ForeignKey('conversation.conversation_id'), index=True)


class Conversation(Model):
    __tablename__ = 'conversation'

    conversation_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), index=True)
    # Data corresponds to an encrypted blob. After encryption, it becomes a
    # JSON string with the following format:
    # {
    #     "condensed_text": "A summary",
    #     "message_history": [
    #         message_id1,
    #         message_id2
    #     ],
    #     "condensed_message_history": [
    #         { message object1 },
    #         { message object2 }
    #     ]
    #     'title': self._conversation_title,
    # }
    # The message_ids refer to entries in the message table below. For older
    # conversations, the message_ids may instead by dicts. The 
    # DatabaseManager.get_message() function takes care of this.    
    data = Column(LargeBinary)


class Message(Model):
    __tablename__ = 'message'

    message_id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer,
                             ForeignKey('conversation.conversation_id'),
                             index=True)
    # Data corresponds to an encrypted blob. After encryption, it becomes a
    # JSON string.
    data = Column(LargeBinary)


class Activity(Model):
    __tablename__ = 'activity'

    activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), index=True)
    time = Column(DateTime)
    tokens_consumed = Column(Integer)


class Subscription(Model):
    __tablename__ = 'subscription'

    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), index=True)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    stripe_subscription_id = Column(String(80))
    stripe_customer_id = Column(String(80))


class Setting(Model):
    __tablename__ = 'setting'

    setting_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), index=True)
    key = Column(String(80))
    value = Column(String(80))
