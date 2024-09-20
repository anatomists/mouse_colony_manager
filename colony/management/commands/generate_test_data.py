from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from colony.models import Rack, Cage, Mouse, Strain
import random

class Command(BaseCommand):
    help = 'Generates test data for the colony management system'

    def handle(self, *args, **kwargs):
        self.generate_racks()
        self.generate_cages()
        self.generate_strains()
        self.generate_mice()

    def generate_racks(self):
        Rack.objects.all().delete()
        # Room 1
        for i in range(3):
            Rack.objects.create(number=f"1L{i+1}", room=1, position=i+1, side='L')
            Rack.objects.create(number=f"1R{i+1}", room=1, position=i+1, side='R')
        # Room 2
        for i in range(4):
            Rack.objects.create(number=f"2L{i+1}", room=2, position=i+1, side='L')
        Rack.objects.create(number="2R1", room=2, position=1, side='R', is_one_sided=True)

    def generate_cages(self):
        Cage.objects.all().delete()
        racks = Rack.objects.all()
        for rack in racks:
            for i in range(140):
                Cage.objects.create(
                    given_number=i + 1,
                    cage_number=f"{rack.number}-{i+1}",
                    rack=rack,
                    room=rack.room,
                    position=i+1
                )

    def generate_strains(self):
        Strain.objects.all().delete()
        strains = ["C57BL/6", "BALB/c", "CD-1", "129S", "FVB"]
        for strain in strains:
            Strain.objects.create(name=strain)

    def generate_mice(self):
        Mouse.objects.all().delete()
        cages = Cage.objects.all()
        strains = Strain.objects.all()
        for cage in cages:
            for _ in range(random.randint(0, 5)):
                Mouse.objects.create(
                    number_in_strain=random.randint(1, 1000),
                    strain=random.choice(strains),
                    sex=random.choice(['M', 'F']),
                    dob=timezone.now() - timedelta(days=random.randint(30, 365)),
                    ear_id=f"{cage.cage_number}-{random.randint(1, 99)}",
                    cage=cage
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated test data'))
