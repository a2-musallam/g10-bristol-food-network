# Generated migration for organic certification feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0017_remove_notification_producer_notification_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_organic',
            field=models.BooleanField(default=False, help_text='Is this product certified organic?'),
        ),
        migrations.AddField(
            model_name='product',
            name='organic_certification_number',
            field=models.CharField(blank=True, help_text='Certification number for audit trail', max_length=100, null=True),
        ),
    ]
