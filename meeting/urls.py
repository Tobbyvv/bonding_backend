from .views import MeetingViewSet, ParticipantViewset, ConfirmedTimesViewset
from rest_framework.routers import SimpleRouter

router = SimpleRouter(trailing_slash=False)
router.register(r"meetings", MeetingViewSet, basename="meeting")
router.register(r"participants", ParticipantViewset, basename="participant")
router.register(r"confirmed-times", ConfirmedTimesViewset, basename="confirmed_time")
urlpatterns = router.urls
