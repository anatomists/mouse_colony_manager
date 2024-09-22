from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from colony.models import Strain, Cage, Mouse, Rack
from .serializers import UserSerializer, StrainSerializer, CageSerializer, MouseSerializer, RackSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add extra responses here
        data['user'] = UserSerializer(self.user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            regular_user_group = Group.objects.get(name='Regular User')
            user.groups.add(regular_user_group)
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "User Created Successfully."
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_user_type(self, request, pk=None):
        user = self.get_object()
        user_type = request.data.get('user_type')
        if user_type not in ['admin', 'manager', 'user']:
            return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

        user.groups.clear()
        if user_type == 'admin':
            user.is_superuser = True
        elif user_type == 'manager':
            manager_group = Group.objects.get(name='Mice Colony Manager')
            user.groups.add(manager_group)
        else:
            regular_user_group = Group.objects.get(name='Regular User')
            user.groups.add(regular_user_group)

        user.save()
        return Response({"message": f"User type set to {user_type}"})

    def get_permissions(self):
        if self.action in ['register', 'login', 'logout']:
            return [AllowAny()]
        return [IsAuthenticated()]

class StrainViewSet(viewsets.ModelViewSet):
    queryset = Strain.objects.all()
    serializer_class = StrainSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, created_by=self.request.user)

    def get_queryset(self):
        queryset = Strain.objects.all()
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Mice Colony Manager').exists():
            queryset = Strain.objects.all()
        else:
            queryset = Strain.objects.filter(owner_id=user)
        # if self.request.user.is_authenticated:
        #     queryset = queryset.filter(owner=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        #print('Strains being sent from API:', serializer.data)
        return Response(serializer.data)


class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        #print('Racks being sent from API:', serializer.data)  # Add this line
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        rack = self.get_object()
        rack.is_rotated = not rack.is_rotated
        rack.save()
        return Response({'status': 'rack rotated'})


class CageViewSet(viewsets.ModelViewSet):
    queryset = Cage.objects.all()
    serializer_class = CageSerializer

    @action(detail=False, methods=['post'])
    def move_cage(self, request):
        source_rack_id = request.data.get('source_rack_id')
        source_position = request.data.get('source_position')
        target_rack_id = request.data.get('target_rack_id')
        target_position = request.data.get('target_position')

        try:
            cage = Cage.objects.get(rack_id=source_rack_id, position=source_position)
            cage.rack_id = target_rack_id
            cage.position = target_position
            cage.save()
            return Response({'message': 'Cage moved successfully'}, status=status.HTTP_200_OK)
        except Cage.DoesNotExist:
            return Response({'error': 'Cage not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MouseViewSet(viewsets.ModelViewSet):
    queryset = Mouse.objects.all()
    serializer_class = MouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Mice Colony Manager').exists():
            queryset = Mouse.objects.all()
        else:
            queryset = Mouse.objects.filter(strain__owner=user)

        cage_id = self.request.query_params.get('cage', None)
        if cage_id is not None:
            queryset = queryset.filter(cage_id=cage_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def move_mouse(self, request):
        mouse_id = request.data.get('mouse_id')
        cage_id = request.data.get('cage_id')

        try:
            mouse = Mouse.objects.get(id=mouse_id)
            cage = Cage.objects.get(id=cage_id)
            mouse.cage = cage
            mouse.save()
            return Response({'message': 'Mouse moved successfully'}, status=status.HTTP_200_OK)
        except (Mouse.DoesNotExist, Cage.DoesNotExist):
            return Response({'error': 'Mouse or Cage not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sacrifice(self, request, pk=None):
        mouse = self.get_object()
        mouse.is_sacrificed = True
        mouse.save()
        return Response({"message": "Mouse sacrificed successfully"})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        mouse = self.get_object()
        mouse.is_sacrificed = False
        mouse.save()
        return Response({"message": "Mouse restored successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
