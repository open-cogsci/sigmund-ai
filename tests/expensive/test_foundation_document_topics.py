import unittest
from sigmund.sigmund import Sigmund
from sigmund import config
import logging
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)


class TestFoundationDocumentTopics(unittest.TestCase):
    
    def setUp(self):
        from sigmund.database.models import drop_db, init_db
        drop_db()
        init_db()
        config.max_tokens_per_hour = float('inf')
        config.log_replies = True
        config.search_enabled = True
        self.sigmund = Sigmund(user_id='pytest', model_config='dummy',
                               foundation_document_topics=['opensesame'])
        
    def test(self):
        for result in self.sigmund.send_user_message('dummy query'):
            print(result)
        assert any(d['topic'] == 'opensesame'
                   for d in self.sigmund.documentation._documents)
