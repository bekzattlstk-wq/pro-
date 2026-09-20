from .models import Notification


def unread_notifications(request):
    """Счётчик непрочитанных уведомлений для бейджа в меню."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'unread_notifications_count': 0}
    return {
        'unread_notifications_count': Notification.objects.filter(
            user=user, is_read=False
        ).count()
    }
