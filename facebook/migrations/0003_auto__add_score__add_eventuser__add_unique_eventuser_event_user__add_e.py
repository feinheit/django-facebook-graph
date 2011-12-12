# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Score'
        db.create_table('facebook_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['facebook.User'])),
            ('score', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('application_id', self.gf('django.db.models.fields.BigIntegerField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('facebook', ['Score'])

        # Adding model 'EventUser'
        db.create_table('facebook_eventuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['facebook.Event'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['facebook.User'])),
            ('rsvp_status', self.gf('django.db.models.fields.CharField')(default='attending', max_length=10)),
        ))
        db.send_create_signal('facebook', ['EventUser'])

        # Adding unique constraint on 'EventUser', fields ['event', 'user']
        db.create_unique('facebook_eventuser', ['event_id', 'user_id'])

        # Adding model 'Event'
        db.create_table('facebook_event', (
            ('_graph', self.gf('facebook.fields.JSONField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.BigIntegerField')(unique=True, primary_key=True)),
            ('_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('_link', self.gf('django.db.models.fields.URLField')(max_length=255, null=True, blank=True)),
            ('_picture', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
            ('_pic_square', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
            ('_pic_small', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
            ('_pic_large', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
            ('_pic_crop', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
            ('_owner', self.gf('facebook.fields.JSONField')(null=True, blank=True)),
            ('_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('_start_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('_end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('_location', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('_venue', self.gf('facebook.fields.JSONField')(null=True, blank=True)),
            ('_privacy', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('_updated_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('facebook', ['Event'])

        # Adding model 'Achievment'
        db.create_table('facebook_achievment', (
            ('id', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('image', self.gf('facebook.fields.JSONField')(blank=True)),
            ('points', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('updated_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('context', self.gf('facebook.fields.JSONField')(blank=True)),
        ))
        db.send_create_signal('facebook', ['Achievment'])

    def backwards(self, orm):
        
        # Removing unique constraint on 'EventUser', fields ['event', 'user']
        db.delete_unique('facebook_eventuser', ['event_id', 'user_id'])

        # Deleting model 'Score'
        db.delete_table('facebook_score')

        # Deleting model 'EventUser'
        db.delete_table('facebook_eventuser')

        # Deleting model 'Event'
        db.delete_table('facebook_event')

        # Deleting model 'Achievment'
        db.delete_table('facebook_achievment')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'facebook.achievment': {
            'Meta': {'object_name': 'Achievment'},
            'context': ('facebook.fields.JSONField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'image': ('facebook.fields.JSONField', [], {'blank': 'True'}),
            'points': ('django.db.models.fields.SmallIntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'facebook.event': {
            'Meta': {'ordering': "('_start_time',)", 'object_name': 'Event'},
            '_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            '_end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_link': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            '_location': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            '_owner': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_pic_crop': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_large': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_small': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_square': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_picture': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_privacy': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            '_start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_updated_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_venue': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'invited': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['facebook.User']", 'through': "orm['facebook.EventUser']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'facebook.eventuser': {
            'Meta': {'unique_together': "[('event', 'user')]", 'object_name': 'EventUser'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['facebook.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rsvp_status': ('django.db.models.fields.CharField', [], {'default': "'attending'", 'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['facebook.User']"})
        },
        'facebook.page': {
            'Meta': {'object_name': 'Page'},
            '_access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_likes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_link': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            '_pic_crop': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_large': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_small': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_square': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_picture': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'facebook.photo': {
            'Meta': {'object_name': 'Photo'},
            '_from_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_like_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_likes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'photo_likes'", 'symmetrical': 'False', 'to': "orm['facebook.User']"}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'fb_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'facebook.post': {
            'Meta': {'ordering': "['-_created_time']", 'object_name': 'Post'},
            '_actions': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_application': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_caption': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            '_comments': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            '_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'facebook_post_posts_sent'", 'null': 'True', 'to': "orm['facebook.User']"}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_icon': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            '_likes': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_link': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            '_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            '_object_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            '_picture': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            '_privacy': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_properties': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_source': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            '_story': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            '_subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            '_targeting': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_to': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_type': ('django.db.models.fields.CharField', [], {'default': "'status'", 'max_length': '20'}),
            '_updated_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'facebook.request': {
            'Meta': {'object_name': 'Request'},
            '_application_id': ('django.db.models.fields.BigIntegerField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            '_created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            '_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            '_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'request_from_set'", 'null': 'True', 'to': "orm['facebook.User']"}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            '_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'request_to_set'", 'null': 'True', 'to': "orm['facebook.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'facebook.score': {
            'Meta': {'ordering': "['-score']", 'object_name': 'Score'},
            'application_id': ('django.db.models.fields.BigIntegerField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['facebook.User']"})
        },
        'facebook.testuser': {
            'Meta': {'object_name': 'TestUser'},
            '_birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            '_email': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            '_first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            '_gender': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            '_link': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            '_locale': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            '_location': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            '_pic_crop': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_large': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_small': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_square': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_picture': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'belongs_to': ('django.db.models.fields.BigIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'friends': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'friends_rel_+'", 'to': "orm['facebook.TestUser']"}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'login_url': ('django.db.models.fields.URLField', [], {'max_length': '160', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'facebooktestuser'", 'unique': 'True', 'null': 'True', 'to': "orm['auth.User']"})
        },
        'facebook.user': {
            'Meta': {'object_name': 'User'},
            '_birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            '_email': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            '_first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            '_gender': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            '_graph': ('facebook.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            '_last_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            '_link': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            '_locale': ('django.db.models.fields.CharField', [], {'max_length': '6', 'null': 'True', 'blank': 'True'}),
            '_location': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'}),
            '_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            '_pic_crop': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_large': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_small': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_pic_square': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_picture': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'friends': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'friends_rel_+'", 'to': "orm['facebook.User']"}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'facebookuser'", 'unique': 'True', 'null': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['facebook']
