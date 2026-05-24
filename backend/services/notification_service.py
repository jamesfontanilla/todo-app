"""Notification service handling CRUD operations scoped to authenticated users."""

import uuid
from datetime import datetime, timezone

from exceptions import NotFoundError
from models import Notification
from store import JSONStore


class NotificationService:
    """Handles CRUD operations on notifications scoped to the authenticated user."""

    def __init__(self, notification_store: JSONStore):
        """Initialize with notification store.

        Args:
            notification_store: JSONStore instance for notification persistence.
        """
        self.notification_store = notification_store

    def create(self, user_id: str, todo_id: str, notification_type: str, message: str) -> Notification:
        """Create a new notification.

        Generates UUID, sets created_at to now, is_read=False.
        Persists to notifications.json via JSONStore.

        Args:
            user_id: UUID4 string of the notification owner.
            todo_id: UUID4 string of the related todo.
            notification_type: "reminder" or "overdue".
            message: Human-readable notification message.

        Returns:
            Notification Pydantic model instance.
        """
        notification_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "todo_id": todo_id,
            "type": notification_type,
            "message": message,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.notification_store.add(notification_data)

        return Notification(**notification_data)

    def list_notifications(self, user_id: str, limit: int = 20) -> list[Notification]:
        """Read all notifications for user_id.

        Sorts by created_at descending (most recent first).
        Returns up to `limit` notifications.

        Args:
            user_id: The authenticated user's ID.
            limit: Maximum number of notifications to return.

        Returns:
            A list of Notification objects sorted by created_at descending.
        """
        all_records = self.notification_store.read_all()
        user_notifications = [r for r in all_records if r.get("user_id") == user_id]

        # Sort by created_at descending (most recent first)
        user_notifications.sort(key=lambda r: r.get("created_at", ""), reverse=True)

        # Apply limit
        user_notifications = user_notifications[:limit]

        return [Notification(**r) for r in user_notifications]

    def get_unread_count(self, user_id: str) -> int:
        """Count notifications where user_id matches and is_read=False.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Integer count of unread notifications.
        """
        all_records = self.notification_store.read_all()
        return sum(
            1 for r in all_records
            if r.get("user_id") == user_id and r.get("is_read") is False
        )

    def mark_as_read(self, user_id: str, notification_id: str) -> Notification:
        """Mark a notification as read.

        Finds notification by id, verifies user_id ownership,
        sets is_read=True, and persists change.

        Args:
            user_id: The authenticated user's ID.
            notification_id: The notification's ID to mark as read.

        Returns:
            The updated Notification object.

        Raises:
            NotFoundError: If notification is not found or not owned by user.
        """
        record = self.notification_store.find_by_id(notification_id)

        if not record or record.get("user_id") != user_id:
            raise NotFoundError("Notification not found")

        updated_record = self.notification_store.update(notification_id, {"is_read": True})

        if not updated_record:
            raise NotFoundError("Notification not found")

        return Notification(**updated_record)

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for user as read.

        Finds all notifications for user_id where is_read=False,
        sets is_read=True on all, and persists changes.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Count of notifications marked as read.
        """
        all_records = self.notification_store.read_all()
        count = 0

        for record in all_records:
            if record.get("user_id") == user_id and record.get("is_read") is False:
                record["is_read"] = True
                count += 1

        if count > 0:
            self.notification_store.write_all(all_records)

        return count

    def delete_all(self, user_id: str) -> int:
        """Remove all notifications for user_id from store.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            Count of notifications deleted.
        """
        all_records = self.notification_store.read_all()
        original_count = len([r for r in all_records if r.get("user_id") == user_id])

        remaining = [r for r in all_records if r.get("user_id") != user_id]
        self.notification_store.write_all(remaining)

        return original_count

    def exists(self, user_id: str, todo_id: str, notification_type: str) -> bool:
        """Check if a notification already exists for deduplication.

        Args:
            user_id: UUID4 string of the notification owner.
            todo_id: UUID4 string of the related todo.
            notification_type: "reminder" or "overdue".

        Returns:
            True if a notification with this (user_id, todo_id, type) exists.
        """
        all_records = self.notification_store.read_all()
        return any(
            r.get("user_id") == user_id
            and r.get("todo_id") == todo_id
            and r.get("type") == notification_type
            for r in all_records
        )
