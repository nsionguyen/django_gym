from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, MemberProfile, Schedule, Review, Progress, Payment, Package, MemberPackage, Notification, Chat, ChatParticipant, Message

#AdminUser và MemberProfile
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_staff', 'is_superuser', 'is_active', 'date_joined', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('date_joined',)}),  # Loại bỏ created_at và last_login
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'role'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

    # Đặt role mặc định là member khi tạo user mới
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Khi thêm user mới
            form.base_fields['role'].initial = 'member'  # Mặc định role là member
        return form

class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'height', 'weight', 'bmi', 'updated_at')
    search_fields = ('user__username', 'user__email')
    exclude = ('bmi', 'updated_at')  # Loại bỏ bmi và updated_at khỏi form



    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='member')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(User, UserAdmin)
admin.site.register(MemberProfile, MemberProfileAdmin)

#AdminSchedule
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'pt', 'start_time', 'end_time', 'status', 'note')
    list_filter = ('status', 'pt')
    search_fields = ('user__username', 'pt__username', 'note')
    date_hierarchy = 'start_time'
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'pt':
            return qs.filter(pt=request.user)  # PT chỉ thấy lịch của mình
        return qs

    def get_readonly_fields(self, request, obj=None):
        if request.user.role == 'pt':
            return ['user', 'member_package', 'created_at', 'updated_at']  # PT không sửa các trường này
        return []

    def has_add_permission(self, request):
        return True  # PT có thể tạo lịch mới

    def has_change_permission(self, request, obj=None):
        return True  # PT có thể sửa lịch

    def has_delete_permission(self, request, obj=None):
        if request.user.role == 'pt':
            return False  # PT không được xóa lịch
        return True

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'pt', 'gym_rating', 'pt_rating', 'created_at')
    list_filter = ('gym_rating', 'pt_rating')
    search_fields = ('user__username', 'pt__username', 'comment')
    date_hierarchy = 'created_at'

#
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'pt', 'weight', 'body_fat', 'muscle_mass', 'recorded_at')
    list_filter = ('pt',)
    search_fields = ('user__username', 'pt__username', 'note')
    date_hierarchy = 'recorded_at'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('member_package', 'amount', 'method', 'payment_date', 'status')
    list_filter = ('method', 'status')
    search_fields = ('member_package__user__username', 'member_package__package__name')
    date_hierarchy = 'payment_date'

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'pt_sessions', 'package_type', 'is_active']  # Xóa 'duration'
    list_filter = ['package_type', 'is_active']
    search_fields = ['name']

@admin.register(MemberPackage)
class MemberPackageAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'start_date', 'end_date', 'status']
    list_filter = ['status']
    search_fields = ['user__username', 'package__name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'sent_at', 'is_read')
    list_filter = ('type', 'is_read')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'sent_at'


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('chat_name', 'is_group', 'last_message', 'last_updated')
    list_filter = ('is_group',)
    search_fields = ('chat_name',)

@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'joined_at')
    list_filter = ('chat',)
    search_fields = ('user__username',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender', 'content', 'timestamp')
    list_filter = ('chat', 'sender')
    search_fields = ('content', 'sender__username')
