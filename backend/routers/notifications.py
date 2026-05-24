"""Notification router handling CRUD operations for user notifications."""

import os

from fastapi import APIRouter, Depends, Response

from dependencies import get_current_user
from models import (
    Notification,
    NotificationResponse,
    NotificationsListResponse,
    User,
)
from services.notification_service import NotificationService
from services.reminder_checker import check_user
from store import JSONStore

# Initialize notification store and service
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
notification_store = JSONStore(os.path.join(DATA_DIR, "notifications.json"))
notification_service = NotificationService(notification_store)

# Also need access to todo_store for reading user's todos during GET
todo_store = JSONStore(os.path.join(DATA_DIR, "todos.json"))

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
) -> NotificationsListResponse:
    """Get notifications for the authenticated user.

    Calls reminder_checker.check_user() to detect new notifications,
    creates any new notifications, then returns the full list with unread count.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        NotificationsListResponse with notifications list and unread_count.
    """
    # 1. Read user's todos from todo_store
    all_todos = todo_store.read_all()
    user_todos = [t for t in all_todos if t.get("user_id") == current_user.id]

    # 2. Read user's existing notifications from notification_store
    all_notifications = notification_store.read_all()
    user_notifications = [n for n in all_notifications if n.get("user_id") == current_user.id]

    # 3. Call reminder_checker.check_user() to detect new notifications
    new_notification_tuples = check_user(
        user_id=current_user.id,
        todos=user_todos,
        existing_notifications=user_notifications,
    )

    # 4. Create any new notifications
    for todo_id, notification_type, message in new_notification_tuples:
        notification_service.create(
            user_id=current_user.id,
            todo_id=todo_id,
            notification_type=notification_type,
            message=message,
        )

    # 5. Get the full list of notifications for the user
    notifications = notification_service.list_notifications(current_user.id)

    # 6. Get unread count
    unread_count = notification_service.get_unread_count(current_user.id)

    # 7. Return response
    return NotificationsListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                todo_id=n.todo_id,
                type=n.type,
                message=n.message,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        unread_count=unread_count,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """Mark a specific notification as read.

    Args:
        notification_id: The notification's ID to mark as read.
        current_user: The authenticated user (injected by dependency).

    Returns:
        The updated notification.
    """
    notification = notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )

    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        todo_id=notification.todo_id,
        type=notification.type,
        message=notification.message,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark all notifications as read for the authenticated user.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        Dict with marked_count indicating how many were marked.
    """
    count = notification_service.mark_all_as_read(current_user.id)
    return {"marked_count": count}


@router.delete("", status_code=204)
async def delete_all_notifications(
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete all notifications for the authenticated user.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        204 No Content response on success.
    """
    notification_service.delete_all(current_user.id)
    return Response(status_code=204)
