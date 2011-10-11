from django.conf import settings
import sys, os

FACEBOOK_APPS = {
    'FB_Unittest' : {
            'ID': '218940591464663',
            'SECRET': 'd4ba1920446f44d557fc6518c475d9b7',
            'CANVAS-PAGE': 'http://apps.facebook.com/fhunittest/',
            'CANVAS-URL': 'http://fht.li/unittest/',
            'SECURE-CANVAS-URL': 'https://fht.li/unittest/',
            'REDIRECT-URL': 'http://apps.facebook.com/fhunittest/',
            'DOMAIN': 'fht.li'
    }
}

TESTUSERS = [
    {   'first_name': "Margaret",
        'gender': "female",
        'id': 100003005576619,
        'last_name': "Okelolawitz",
        'link': "http://www.facebook.com/profile.php?id=100003005576619",
        'locale': "de_DE",
        'middle_name': "Amckeegffai",
        'name': "Margaret Amckeegffai Okelolawitz",
        'updated_time': "2011-10-07T15:13:11+0000"
    },
    {   'first_name': "Nancy",
        'gender': "female",
        'id': 100002343838234,
        'last_name': "Carrieroberg",
        'link': "http://www.facebook.com/profile.php?id=100002343838234",
        'locale': "de_DE",
        'middle_name': "Ambcdchchbcd",
        'name': "Nancy Ambcdchchbcd Carrieroberg",
        'updated_time': "2011-05-06T22:12:59+0000",
    }, 
]