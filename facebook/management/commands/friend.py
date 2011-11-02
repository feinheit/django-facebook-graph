#coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from facebook.testusers import TestUsers
from facebook.modules.profile.user.models import TestUser
from facebook.graph import get_static_graph


class Command(BaseCommand):
    args = '<id1>, [<id2>], [<app name>]'
    help = 'Friend Testusers. Use friend <id1> [<id2="all">]'
    can_import_settings = True
    
    def handle(self, *args, **options):
        if args:
            try:
                arg1 = int(args[0])
            except AttributeError:
                raise CommandError('Arg %s must be integer' %user1 )

            try:
                arg2 = int(args[1])
            except IndexError:
                arg2 = None
            except AttributeError:
                raise CommandError('Arg %s must be integer or empty for all users.' %user2 )  
            try:
                app = args[2]
            except IndexError:
                app = None
        else:
             raise CommandError('Need at least one user_id.')

        graph = get_static_graph(app_dict=app)
        testusers = TestUsers(graph)
        try:
            user1 = TestUser.objects.get(id=arg1)
        except TestUser.DoesNotExist:
            raise CommandError('User1 does not exist.')
        if arg2:
            try:
                user2 = TestUser.objects.get(id=arg2)
            except TestUser.DoesNotExist:
                raise CommandError('User2 does not exist.')
            response = testusers.make_friends_with(user1, user2)
            self.stdout.write(u' %s\n' % response)
        else:
            users = TestUser.objects.exclude(id=user1.id)
            for user in users:
                response = testusers.make_friends_with(user1, user)
                self.stdout.write(u' %s\n' % response)
