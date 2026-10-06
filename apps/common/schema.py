from rest_framework import serializers


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
