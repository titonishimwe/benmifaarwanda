from __future__ import annotations

import random
from dataclasses import dataclass

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import PDFGuide, ProfessionalSupportService, SiteSettings, Slide, Video
from users.models import Profile
from django.contrib.auth.models import User


_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd5\x1a\x9b"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _tiny_png_file(name: str) -> ContentFile:
    f = ContentFile(_TINY_PNG)
    f.name = name
    return f


def _text_file(name: str, text: str) -> ContentFile:
    f = ContentFile(text.encode("utf-8"))
    f.name = name
    return f


def _fake_youtube_id() -> str:
    # 11-char IDs (public, stable examples)
    ids = [
        "dQw4w9WgXcQ",
        "3JZ_D3ELwOQ",
        "M7lc1UVf-VE",
        "hTWKbfoikeg",
        "e-ORhEE9VVg",
        "L_jWHffIx5E",
        "kJQP7kiw5Fk",
        "YQHsXMglC9A",
    ]
    return random.choice(ids)


@dataclass(frozen=True)
class _ServiceSeed:
    title: str
    tag: str
    icon: str


class Command(BaseCommand):
    help = "Populate demo/dummy data for local testing."

    def add_arguments(self, parser):
        parser.add_argument("--videos", type=int, default=12)
        parser.add_argument("--pdfs", type=int, default=8)
        parser.add_argument("--slides", type=int, default=8)
        parser.add_argument("--services", type=int, default=6)
        parser.add_argument("--users", type=int, default=8)
        parser.add_argument("--featured-videos", type=int, default=6)
        parser.add_argument("--featured-services", type=int, default=3)
        parser.add_argument(
            "--admin-username",
            type=str,
            default="tite",
            help="Demo admin username (default: tite). Skipped if user already exists.",
        )
        parser.add_argument("--admin-password", type=str, default="admin12345")
        parser.add_argument(
            "--create-admin",
            action="store_true",
            help="Create the admin user if missing. Does not change existing users' roles.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(7)

        if opts["create_admin"]:
            admin_user, admin_created = User.objects.get_or_create(
                username=opts["admin_username"],
                defaults={
                    "email": "admin@be2sahobe.local",
                    "is_staff": True,
                    "is_superuser": True,
                    "first_name": "Admin",
                    "last_name": "User",
                    "is_active": True,
                },
            )
            if admin_created:
                admin_user.set_password(opts["admin_password"])
                admin_user.save(update_fields=["password"])
            Profile.objects.get_or_create(user=admin_user)

        SiteSettings.load()

        # Members
        created_members = 0
        for i in range(1, int(opts["users"]) + 1):
            username = f"member{i:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": f"Member{i}",
                    "last_name": "Demo",
                    "is_active": True,
                },
            )
            if created:
                user.set_password("member12345")
                user.save(update_fields=["password"])
                created_members += 1
            Profile.objects.get_or_create(user=user)

        # Videos
        video_categories = [c for c, _ in Video.CATEGORY_CHOICES]
        created_videos = 0
        now = timezone.now()
        for i in range(1, int(opts["videos"]) + 1):
            title = f"Demo Video {i:02d}"
            defaults = {
                "youtube_url": _fake_youtube_id(),
                "category": random.choice(video_categories),
                "description": "Demo training content for the BE2SAHOBE learning library.",
                "instructor": random.choice(["BE2SAHOBE Trainer", "Coach Aline", "Coach Eric", "Mentor Grace"]),
                "duration": random.choice(["8 mins", "12 mins", "15 mins", "22 mins", "30 mins"]),
                "created_at": now,
            }
            obj, created = Video.objects.get_or_create(title=title, defaults=defaults)
            if created:
                created_videos += 1

        # Feature some videos for homepage section
        featured_count = int(opts["featured_videos"])
        videos = list(Video.objects.order_by("created_at").values_list("id", flat=True))
        for order, vid in enumerate(videos[:featured_count]):
            Video.objects.filter(id=vid).update(show_on_homepage=True, homepage_order=order)

        # PDFs (requires thumbnail + file)
        pdf_categories = [c for c, _ in PDFGuide.CATEGORY_CHOICES]
        created_pdfs = 0
        for i in range(1, int(opts["pdfs"]) + 1):
            title = f"Demo PDF Guide {i:02d}"
            obj, created = PDFGuide.objects.get_or_create(
                title=title,
                defaults={
                    "category": random.choice(pdf_categories),
                    "author": random.choice(["BE2SAHOBE Team", "MIFAA/NGoP", "Community Facilitator"]),
                    "description": "Demo PDF guide for offline learning and reference.",
                    "pages": random.randint(3, 28),
                },
            )
            if created:
                obj.thumbnail.save(f"pdf_{i:02d}.png", _tiny_png_file(f"pdf_{i:02d}.png"), save=False)
                obj.pdf_file.save(f"guide_{i:02d}.pdf", _text_file(f"guide_{i:02d}.pdf", "Demo PDF content."), save=False)
                obj.save()
                created_pdfs += 1

        # Slides (requires thumbnail + slide_file)
        slide_categories = [c for c, _ in Slide.CATEGORY_CHOICES]
        created_slides = 0
        for i in range(1, int(opts["slides"]) + 1):
            title = f"Demo Slides {i:02d}"
            obj, created = Slide.objects.get_or_create(
                title=title,
                defaults={
                    "category": random.choice(slide_categories),
                    "presenter": random.choice(["BE2SAHOBE Team", "Workshop Lead", "Trainer Jane"]),
                    "description": "Demo slide deck for workshops and classes.",
                    "slides_count": random.randint(8, 45),
                },
            )
            if created:
                obj.thumbnail.save(f"slides_{i:02d}.png", _tiny_png_file(f"slides_{i:02d}.png"), save=False)
                obj.slide_file.save(
                    f"slides_{i:02d}.pdf",
                    _text_file(f"slides_{i:02d}.pdf", "Demo slides content."),
                    save=False,
                )
                obj.save()
                created_slides += 1

        # Services
        service_seeds = [
            _ServiceSeed("Project Design & M&E", "Data-Driven", "bi-clipboard-data"),
            _ServiceSeed("Grant Writing & Proposals", "Funding", "bi-file-earmark-text"),
            _ServiceSeed("Business Strategy", "Growth", "bi-graph-up-arrow"),
            _ServiceSeed("Financial Coaching", "Planning", "bi-cash-coin"),
            _ServiceSeed("Training & Facilitation", "Workshops", "bi-easel2"),
            _ServiceSeed("Branding & Communication", "Professional", "bi-megaphone"),
            _ServiceSeed("Community Development", "Impact", "bi-people"),
        ]
        created_services = 0
        for i in range(1, int(opts["services"]) + 1):
            seed = service_seeds[(i - 1) % len(service_seeds)]
            title = seed.title if i <= len(service_seeds) else f"{seed.title} {i:02d}"
            obj, created = ProfessionalSupportService.objects.get_or_create(
                title=title,
                defaults={
                    "description": "Professional framework design, monitoring, and evaluation for community development and social impact projects.",
                    "image_url": "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=1200",
                    "image_alt": title,
                    "tag_label": seed.tag,
                    "icon_class": seed.icon,
                    "email": "info@be2sahobe.rw",
                    "order": i,
                },
            )
            if created:
                created_services += 1

        # Feature some services on homepage
        featured_services_count = int(opts["featured_services"])
        service_ids = list(
            ProfessionalSupportService.objects.order_by("order", "created_at").values_list("id", flat=True)
        )
        for order, sid in enumerate(service_ids[:featured_services_count]):
            ProfessionalSupportService.objects.filter(id=sid).update(show_on_homepage=True, homepage_order=order)

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Created: members={created_members}, videos={created_videos}, pdfs={created_pdfs}, slides={created_slides}, services={created_services}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Admin login: username={admin_user.username} password={opts['admin_password']}"
            )
        )

