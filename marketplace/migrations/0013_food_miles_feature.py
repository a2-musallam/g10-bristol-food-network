# Generated migration for food miles feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),  # Update this to match your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='postcode',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='farm_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='farm_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='total_food_miles',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Total food miles for all items in this order', max_digits=10),
        ),
        migrations.CreateModel(
            name='FoodMiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_postcode', models.CharField(max_length=10)),
                ('distance_km', models.DecimalField(decimal_places=2, help_text='Distance in kilometers from farm to customer', max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='food_miles_records', to='marketplace.user')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='food_miles_records', to='marketplace.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='food_miles_records', to='marketplace.product')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
