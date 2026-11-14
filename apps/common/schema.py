from rest_framework import serializers


class InstructorDailyCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class InstructorDailyEarningSerializer(serializers.Serializer):
    date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class InstructorDashboardSerializer(serializers.Serializer):
    instructor = serializers.DictField(child=serializers.CharField())
    metrics = serializers.DictField()
    enrollment_trend = InstructorDailyCountSerializer(many=True)
    course_earnings = InstructorDailyEarningSerializer(many=True)
    top_courses = serializers.ListField(child=serializers.DictField())
    recent_ratings = serializers.ListField(child=serializers.DictField())


class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_instructors = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    total_revenue = serializers.FloatField()
    current_earnings = serializers.FloatField()
    total_earnings = serializers.FloatField()


class DailyCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class DashboardChartsSerializer(serializers.Serializer):
    orders = DailyCountSerializer(many=True)
    users = DailyCountSerializer(many=True)
