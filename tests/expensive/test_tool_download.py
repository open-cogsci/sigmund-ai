from .expensive_test_utils import BaseExpensiveTest


class TestToolsDownload(BaseExpensiveTest):
    
    def _test_tool(self):
        query = 'Can you download https://raw.githubusercontent.com/open-cogsci/sigmund-ai/refs/heads/master/readme.md for me?'
        n = len(self.sigmund.database.list_attachments())
        for reply, metadata in self.sigmund.send_user_message(query):
            print(reply)
        assert len(self.sigmund.database.list_attachments()) == n + 1
