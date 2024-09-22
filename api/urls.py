from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StrainViewSet, CageViewSet, MouseViewSet, RackViewSet, CustomTokenObtainPairView, CustomTokenRefreshView, get_user

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'strains', StrainViewSet)
router.register(r'cages', CageViewSet)
router.register(r'mice', MouseViewSet)
router.register(r'racks', RackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='login'),
    path('logout/', UserViewSet.as_view({'post': 'logout'}), name='logout'),
    path('user/', get_user, name='get_user'),
    path('users/<int:pk>/set_user_type/', UserViewSet.as_view({'post': 'set_user_type'}), name='set_user_type'),
    path('move-cage/', CageViewSet.as_view({'post': 'move_cage'}), name='move-cage'),
]
