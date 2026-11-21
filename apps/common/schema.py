from rest_framework import serializers


class AdminDashboardMetricsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_learners = serializers.IntegerField()
    instructors = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    published_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    enrollments_30d = serializers.IntegerField()
    gross_revenue = serializers.CharField()
    orders_30d = serializers.IntegerField()


class AdminDashboardTrendCountSerializer(serializers.Serializer):
    date = serializers.CharField()
    count = serializers.IntegerField()


class AdminDashboardTrendRevenueSerializer(serializers.Serializer):
    date = serializers.CharField()
    amount = serializers.CharField()


class AdminDashboardCourseStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class AdminDashboardRecentOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_name = serializers.CharField()
    course_title = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    is_free = serializers.BooleanField()
    total_paid = serializers.CharField()
    created_at = serializers.DateTimeField()


class AdminDashboardSerializer(serializers.Serializer):
    metrics = AdminDashboardMetricsSerializer()
    currency = serializers.CharField()
    as_of = serializers.DateTimeField()
    enrollment_trend = AdminDashboardTrendCountSerializer(many=True)
    revenue_trend = AdminDashboardTrendRevenueSerializer(many=True)
    course_status_counts = AdminDashboardCourseStatusSerializer(many=True)
    recent_orders = AdminDashboardRecentOrderSerializer(many=True)


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
