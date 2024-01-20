import json
import logging
import time
from datetime import datetime, timedelta
from .models import db, User, Conversation, Attachment, Activity, Subscription
from .encryption import EncryptionManager
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger('heymans')


class DatabaseManager:
    
    def __init__(self, username: str, encryption_key: [str, bytes]):
        self.username = username
        self.encryption_manager = EncryptionManager(encryption_key)
        self.ensure_user_exists()
        logger.info(
            f'initializing database for user {self.username} ({self.user_id})')

    def ensure_user_exists(self):
        try:
            user = User.query.filter_by(username=self.username).one()
            self.user_id = user.user_id
        except NoResultFound:
            logger.info(f'creating new user: {self.username}')
            user = User(username=self.username)
            db.session.add(user)
            db.session.commit()
            self.user_id = user.user_id
            self.new_conversation()

    def get_active_conversation(self) -> dict:
        try:
            user = User.query.filter_by(user_id=self.user_id).one()
            conversation = Conversation.query.filter_by(
                conversation_id=user.active_conversation_id).one()
            decrypted_data = self.encryption_manager.decrypt_data(
                conversation.data)
            return json.loads(decrypted_data)
        except NoResultFound:
            logger.warning(
                f"No active conversation found for user {self.user_id}")
            return {}

    def set_active_conversation(self, conversation_id: int) -> bool:
        try:
            # We first get the active conversation
            conversation = Conversation.query.filter_by(
                conversation_id=conversation_id, user_id=self.user_id).one()
            # And then update the current time for that conversation so that
            # it ends on top
            decrypted_data = self.encryption_manager.decrypt_data(
                conversation.data)
            conversation_data = json.loads(decrypted_data)
            conversation_data['last_updated'] = time.time()
            json_data = json.dumps(conversation_data)
            encrypted_data = self.encryption_manager.encrypt_data(
                json_data.encode('utf-8'))
            conversation.data = encrypted_data
            # Finally we change the active conversation for the user
            user = User.query.filter_by(user_id=self.user_id).one()
            user.active_conversation_id = conversation.conversation_id
            db.session.commit()
            return True
        except NoResultFound:
            logger.warning(f"Conversation {conversation_id} not found or does "
                           f"not belong to user {self.user_id}")
            return False

    def update_active_conversation(self, conversation_data: dict) -> bool:
        try:
            user = User.query.filter_by(user_id=self.user_id).one()
            conversation = Conversation.query.filter_by(
                conversation_id=user.active_conversation_id).one()
            conversation_data['last_updated'] = time.time()
            json_data = json.dumps(conversation_data)
            encrypted_data = self.encryption_manager.encrypt_data(
                json_data.encode('utf-8'))
            conversation.data = encrypted_data
            db.session.commit()
            return True
        except NoResultFound:
            logger.warning(
                f"No active conversation to update for user {self.user_id}")
            return False

    def list_conversations(self) -> dict:
        
        conversations = {}
        for conversation in \
                Conversation.query.filter_by(user_id=self.user_id).all():
            try:
                data = json.loads(self.encryption_manager.decrypt_data(
                    conversation.data))
                conversations[conversation.conversation_id] = (
                     data.get('title', 'Untitled conversation'),
                     data.get('last_updated', time.time()))
            except Exception as e:
                logger.error(f"Error decrypting conversation data: {e}")
        return conversations

    def new_conversation(self) -> bool:
        try:
            conversation_data = {
                "title": "New conversation",
                "condensed_text": None,
                "message_history": [],
                "message_metadata": [],
                "last_updated": time.time()
            }
            json_data = json.dumps(conversation_data)
            encrypted_data = self.encryption_manager.encrypt_data(
                json_data.encode('utf-8'))
            conversation = Conversation(user_id=self.user_id,
                                        data=encrypted_data)
            db.session.add(conversation)
            db.session.commit()
            self.set_active_conversation(conversation.conversation_id)
            return True
        except Exception as e:
            logger.error(f"Error creating new conversation: {e}")
            return False

    def delete_conversation(self, conversation_id: int) -> bool:
        try:
            user = User.query.filter_by(user_id=self.user_id).one()
            conversation = Conversation.query.filter_by(
                conversation_id=conversation_id, user_id=self.user_id).one()
            if user.active_conversation_id == conversation.conversation_id:
                logger.warning(
                    f"Cannot delete active conversation {conversation_id} for "
                    f"user {self.user_id}")
                return False
            db.session.delete(conversation)
            db.session.commit()
            return True
        except NoResultFound:
            logger.warning(f"Conversation {conversation_id} not found or does "
                           f"not belong to user {self.user_id}")
            return False

    def list_attachments(self) -> dict:
        attachments = Attachment.query.filter_by(user_id=self.user_id).all()
        attachment_dict = {}
        for attachment in attachments:
            try:
                decrypted_data = self.encryption_manager.decrypt_data(
                    attachment.data)
                attachment_data = json.loads(decrypted_data)
                attachment_dict[attachment.attachment_id] = {
                    'filename' : attachment_data.get(
                        'filename', 'No filename'),
                    'description' : attachment_data.get(
                        'description', 'No description')
                }
            except Exception as e:
                logger.error(f"Error decrypting attachment data for "
                             f"attachment_id {attachment.attachment_id}: {e}")
        return attachment_dict

    def delete_attachment(self, attachment_id: int) -> bool:
        try:
            attachment = Attachment.query.filter_by(
                attachment_id=attachment_id, user_id=self.user_id).one()
            db.session.delete(attachment)
            db.session.commit()
            return True
        except NoResultFound:
            logger.warning(f"Attachment {attachment_id} not found or does not "
                           f"belong to user {self.user_id}")
            return False

    def add_attachment(self, attachment_data: dict) -> int:
        """Adds an attachment and returns the attachment_id or -1 if an error
        occurred. attachment_data should be a dict with filename, content,
        and description keys, where content is a base64-encoded str.
        """
        try:
            json_data = json.dumps(attachment_data)
            encrypted_data = self.encryption_manager.encrypt_data(
                json_data.encode('utf-8'))
            attachment = Attachment(user_id=self.user_id, data=encrypted_data)
            db.session.add(attachment)
            db.session.commit()
            return attachment.attachment_id
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
            return -1

    def get_attachment(self, attachment_id: int) -> dict:
        try:
            attachment = Attachment.query.filter_by(
                attachment_id=attachment_id, user_id=self.user_id).one()
            decrypted_data = self.encryption_manager.decrypt_data(
                attachment.data)
            return json.loads(decrypted_data)
        except NoResultFound:
            logger.warning(f"Attachment {attachment_id} not found or does not "
                           f"belong to user {self.user_id}")
            return {}
        except Exception as e:
            logger.error(f"Error decrypting attachment data for attachment_id "
                         f"{attachment_id}: {e}")
            return {}

    def add_activity(self, tokens_consumed: int):
        """Adds the number of tokens consumed using the current time."""
        new_activity = Activity(user_id=self.user_id, time=datetime.utcnow(),
                                tokens_consumed=tokens_consumed)
        db.session.add(new_activity)
        db.session.commit()

    def get_activity(self, after_time=None) -> int:
        """Retrieves the total number of tokens consumed since a particular 
        time, using the past hour as a default if no after_time is provided.
        """
        if after_time is None:
            after_time = datetime.utcnow() - timedelta(hours=1)

        total_tokens = db.session.query(func.sum(Activity.tokens_consumed)) \
            .filter(Activity.user_id == self.user_id) \
            .filter(Activity.time >= after_time) \
            .scalar()
        return total_tokens if total_tokens is not None else 0

    def update_subscription(self, stripe_customer_id: str,
                            stripe_subscription_id: str, from_date=None,
                            to_date=None):
        """Updates a subscription. By default the subscriptions starts 
        immediately and ends exactly one month from the current time. A user
        has only one subscription, which means that a subscription should be
        added if it doesn't exist, and updated if it already exists.
        """
        now = datetime.utcnow()
        from_date = from_date or now
        to_date = to_date or now + timedelta(days=31)
        subscription = Subscription.query.filter_by(
            user_id=self.user_id).first()
        if subscription:
            subscription.from_date = from_date
            subscription.to_date = to_date
        else:
            subscription = Subscription(
                user_id=self.user_id, from_date=from_date, to_date=to_date,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id)
            db.session.add(subscription)
        db.session.commit()

    def check_subscription(self) -> bool:
        """Returns a bool indicating whether the user is currently subscribed.
        """
        now = datetime.utcnow()
        subscription = Subscription.query.filter_by(
            user_id=self.user_id).first()
        return subscription and \
                subscription.from_date <= now < subscription.to_date

    def cancel_subscription(self):
        """Sets the to_date of the subscription to the current time if the user
        is currently subscribed.
        """
        if not self.check_subscription():
            return
        subscription = Subscription.query.filter_by(
            user_id=self.user_id).first()
        subscription.to_date = datetime.utcnow()
        db.session.commit()

    def get_stripe_customer_id(self) -> str:
        subscription_record = Subscription.query.filter(
            Subscription.user_id == self.user_id
        ).order_by(Subscription.from_date.desc()).first()
        if subscription_record:
            return subscription_record.stripe_customer_id
        return None

    @staticmethod
    def from_stripe_customer_id(stripe_customer_id: str) -> str:
        subscription_record = Subscription.query.filter(
            Subscription.stripe_customer_id == stripe_customer_id
        ).order_by(Subscription.from_date.desc()).first()
        if not subscription_record:
            return None
        user_record = User.query.filter(
            User.user_id == subscription_record.user_id
        ).order_by(Subscription.from_date.desc()).first()
        if not user_record:
            return None
        return DatabaseManager(username=user_record.username)
