from django.core.management.base import BaseCommand, CommandError
from facebook.testusers import TestUsers
from facebook.models import TestUser
from facebook.utils import get_static_graph
from optparse import make_option
from django.conf import settings

class Command(BaseCommand):
    args = '[<App Name>], [<App Name>], ...'
    help = 'Generates a new Facebook test user for your app.'
    option_list = BaseCommand.option_list + (
                            make_option('--installed', '-i',
                                action='store_true',
                                dest='installed',
                                default=False,
                                help='User has app installed.'),
                            )
    can_import_settings = True
    
    def handle(self, *args, **options):
        installed = options.get('installed')
        apps = []
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
            user = testusers.generate_new_test_user(installed=installed)
            self.stdout.write(u'Generated new Testuser: %s\n' % user)