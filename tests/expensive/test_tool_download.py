from .expensive_test_utils import BaseExpensiveTest


class TestToolsDownload(BaseExpensiveTest):
    
    def _test_tool(self):
        query = 'Can you download https://www.biorxiv.org/content/10.1101/2023.12.05.570327v1.full.pdf for me?'
        n = len(self.sigmund.database.list_attachments())
        for reply, metadata in self.sigmund.send_user_message(query):
            print(reply)
        assert len(self.sigmund.database.list_attachments()) == n + 1