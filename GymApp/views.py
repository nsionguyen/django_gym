from rest_framework import viewsets, generics, permissions, parsers, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from . import serializers
from .models import User, MemberProfile, Package, MemberPackage, Schedule, Review, Progress, Payment, Notification, Chat, Message, PtProfile,Comment
from .serializers import UserSerializer, MemberProfileSerializer, ScheduleSerializer, PackageSerializer, MemberPackageSerializer
from .serializers import ReviewSerializer, ProgressSerializer, PaymentSerializer, NotificationSerializer, ChatSerializer, MessageSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from GymApp import perms
class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    @action(methods=['get', 'patch'], url_path="current-user", detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        if request.method.__eq__("PATCH"):
            u = request.user

            for key in request.data:
                if key in ['first_name', 'last_name']:
                    setattr(u, key, request.data[key])
                elif key.__eq__('password'):
                    u.set_password(request.data[key])

            u.save()
            return Response(serializers.UserSerializer(u).data)
        else:
            return Response(serializers.UserSerializer(request.user).data)

class MemberProfileViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = MemberProfile.objects.all()
    serializer_class = MemberProfileSerializer


    # @action(methods=['post'], detail=True, url_path='member-profiles')
    # def get_comments(self, request, pk):
    #     if request.method.__eq__('POST'):
    #         s = serializers.MemberProfileSerializer(data={
    #             'height': request.data.get('height'),
    #             'weight': request.data.get('weight'),
    #             'goal': request.data.get('goal'),
    #             'user_id': request.data.get('user_id')
    #         })
    #         s.is_valid(raise_exception=True)
    #         c = s.save()
    #         return Response(serializers.MemberProfileSerializer(c).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        # Chỉ admin hoặc chính user mới thấy profile
        if self.request.user.is_superuser:
            return MemberProfile.objects.all()
        return MemberProfile.objects.filter(user=self.request.user)


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class MemberPackageViewSet(viewsets.ModelViewSet):
    queryset = MemberPackage.objects.all()
    serializer_class = MemberPackageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return MemberPackage.objects.all()
        return MemberPackage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Schedule.objects.all()
        elif self.request.user.role == 'pt':
            return Schedule.objects.filter(pt=self.request.user)
        return Schedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role == 'pt':
            serializer.save(pt=self.request.user)
        else:
            serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if self.request.user.role == 'pt':
            serializer.save()
        elif self.request.user == instance.user:
            serializer.save(status='pending')  # Hội viên cập nhật thì status về pending
        else:
            raise ValidationError("You do not have permission to update this schedule.")

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.filter()
    serializer_class = serializers.ReviewSerializer





    def get_queryset(self):
        if self.request.user.is_superuser:
            return Review.objects.all()
        elif self.request.user.role == 'pt':
            return Review.objects.filter(pt=self.request.user)
        return Review.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role != 'member':
            raise ValidationError("Only members can create reviews.")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if self.request.user != instance.user:
            raise ValidationError("You can only update your own reviews.")
        serializer.save()

class ProgressViewSet(viewsets.ModelViewSet):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Progress.objects.all()
        elif self.request.user.role == 'pt':
            return Progress.objects.filter(pt=self.request.user)
        return Progress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role != 'pt':
            raise ValidationError("Only PTs can create progress records.")
        serializer.save(pt=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if self.request.user != instance.pt:
            raise ValidationError("You can only update progress records you created.")
        serializer.save()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Chỉ hiển thị notification của người dùng hiện tại (trừ admin)
        user = self.request.user
        if user.is_superuser:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        chat = self.get_object()
        messages = chat.messages.all().order_by('-timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class PtProfileViewSet(viewsets.ViewSet,generics.ListAPIView, generics.RetrieveAPIView):
    queryset = PtProfile.objects.filter()
    serializer_class = serializers.PtProfileSerializer

    def get_permissions(self):
        if self.action in ['get_reviews'] and self.request.method.__eq__('POST'):
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]



    @action(methods=['get', 'post'], detail=True, url_path='comments')
    def get_comments(self, request, pk):
        if request.method.__eq__('POST'):
            u = serializers.CommentSerializer(data={
                'content': request.data.get('content'),
                'rating' : request.data.get('rating'),
                'user': request.user.pk,
                'pt_profile': pk
            })
            u.is_valid(raise_exception=True)
            c = u.save()
            return Response(serializers.CommentSerializer(c).data, status=status.HTTP_201_CREATED)
        else:
            comments = self.get_object().comment_set.select_related('user').filter(active=True)
            return Response(serializers.CommentSerializer(comments, many=True).data, status=status.HTTP_200_OK)
class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.filter(active=True)
    serializer_class = serializers.CommentSerializer
    permission_classes = [perms.IsCommentOwner]