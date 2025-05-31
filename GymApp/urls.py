from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MemberProfileViewSet, ScheduleViewSet, ReviewViewSet, ProgressViewSet, PaymentViewSet
from .views import PackageViewSet, MemberPackageViewSet, NotificationViewSet, ChatViewSet, MessageViewSet
from django.urls import path, include
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'member-profiles', MemberProfileViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'progress', ProgressViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'packages', PackageViewSet)
router.register(r'member-packages', MemberPackageViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'chats', ChatViewSet)
router.register(r'messages', MessageViewSet)
urlpatterns =  [
    path('', include(router.urls)),
]

