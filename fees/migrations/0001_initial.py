import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('students', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('category', models.CharField(
                    choices=[
                        ('Tuition', 'Tuition Fee'),
                        ('University', 'University Fee'),
                        ('Transport', 'Bus / Transport Fee'),
                        ('Examination', 'Examination Fee'),
                        ('Library', 'Library Fee'),
                        ('Laboratory', 'Laboratory Fee'),
                        ('Hostel', 'Hostel Fee'),
                        ('Miscellaneous', 'Miscellaneous'),
                    ],
                    max_length=20,
                )),
                ('period', models.CharField(
                    choices=[('Sem 1', 'Semester 1'), ('Sem 2', 'Semester 2'), ('Annual', 'Annual')],
                    default='Annual',
                    max_length=10,
                )),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('academic_year', models.CharField(default='2025-26', max_length=10)),
                ('due_date', models.DateField()),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='fee_structures_created',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Fee Structure', 'ordering': ['department', 'year', 'category']},
        ),
        migrations.CreateModel(
            name='StudentFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('due_date', models.DateField()),
                ('status', models.CharField(
                    choices=[
                        ('Paid', 'Paid'),
                        ('Partially Paid', 'Partially Paid'),
                        ('Pending', 'Pending'),
                        ('Waived', 'Waived'),
                    ],
                    default='Pending',
                    max_length=15,
                )),
                ('remarks', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('fee_structure', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_fees',
                    to='fees.feestructure',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fee_records',
                    to='students.student',
                )),
                ('updated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='fees_updated',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Student Fee', 'ordering': ['due_date', 'fee_structure__category']},
        ),
        migrations.CreateModel(
            name='FeePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateField(default=django.utils.timezone.localdate)),
                ('mode', models.CharField(
                    choices=[
                        ('Cash', 'Cash'),
                        ('Online', 'Online Transfer'),
                        ('Demand Draft', 'Demand Draft'),
                        ('Cheque', 'Cheque'),
                        ('UPI', 'UPI'),
                    ],
                    default='Cash',
                    max_length=15,
                )),
                ('reference_no', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('received_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='payments_received',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('student_fee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payments',
                    to='fees.studentfee',
                )),
            ],
            options={'verbose_name': 'Fee Payment', 'ordering': ['-payment_date']},
        ),
        migrations.AddConstraint(
            model_name='feestructure',
            constraint=models.UniqueConstraint(
                fields=['department', 'year', 'category', 'period', 'academic_year'],
                name='unique_fee_structure',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentfee',
            constraint=models.UniqueConstraint(
                fields=['student', 'fee_structure'],
                name='unique_student_fee',
            ),
        ),
    ]
