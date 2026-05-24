# Unit 1: Notification Backend — Code Summary

## Files Created

| File | Description |
|---|---|
| `backend/services/notification_service.py` | NotificationService class with full CRUD: create, list_notifications, get_unread_count, mark_as_read, mark_all_as_read, delete_all, exists |
| `backend/routers/notifications.py` | FastAPI router with 4 endpoints: GET, PATCH /{id}/read, POST /read-all, DELETE |
| `backend/data/notifications.json` | Empty JSON array for notification persistence |

## Files Modified

| File | Changes |
|---|---|
| `backend/models.py` | Added NotificationType enum, Notification, NotificationResponse, NotificationsListResponse models |
| `backend/main.py` | Imported and registered notifications router; added PATCH to CORS allowed methods |

## API Endpoints Implemented

| Method | Path | Description |
|---|---|---|
| GET | `/api/notifications` | List notifications + trigger reminder detection via check_user() |
| PATCH | `/api/notifications/{id}/read` | Mark single notification as read |
| POST | `/api/notifications/read-all` | Mark all notifications as read |
| DELETE | `/api/notifications` | Delete all user notifications (204 No Content) |

## Integration Points

- **GET /api/notifications** integrates with Unit 2's `reminder_checker.check_user()` to detect and create new notifications on each poll
- **NotificationService.create()** and **NotificationService.exists()** are exposed as internal interfaces for Unit 2 consumption
- CORS middleware updated to allow PATCH method for the mark-as-read endpoint

## Design Patterns Followed

- Same singleton service pattern as TodoService (store injected at module level)
- Same authentication pattern via `get_current_user` dependency
- Same error handling via custom exceptions (NotFoundError)
- Same JSONStore persistence layer
- Same router prefix/tag conventions
