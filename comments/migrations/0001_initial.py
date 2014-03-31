# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomUser'
        db.create_table(u'comments_customuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email', self.gf('django.db.models.fields.EmailField')(db_index=True, unique=True, max_length=255, blank=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_admin', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('avatar_num', self.gf('django.db.models.fields.IntegerField')(default=6)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'comments', ['CustomUser'])

        # Adding M2M table for field groups on 'CustomUser'
        db.create_table(u'comments_customuser_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(u'comments_customuser_groups', ['customuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'CustomUser'
        db.create_table(u'comments_customuser_user_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(u'comments_customuser_user_permissions', ['customuser_id', 'permission_id'])

        # Adding model 'Site'
        db.create_table(u'comments_site', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('anonymous_allowed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rs_customer_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'comments', ['Site'])

        # Adding model 'Thread'
        db.create_table(u'comments_thread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(related_name='threads', to=orm['comments.Site'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('allow_comments', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('liked_by_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('disliked_by_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('titles', self.gf('jsonfield.fields.JSONField')(default={'page_title': '', 'h1_title': '', 'selector_title': ''})),
        ))
        db.send_create_signal(u'comments', ['Thread'])

        # Adding unique constraint on 'Thread', fields ['site', 'url']
        db.create_unique(u'comments_thread', ['site_id', 'url'])

        # Adding M2M table for field liked_by on 'Thread'
        db.create_table(u'comments_thread_liked_by', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('thread', models.ForeignKey(orm[u'comments.thread'], null=False)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False))
        ))
        db.create_unique(u'comments_thread_liked_by', ['thread_id', 'customuser_id'])

        # Adding M2M table for field disliked_by on 'Thread'
        db.create_table(u'comments_thread_disliked_by', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('thread', models.ForeignKey(orm[u'comments.thread'], null=False)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False))
        ))
        db.create_unique(u'comments_thread_disliked_by', ['thread_id', 'customuser_id'])

        # Adding model 'Comment'
        db.create_table(u'comments_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', null=True, to=orm['comments.CustomUser'])),
            ('poster_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['comments.Thread'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('liked_by_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('disliked_by_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('avatar_num', self.gf('django.db.models.fields.IntegerField')(default=6)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ip_address', self.gf('django.db.models.fields.GenericIPAddressField')(max_length=39, null=True)),
        ))
        db.send_create_signal(u'comments', ['Comment'])

        # Adding M2M table for field liked_by on 'Comment'
        db.create_table(u'comments_comment_liked_by', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'comments.comment'], null=False)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False))
        ))
        db.create_unique(u'comments_comment_liked_by', ['comment_id', 'customuser_id'])

        # Adding M2M table for field disliked_by on 'Comment'
        db.create_table(u'comments_comment_disliked_by', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'comments.comment'], null=False)),
            ('customuser', models.ForeignKey(orm[u'comments.customuser'], null=False))
        ))
        db.create_unique(u'comments_comment_disliked_by', ['comment_id', 'customuser_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Thread', fields ['site', 'url']
        db.delete_unique(u'comments_thread', ['site_id', 'url'])

        # Deleting model 'CustomUser'
        db.delete_table(u'comments_customuser')

        # Removing M2M table for field groups on 'CustomUser'
        db.delete_table('comments_customuser_groups')

        # Removing M2M table for field user_permissions on 'CustomUser'
        db.delete_table('comments_customuser_user_permissions')

        # Deleting model 'Site'
        db.delete_table(u'comments_site')

        # Deleting model 'Thread'
        db.delete_table(u'comments_thread')

        # Removing M2M table for field liked_by on 'Thread'
        db.delete_table('comments_thread_liked_by')

        # Removing M2M table for field disliked_by on 'Thread'
        db.delete_table('comments_thread_disliked_by')

        # Deleting model 'Comment'
        db.delete_table(u'comments_comment')

        # Removing M2M table for field liked_by on 'Comment'
        db.delete_table('comments_comment_liked_by')

        # Removing M2M table for field disliked_by on 'Comment'
        db.delete_table('comments_comment_disliked_by')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'comments.comment': {
            'Meta': {'ordering': "['created']", 'object_name': 'Comment'},
            'avatar_num': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disliked_by': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'disliked_comments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['comments.CustomUser']"}),
            'disliked_by_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True'}),
            'liked_by': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'liked_comments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['comments.CustomUser']"}),
            'liked_by_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'poster_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['comments.Thread']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'null': 'True', 'to': u"orm['comments.CustomUser']"})
        },
        u'comments.customuser': {
            'Meta': {'object_name': 'CustomUser'},
            'avatar_num': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'comments.site': {
            'Meta': {'object_name': 'Site'},
            'anonymous_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rs_customer_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'comments.thread': {
            'Meta': {'unique_together': "(('site', 'url'),)", 'object_name': 'Thread'},
            'allow_comments': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disliked_by': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'disliked_threads'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['comments.CustomUser']"}),
            'disliked_by_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'liked_by': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'liked_threads'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['comments.CustomUser']"}),
            'liked_by_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'threads'", 'to': u"orm['comments.Site']"}),
            'titles': ('jsonfield.fields.JSONField', [], {'default': "{'page_title': '', 'h1_title': '', 'selector_title': ''}"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['comments']