import pandas as pd
from django.db.models import Sum
from sklearn.linear_model import LinearRegression

from attendance.views import calculate_attendance_percentage
from marks.models import Marks
from students.models import Student


def _get_student_features(student):
    attendance_pct = calculate_attendance_percentage(student)

    internal = Marks.objects.filter(
        student=student,
        exam_type=Marks.EXAM_INTERNAL,
    ).aggregate(total=Sum('marks'), max_total=Sum('max_marks'))
    internal_pct = 0
    if internal['max_total']:
        internal_pct = (internal['total'] / internal['max_total']) * 100

    assignment = Marks.objects.filter(
        student=student,
        exam_type=Marks.EXAM_ASSIGNMENT,
    ).aggregate(total=Sum('marks'), max_total=Sum('max_marks'))
    assignment_pct = 0
    if assignment['max_total']:
        assignment_pct = (assignment['total'] / assignment['max_total']) * 100

    final = Marks.objects.filter(
        student=student,
        exam_type=Marks.EXAM_FINAL,
    ).aggregate(total=Sum('marks'), max_total=Sum('max_marks'))
    final_pct = None
    if final['max_total']:
        final_pct = (final['total'] / final['max_total']) * 100

    return {
        'attendance_pct': attendance_pct,
        'internal_pct': internal_pct,
        'assignment_pct': assignment_pct,
        'final_pct': final_pct,
    }


def train_model():
    rows = []
    for student in Student.objects.all():
        features = _get_student_features(student)
        if features['final_pct'] is not None:
            rows.append({
                'attendance_pct': features['attendance_pct'],
                'internal_pct': features['internal_pct'],
                'assignment_pct': features['assignment_pct'],
                'final_pct': features['final_pct'],
            })

    if len(rows) < 2:
        return None, None

    df = pd.DataFrame(rows)
    X = df[['attendance_pct', 'internal_pct', 'assignment_pct']]
    y = df['final_pct']
    model = LinearRegression()
    model.fit(X, y)
    return model, df


def predict_final_score(student):
    features = _get_student_features(student)
    model, _ = train_model()

    if model is None:
        weighted = (
            features['attendance_pct'] * 0.2
            + features['internal_pct'] * 0.4
            + features['assignment_pct'] * 0.4
        )
        return round(min(max(weighted, 0), 100), 2)

    X = pd.DataFrame([{
        'attendance_pct': features['attendance_pct'],
        'internal_pct': features['internal_pct'],
        'assignment_pct': features['assignment_pct'],
    }])
    prediction = model.predict(X)[0]
    return round(min(max(prediction, 0), 100), 2)
