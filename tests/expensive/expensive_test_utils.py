import unittest
import os
from heymans.heymans import Heymans


class BaseExpensiveTest(unittest.TestCase):
    
    def setUp(self):
        from heymans.database.models import init_db
        init_db()
        self.heymans = Heymans(user_id='pytest', search_first=False)
