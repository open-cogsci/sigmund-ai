import json
import logging
import time
from datetime import datetime, timedelta
from .. import config
from .models import db, User, Conversation, Activity, Subscription, Setting, \
    Message
from .encryption import EncryptionManager
from sqlalchemy import func, delete
from sqlalchemy.orm.exc import NoResultFound

logger = logging.getLogger('sigmund')


class DatabaseManager:
    
    def __init__(self, sigmund, username: str,
                 encryption_key: [str, bytes]=None):
        self.transient_settings = {}
        self._sigmund = sigmund
        self.username = username
        self.encryption_manager = EncryptionManager(encryption_key)
        self.ensure_user_exists()
        logger.info(
            f'initializing database for user {self.username} ({self.user_id})')
        
    def prune_detached_messages(self):
        """Delete all messages that are not attached to a conversation anymore
        due to an old bug in which messages where re-added but never deleted.
        """
        for conversation in Conversation.query.filter_by(
                user_id=self.user_id).all():
            logger.info(f'decrypting {conversation.conversation_id}, {len(conversation.data)} bytes')
            if len(conversation.data) > 20000:
                logger.info('skipping')
                continue
            decrypted_data = self.encryption_manager.decrypt_data(
                conversation.data)
            conversation_data = json.loads(decrypted_data)
            logger.info('getting attached messages')
            attached_message_ids = conversation_data.get('message_history', [])
            attached_message_ids = [
                msg_id for msg_id in attached_message_ids
                if isinstance(msg_id, int)
            ]
            logger.info('getting all messages')
            all_messages = Message.query.filter_by(
                conversation_id=conversation.conversation_id).all()
            for message in all_messages:
                if message.message_id not in attached_message_ids:
                    logger.info(f'deleting {message.message_id}')
                    db.session.delete(message)
        logger.info('committing')
        db.session.commit()
        logger.info('done')
            
    def ensure_user_exists(self):
        try:
            user = User.query.filter_by(username=self.username).one()
            self.user_id = user.user_id
            logger.info(f'user {self.username} exists')
        except NoResultFound:
            # This is a hack to fix a bug in earlier versions of Sigmund without
            # breaking log-in for existing users.
            #
            # If the user id doesn't exist, this may be because the user 
            # previously logged in through Google before the unique ID was 
            # included in the username. Currently, Google usernames look like
            # Name (google)::unique_id. Previously, Google usernames looked like
            # Name (google). If an old Google username exists, we automatically
            # rename the user to the new unique username.
            if '(google)::' in self.username:
                # Strip everything after (google)::
                old_username = self.username.split('(google)::')[0] + '(google)'
                logger.info(
                    f'Checking if {self.username} exists as {old_username}')
                try:                    
                    user = User.query.filter_by(username=old_username).one()
                    self.user_id = user.user_id
                except NoResultFound:
                    # No the user really doesn't exist
                    pass
                else:
                    # Yes, the user has an old-style name, so we need to update
                    # the database so that User.username is set to old username
                    user.username = self.username
                    db.session.commit()
                    return
            # If the user doesn't exist, we create it and start a new 
            # conversation
            logger.info(f'creating new user: {self.username}')
            user = User(username=self.username)
            db.session.add(user)
            db.session.commit()
            self.user_id = user.user_id
            self.new_conversation()
    
    def get_message(self, message_id: int) -> dict:
        # If it's not an int, then it's an old-style mesage
        if not isinstance(message_id, int):
            return message_id
        try:
            # First, check if the message exists in the new Message table
            message = Message.query.filter_by(message_id=message_id).first()
            if message:
                # If it exists, decrypt and return the message
                decrypted_data = self.encryption_manager.decrypt_data(message.data)
                return json.loads(decrypted_data)
            # If the message doesn't exist, something is wrong.
            logger.error(f"Message {message_id} does not exist")
            return {}
        except Exception as e:
            logger.error(f"Error retrieving message {message_id}: {e}")
            return {}
            
    def get_message_history(self, conversation_data):
        """Returns a list of message dicts, excluding empty ones"""
        message_ids = conversation_data.get('message_history', [])
        message_history = []
        for msg_id in message_ids:
            msg = self.get_message(msg_id)
            if msg:
                message_history.append(msg)
        return message_history

    
    def add_message(self, conversation_id: int, message_data: dict) -> int:
        json_data = json.dumps(message_data)
        encrypted_data = self.encryption_manager.encrypt_data(
            json_data.encode('utf-8'))
        message = Message(conversation_id=conversation_id, data=encrypted_data)
        db.session.add(message)
        db.session.commit()
        return message.message_id
    
    def get_active_conversation(self) -> dict:
        try:
            user = User.query.filter_by(user_id=self.user_id).one()
            conversation = Conversation.query.filter_by(
                conversation_id=user.active_conversation_id).one()
        except NoResultFound:
            logger.warning(f"No active conversation found for user {self.user_id}")
            return {}    
        decrypted_data = self.encryption_manager.decrypt_data(conversation.data)
        conversation_data = json.loads(decrypted_data)
        conversation_data['message_history'] = self.get_message_history(
            conversation_data)
        return conversation_data            

    def _get_conversation(self, conversation_id: int):
        """Retrieves a conversation for the current user.

        Parameters
        ----------
        conversation_id : int
            The ID of the conversation to retrieve

        Returns
        -------
        Conversation or None
            The Conversation object if found and belongs to the user, None otherwise
        """
        try:
            conversation = Conversation.query.filter_by(
                conversation_id=conversation_id, user_id=self.user_id).one()
            return conversation
        except NoResultFound:
            logger.warning(f"Conversation {conversation_id} not found or does "
                           f"not belong to user {self.user_id}")
            return None

    def _decrypt_conversation_data(self, conversation):
        """Decrypts and parses conversation data.

        Parameters
        ----------
        conversation : Conversation
            The conversation object with encrypted data

        Returns
        -------
        dict
            The decrypted and parsed conversation data as a dictionary
        """
        decrypted_data = self.encryption_manager.decrypt_data(conversation.data)
        return json.loads(decrypted_data)

    def _encrypt_conversation_data(self, conversation_data: dict):
        """Encrypts conversation data.

        Parameters
        ----------
        conversation_data : dict
            The conversation data dictionary to encrypt

        Returns
        -------
        bytes
            The encrypted data
        """
        json_data = json.dumps(conversation_data)
        return self.encryption_manager.encrypt_data(json_data.encode('utf-8'))

    def _update_conversation_data(self, conversation, conversation_data: dict):
        """Updates and saves encrypted conversation data.

        Parameters
        ----------
        conversation : Conversation
            The conversation object to update
        conversation_data : dict
            The updated conversation data dictionary
        """
        encrypted_data = self._encrypt_conversation_data(conversation_data)
        conversation.data = encrypted_data
        db.session.commit()

    def set_active_conversation(self, conversation_id: int) -> bool:
        """Sets the active conversation for the current user.

        This method retrieves the specified conversation, updates its last_updated
        timestamp, encrypts the updated data, and sets it as the user's active
        conversation.

        Parameters
        ----------
        conversation_id : int
            The ID of the conversation to set as active

        Returns
        -------
        bool
            True if the conversation was successfully set as active, False if
            the conversation was not found or doesn't belong to the user
        """
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return False
    
        # Update the last_updated timestamp
        conversation_data = self._decrypt_conversation_data(conversation)
        conversation_data['last_updated'] = time.time()
        self._update_conversation_data(conversation, conversation_data)
    
        # Change the active conversation for the user
        user = User.query.filter_by(user_id=self.user_id).one()
        user.active_conversation_id = conversation.conversation_id
        db.session.commit()
        return True

    def set_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Updates the title of a conversation.

        This method retrieves the specified conversation, decrypts its data,
        updates the title field, and re-encrypts the data before committing
        to the database.

        Parameters
        ----------
        conversation_id : int
            The ID of the conversation to update
        title : str
            The new title for the conversation

        Returns
        -------
        bool
            True if the title was successfully updated, False if the
            conversation was not found or doesn't belong to the user
        """
        conversation = self._get_conversation(conversation_id)
        if conversation is None:
            return False
    
        # Update the title
        conversation_data = self._decrypt_conversation_data(conversation)
        conversation_data['title'] = title
        self._update_conversation_data(conversation, conversation_data)
        return True
    
    def update_active_conversation(self, conversation_data: dict) -> bool:
        """Updates the active conversation. The messages are saved in a 
        separate table as separate entries. However, all messages are replaced
        when the conversation is updated. That the conversation doesn't grow
        when a new message is added, but rather is reconstructed.
        """
        try:
            user = User.query.filter_by(user_id=self.user_id).one()
            conversation = Conversation.query.filter_by(
                conversation_id=user.active_conversation_id
            ).one()
        except NoResultFound:
            logger.warning(
                f"No active conversation to update for user {self.user_id}")
            return            
        logger.info(f'updating conversation {user.active_conversation_id}')
        logger.info('deleting old messages')
        # Batch delete all messages linked to this conversation, because we
        # will recreate new messages
        db.session.execute(
            delete(Message).where(
                Message.conversation_id == conversation.conversation_id)
        )
        logger.info('adding new messages')
        # Extract new messages and store them separately
        message_history = conversation_data.pop('message_history', [])
        message_ids = []
        for message in message_history:
            message_id = self.add_message(conversation.conversation_id,
                                          message)
            message_ids.append(message_id)
        conversation_data['message_history'] = message_ids
        conversation_data['last_updated'] = time.time()
        json_data = json.dumps(conversation_data)
        encrypted_data = self.encryption_manager.encrypt_data(
            json_data.encode('utf-8'))
        conversation.data = encrypted_data
        logger.info('committing conversation')
        db.session.commit()
        logger.info('done')
        return conversation.conversation_id

    def list_conversations(self, query=None) -> dict:
        conversations = {}
        user = User.query.filter_by(user_id=self.user_id).one()
        for conversation in \
                Conversation.query.filter_by(user_id=self.user_id).all():
            try:
                data = json.loads(self.encryption_manager.decrypt_data(
                    conversation.data))
                # Don't list empty conversations except for the active one
                if len(data.get('message_history', [])) < 2 and \
                        user.active_conversation_id != conversation.conversation_id:
                    continue
                title = data.get('title', 'Untitled conversation')
                if query is not None:
                    # First check title match
                    if query.lower() not in title.lower():
                        # If the title doesn't match, then we do a full-text
                        # search on the message history
                        match = False
                        for message in self.get_message_history(data):
                            message_text = message[1]
                            if query.lower() in message_text.lower():
                                match = True
                                break
                        if not match:
                            continue
                conversations[conversation.conversation_id] = (
                     title, data.get('last_updated', time.time()))
            except Exception as e:
                logger.error(f"Error decrypting conversation data: {e}")
        return conversations
    
    def export_conversations(self) -> dict:
        conversations = []
        for conversation in \
                Conversation.query.filter_by(user_id=self.user_id).all():
            try:
                decrypted_data = self.encryption_manager.decrypt_data(
                    conversation.data)
                conversation_data = json.loads(decrypted_data)
                message_history = self.get_message_history(conversation_data)
            except Exception as e:
                logger.error(f"Error decrypting conversation data: {e}")
            else:
                conversation_data['message_history'] = message_history
                conversations.append(conversation_data)
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

            # Delete associated messages
            Message.query.filter_by(conversation_id=conversation_id).delete()

            # Delete the conversation
            db.session.delete(conversation)
            db.session.commit()
            return True
        except NoResultFound:
            logger.warning(f"Conversation {conversation_id} not found or does "
                           f"not belong to user {self.user_id}")
            return False

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

    def add_subscription_record(self, stripe_customer_id: str,
                                stripe_subscription_id: str,
                                from_date=None, to_date=None):
        """Always append a new subscription record. Do not update old rows.
        from_date defaults to now; to_date defaults to now + subscription_length.
        """
        now = datetime.utcnow()
        from_date = from_date or now
        to_date = to_date or now + timedelta(days=config.subscription_length)
        subscription = Subscription(
            user_id=self.user_id,
            from_date=from_date,
            to_date=to_date,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id
        )
        db.session.add(subscription)
        db.session.commit()

    def update_subscription(self, stripe_customer_id: str,
                            stripe_subscription_id: str, from_date=None,
                            to_date=None):
        """Backwards-compatible wrapper that appends a new subscription record."""
        return self.add_subscription_record(
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            from_date=from_date,
            to_date=to_date
        )

    def check_subscription(self) -> bool:
        """Return True if at least one subscription row is currently active."""
        now = datetime.utcnow()
        # Efficient existence check
        return db.session.query(
            db.exists().where(
                (Subscription.user_id == self.user_id) &
                (Subscription.from_date <= now) &
                (Subscription.to_date > now)
            )
        ).scalar()

    def get_stripe_customer_id(self) -> str:
        """Return the stripe_customer_id of the subscription with the latest to_date.
        If multiple share the same to_date, pick the latest from_date as tie-breaker.
        """
        subscription_record = (
            Subscription.query
            .filter(Subscription.user_id == self.user_id)
            .order_by(Subscription.to_date.desc(), Subscription.from_date.desc())
            .first()
        )
        return subscription_record.stripe_customer_id if subscription_record else None

    @staticmethod
    def from_stripe_customer_id(stripe_customer_id: str):
        """Return a DatabaseManager instance for the user most recently associated
        with this stripe_customer_id (based on latest to_date, then from_date).
        """
        subscription_record = (
            Subscription.query
            .filter(Subscription.stripe_customer_id == stripe_customer_id)
            .order_by(Subscription.to_date.desc(), Subscription.from_date.desc())
            .first()
        )
        if not subscription_record:
            return None
        user_record = User.query.filter(User.user_id == subscription_record.user_id).first()
        if not user_record:
            return None
        return DatabaseManager(None, username=user_record.username)

    def get_setting(self, key: str) -> str:
        """Retrieve a setting value for the current user, which is available
        as self.user_id. If the setting does not exist, return the default
        value as specified in the config or None if no default has been 
        specified.
        """
        if key in self.transient_settings:
            return self.transient_settings[key]
        setting = db.session.query(Setting).filter_by(
            user_id=self.user_id, key=key).first()
        return setting.value if setting \
            else config.settings_default.get(key, None)

    def set_setting(self, key: str, value: str, transient: bool = False):
        """Set a setting to specified value for the current user. If the
        setting already exists, overwrite it. When transient is True, the 
        setting is not stored in the database, but only used for this session.
        """
        if transient:
            self.transient_settings[key] = value
            return
        setting = Setting.query.filter_by(
            user_id=self.user_id, key=key).first()
        if setting:
            setting.value = value
        else:
            new_setting = Setting(user_id=self.user_id, key=key,
                                  value=value)
            db.session.add(new_setting)
        db.session.commit()

    def list_settings(self) -> dict:
        """Returns a dict of all settings for the current user."""
        settings = {}
        setting_objs = db.session.query(Setting).filter_by(
            user_id=self.user_id).all()
        for setting in setting_objs:
            settings[setting.key] = setting.value
        settings.update(self.transient_settings)
        return settings
