from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Strain(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    breeding_scheme = models.TextField()
    primers = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_strains')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Rack(models.Model):
    SIDE_CHOICES = [
        ('L', 'Left'),
        ('R', 'Right'),
    ]
    number = models.CharField(max_length=50)
    room = models.IntegerField()
    position = models.IntegerField(default=0)
    side = models.CharField(max_length=1, choices=SIDE_CHOICES)  # Now non-nullable
    is_rotated = models.BooleanField(default=False)
    is_one_sided = models.BooleanField(default=False)

    def __str__(self):
        return f"Rack {self.number} in Room {self.room}"


class Cage(models.Model):
    given_number = models.CharField(max_length=10, null=True, blank=True)
    cage_number = models.CharField(max_length=50, unique=True)
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='cages')
    room = models.CharField(max_length=50)
    position = models.IntegerField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cages')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Cage {self.cage_number}"

class Mouse(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    number_in_strain = models.IntegerField()
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    dob = models.DateField()
    weaned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='offspring')
    ear_id = models.CharField(max_length=50)
    genotype1 = models.CharField(max_length=50, blank=True)
    genotype2 = models.CharField(max_length=50, blank=True)
    genotype3 = models.CharField(max_length=50, blank=True)
    genotype4 = models.CharField(max_length=50, blank=True)
    pregnant = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    cage = models.ForeignKey(Cage, on_delete=models.SET_NULL, null=True, related_name='mice')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_mice')
    created_at = models.DateTimeField(default=timezone.now)
    is_sacrificed = models.BooleanField(default=False)

    def __str__(self):
        return f"Mouse {self.number_in_strain} ({self.strain})"

