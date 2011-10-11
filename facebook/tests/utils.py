from django.test import TestCase
from facebook.utils import *
from django.utils import unittest
from django.test.client import RequestFactory
from django.contrib.sessions.tests import DatabaseSessionTests

from facebook.tests import settings

class UtilsTestCase(DatabaseSessionTests):
    
    def setUp(self):
        super(UtilsTestCase, self).setUp()
        self.factory = RequestFactory()
        self.app = settings.FACEBOOK_APPS.values()[0]

    def test_settings(self):
        fb = self.app
        self.assertEqual(fb['ID'], '218940591464663')
        self.assertEqual(fb['SECRET'], 'd4ba1920446f44d557fc6518c475d9b7')
        self.assertEqual(fb['CANVAS-PAGE'], 'http://apps.facebook.com/fhunittest/')
        self.assertEqual(fb['CANVAS-URL'], 'http://fht.li/unittest/')
        self.assertEqual(fb['SECURE-CANVAS-URL'], 'https://fht.li/unittest/')
        self.assertEqual(fb['REDIRECT-URL'], 'http://apps.facebook.com/fhunittest/')
        self.assertEqual(fb['DOMAIN'], 'fht.li')
    
    def test_get_graph(self):
        request = self.factory.get('/')
        setattr(request, 'session', self.session)
        graph = get_graph(request, app_dict=self.app)  # Have to pass app name. 
        self.assertTrue(isinstance(graph, Graph))
        self.assertTrue(isinstance(graph.fb_session, FBSession))
        self.assertTrue(isinstance(graph.access_token, basestring))
        self.assertEqual(graph.via, 'application')
        self.assertIsNone(graph.get_token_from_session())
        self.assertIsNone(graph.get_token_from_cookie())
        self.assertTrue(graph.fb_session.app_is_authenticated)
        self.assertIsNone(graph.me)
        self.assertEqual(graph.app_id, '218940591464663')
        # self.assertFalse(graph.fb_session.app_is_authenticated)  Possible Thread-Safe error
        
    def test_static_graph(self):
        graph = get_static_graph(app_dict=self.app)
        self.assertIsNone(graph.HttpRequest)
        self.assertTrue(isinstance(graph.fb_session, FBSessionNoOp))
        self.assertTrue(isinstance(graph.access_token, basestring))
        self.assertEqual(graph.via, 'application')
        self.assertIsNone(graph.me)

    def test_public_graph(self):
        graph = get_public_graph(app_dict=self.app)
        self.assertIsNone(graph.HttpRequest)
        self.assertTrue(isinstance(graph.fb_session, FBSessionNoOp))
        self.assertIsNone(graph.access_token)
        self.assertEqual(graph.via, 'No token requested')
        self.assertIsNone(graph.me)

        
        
        
        