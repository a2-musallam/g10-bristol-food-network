from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies =[
        ('marketplace', '0009_order_status_note_order_updated_at_and_more'),
    ]

    operations =[
        migrations.AddField(
            model_name='order',
            name='special_instructions',
            field=models.TextField(blank=True, null=True),
        ),
    ]
