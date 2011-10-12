#coding: utf-8
""" This test checks user login and authorization. 
    It requires Selenium and Firefox.

    Get Selenium here: http://seleniumhq.org/
    sudo pip install selenium
    Read the docs: http://readthedocs.org/docs/selenium-python/en/latest/
"""

from django.test import TestCase
from facebook.utils import *
from facebook.testusers import TestUsers
from django.utils import unittest
from django.test.client import RequestFactory
from django.contrib.sessions.tests import DatabaseSessionTests

from facebook.tests import settings

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

TEST_APP = 'FB_Unittest'

class UserTestCase(DatabaseSessionTests):
    
    def firefox(self, testuser):
        driver = webdriver.Firefox()
        driver.get(testuser.login_url)
        # Sometimes it needs two calls to the URL.
        if driver.title <> testuser._name:
            driver.get(testuser.login_url)
        return driver
        
    
    def setUp(self):
        super(UserTestCase, self).setUp()
        self.factory = RequestFactory()
        self.app = settings.FACEBOOK_APPS[TEST_APP]
        self.testusers = getattr(settings, 'TESTUSERS')
        
    def test_testusers_settings(self):
        """ Make sure the test user settings are valid."""
        self.assertIsInstance(self.testusers, list)
        self.assertGreaterEqual(len(self.testusers), 2 )
        self.assertIsInstance(self.testusers[0], dict)
        self.assertIsInstance(self.testusers[1], dict)
    
    def test_testusers(self):
        """ The test users are still the ones in the settings."""
        graph = get_static_graph(app_dict=self.app)
        testusers = TestUsers(graph)
        users = testusers.get_test_users()
        self.assertEqual(users[0]._name, self.testusers[0]['name'])
        self.assertEqual(int(users[0].id), self.testusers[0]['id'])
        self.assertEqual(users[1]._name, self.testusers[1]['name'])
        self.assertEqual(int(users[1].id), self.testusers[1]['id'])
        
        user1 = users[0]
        self.driver1 = self.firefox(user1)
        # Check if the Facebook login was successfull:
        self.assertEqual(self.driver1.title, user1._name)
        
        # Try a login:
        self.driver1.get('https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s' % (self.app['ID'], 
                                                                        self.app['REDIRECT-URL']))
        self.assertEqual(self.driver1.title, u'Unittest auf Facebook')
        self.driver1.get('%scanvas/' % self.app['CANVAS-PAGE'])
        
        self.driver1.close()
        """
        user2 = users[1]
        driver2 = webdriver.Firefox()
        driver2.get(user2.login_url)
        if driver2.title <> user2._name:
            driver2.get(user2.login_url)
        self.assertEqual(driver.title, user1._name)
        if driver2.title <> user2._name:
            return # No point of testing further.
        """
        
    
    
        
        