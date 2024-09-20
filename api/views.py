from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "token": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "User Created Successfully."
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "User Logged In Successfully"
            })
        return Response({"message": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def logout(self, request):
        # In token-based auth, the client is responsible for removing the token
        return Response({"message": "User Logged Out Successfully"})

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
        if self.request.user.is_authenticated:
            queryset = queryset.filter(owner=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print('Strains being sent from API:', serializer.data)
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

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        cage = self.get_object()
        new_rack_id = request.data.get('new_rack_id')
        new_position = request.data.get('new_position')

        if new_rack_id and new_position:
            try:
                new_rack = Rack.objects.get(id=new_rack_id)
                cage.rack = new_rack
                cage.position = new_position
                cage.save()
                return Response({'status': 'cage moved'})
            except Rack.DoesNotExist:
                return Response({'error': 'Invalid rack ID'}, status=400)
        else:
            return Response({'error': 'Missing new_rack_id or new_position'}, status=400)


class MouseViewSet(viewsets.ModelViewSet):
    queryset = Mouse.objects.all()
    serializer_class = MouseSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        # print('Mice being sent from API:', serializer.data)  # Add this line
        return Response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        cage_id = self.request.query_params.get('cage', None)
        if cage_id is not None:
            queryset = queryset.filter(cage_id=cage_id)
        return queryset

    @action(detail=False, methods=['post'])
    def move_mice(self, request):
        mouse_ids = request.data.get('mouse_ids', [])
        new_cage_id = request.data.get('new_cage_id')

        if not mouse_ids or not new_cage_id:
            return Response({"error": "Mouse IDs and new cage ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_cage = Cage.objects.get(id=new_cage_id)
            mice = Mouse.objects.filter(id__in=mouse_ids)

            for mouse in mice:
                mouse.cage = new_cage
                mouse.save()

            return Response({"message": "Mice moved successfully"}, status=status.HTTP_200_OK)
        except Cage.DoesNotExist:
            return Response({"error": "New cage not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def sacrifice(self, request, pk=None):
        mouse = self.get_object()
        mouse.is_sacrificed = True
        mouse.save()
        return Response({"message": "Mouse sacrificed successfully"})

    @action(detail=True, methods=['post'])
    def undo_sacrifice(self, request, pk=None):
        mouse = self.get_object()
        mouse.is_sacrificed = False
        mouse.save()
        return Response({"message": "Mouse sacrifice undone successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)