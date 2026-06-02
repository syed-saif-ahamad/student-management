import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add audit tracking columns to Marks
        migrations.AddField(
            model_name='marks',
            name='created_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='marks_created',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='marks',
            name='updated_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='marks_updated',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='marks',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='marks',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Create the audit log table
        migrations.CreateModel(
            name='MarksAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[('CREATE', 'Created'), ('UPDATE', 'Updated'), ('DELETE', 'Deleted')],
                    max_length=10,
                )),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('student_name', models.CharField(max_length=150)),
                ('roll_no', models.CharField(max_length=20)),
                ('subject', models.CharField(max_length=100)),
                ('exam_type', models.CharField(max_length=50)),
                ('marks_value', models.IntegerField(blank=True, null=True)),
                ('max_marks_value', models.IntegerField(blank=True, null=True)),
                ('exam_date', models.DateField(blank=True, null=True)),
                ('changes', models.TextField(blank=True)),
                ('marks', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to='marks.marks',
                )),
                ('performed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='marks_audit_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Marks Audit Log',
                'verbose_name_plural': 'Marks Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
    ]
