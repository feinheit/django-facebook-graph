from django.core.management.base import BaseCommand, CommandError
from facebook.testusers import TestUsers
from facebook.models import TestUser
from facebook.utils import get_static_graph
from optparse import make_option
from django.conf import settings

class Command(BaseCommand):
    args = '[<App Name>], [<App Name>], ...'
    help = 'Update Testusers for your apps'
    can_import_settings = True
    option_list = BaseCommand.option_list + (
                            make_option('--update', '-u',
                                action='store_true',
                                dest='update',
                                default=False,
                                help='Update Login URL.'),
                            )
    
    def handle(self, *args, **options):
        apps = []
        update = options.get('update')  # Not implemented yet. Always update.
        if args:
            for arg in args:
                try:
                    application = settings.FACEBOOK_APPS[arg]
                    apps.append(application)
                except KeyError:
                    raise CommandError('Application %s does not exist' %arg )
        else:
             apps.append(settings.FACEBOOK_APPS.values()[0])
        
        for app in apps:
            graph = get_static_graph(app_dict=app)
            testusers = TestUsers(graph)
            users = testusers.get_test_users()
            self.stdout.write(u' Testusers: %s\n' % users)
            for user in users:
                installed = '*' if getattr(user, 'access_token', False) else ''
                self.stdout.write(u'%s\t%s %s\n' % (user.id, user.login_url, installed))