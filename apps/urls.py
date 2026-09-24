from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.auth.urls", namespace="auth")),
    path("users/", include("apps.users.urls", namespace="user")),
    path("category/", include("apps.category.urls", namespace="category")),
    path("bank/", include("apps.bank.urls", namespace="bank")),
    path("localization/", include("apps.localization.urls", namespace="localization")),
    path("wallet/", include("apps.wallet.urls", namespace="wallet")),
    path("course/", include("apps.course.urls", namespace="course")),
    path("section/", include("apps.section.urls", namespace="section")),
    path("lecture/", include("apps.lecture.urls", namespace="lecture")),
]
