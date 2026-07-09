from django.shortcuts import render,redirect,get_object_or_404, reverse
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .forms import AdminMemberForm, AdminEditMemberForm
from .models import Profile
from core.forms import SiteSettingsForm, HomepageServiceForm, VideoForm, PDFGuideForm, SlideForm
from core.models import SiteSettings, ProfessionalSupportService, Video, PDFGuide, Slide
from core.homepage import save_homepage_selection


# Create your views here.
def register_view(request):
    """Public registration is disabled — only staff can add members."""
    messages.info(
        request,
        'New accounts are created by an administrator. Please sign in or contact support.',
    )
    return redirect('home')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome {user.username}')
            return redirect(f"{reverse('dashboard')}?tab=profile")
        else:
            messages.error(request, 'Invalid username or password')
            return redirect(f"{reverse('home')}?login=1")

    # Login is handled via the homepage modal
    return redirect(f"{reverse('home')}?login=1")


# LOGOUT
def logout_view(request):
   logout(request)
   messages.success(request,'Successfully logged out')
   return redirect('login')

# USER PROFILE

@login_required
def profile_view(request):
    """
    Redirect to the unified dashboard profile tab.
    """
    return redirect(f"{reverse('dashboard')}?tab=profile")


@login_required
def edit_profile(request):
    if request.method != 'POST':
        return redirect(f"{reverse('dashboard')}?tab=profile")

    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    username = (request.POST.get('username') or user.username).strip()
    email = (request.POST.get('email') or '').strip()
    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()

    if User.objects.exclude(id=user.id).filter(username=username).exists():
        messages.error(request, 'This username is already taken.')
        return redirect(f"{reverse('dashboard')}?tab=profile")

    profile.gender = request.POST.get('gender') or ''
    profile.marital_status = request.POST.get('marital_status') or ''
    profile.phone_number = request.POST.get('phone_number') or ''
    profile.address = request.POST.get('address') or ''

    from datetime import datetime
    dob = (request.POST.get('date_of_birth') or '').strip()
    if dob:
        profile.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
    else:
        profile.date_of_birth = None

    if request.FILES.get('profile_picture'):
        profile.profile_picture = request.FILES['profile_picture']

    try:
        profile.save()
    except Exception:
        messages.error(
            request,
            'Could not upload your photo. Check Cloudinary settings on the server, then try again.',
        )
        return redirect(f"{reverse('dashboard')}?tab=profile")

    user.username = username
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.save()

    messages.success(request, 'Your profile has been updated successfully!')
    return redirect(f"{reverse('dashboard')}?tab=profile")




@login_required
def all_profiles(request):
    """
    Display all registered user profiles with search and filter
    """
    # Get all profiles
    profiles_list = Profile.objects.select_related('user').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        profiles_list = profiles_list.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Filter by gender
    gender_filter = request.GET.get('gender', '')
    if gender_filter:
        profiles_list = profiles_list.filter(gender=gender_filter)
    
    # Pagination (12 profiles per page)
    paginator = Paginator(profiles_list, 12)
    page_number = request.GET.get('page')
    profiles = paginator.get_page(page_number)
    
    context = {
        'profiles': profiles,
        'total_members': Profile.objects.count(),
        'search_query': search_query,
        'gender_filter': gender_filter,
    }
    return render(request, 'users/all_profiles.html', context)


@login_required
def profile_detail(request, username):
    """
    Display detailed profile of a specific user
    """
    profile = get_object_or_404(Profile, user__username=username)
    
    context = {
        'viewed_profile': profile,
    }
    return render(request, 'users/profile_details.html', context)




# ============================================================
# USER VIEWS
# ============================================================

@login_required
def user_dashboard(request):
    """
    Unified Dashboard - Handles both regular users and staff.
    """
    active_tab = request.POST.get('tab') or request.GET.get('tab', 'overview')
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    context = {
        'active_tab': active_tab,
        'profile': profile,
    }

    if user.is_staff:
        all_profiles_list = Profile.objects.select_related('user').all()
        member_search = request.GET.get('member_search', '')
        if member_search:
            all_profiles_list = all_profiles_list.filter(
                Q(user__username__icontains=member_search) |
                Q(user__first_name__icontains=member_search) |
                Q(user__last_name__icontains=member_search)
            )

        member_form = AdminMemberForm()
        edit_member_form = None

        if active_tab == 'members' and request.method == 'POST':
            action = request.POST.get('action', '')
            if action == 'add_member':
                member_form = AdminMemberForm(request.POST)
                if member_form.is_valid():
                    user = member_form.save()
                    messages.success(
                        request,
                        f'Member "{user.get_full_name() or user.username}" registered successfully.',
                    )
                    return redirect(f"{reverse('dashboard')}?tab=members")
                messages.error(request, 'Could not register member. Check the form below.')
            elif action == 'edit_member':
                user_id = request.POST.get('user_id')
                target = User.objects.filter(id=user_id).first()
                if not target:
                    messages.error(request, 'Member not found.')
                    return redirect(f"{reverse('dashboard')}?tab=members")
                if target.is_staff and target.id != request.user.id:
                    messages.error(request, 'You cannot edit another staff account here.')
                    return redirect(f"{reverse('dashboard')}?tab=members")
                edit_member_form = AdminEditMemberForm(
                    request.POST, target_user=target
                )
                if edit_member_form.is_valid():
                    edit_member_form.save()
                    messages.success(
                        request,
                        f'Account "{target.get_full_name() or target.username}" updated successfully.',
                    )
                    return redirect(f"{reverse('dashboard')}?tab=members")
                messages.error(request, 'Could not update member. Check the form below.')
            elif action == 'delete_member':
                user_id = request.POST.get('user_id')
                target = User.objects.filter(id=user_id).first()
                if not target:
                    messages.error(request, 'Member not found.')
                    return redirect(f"{reverse('dashboard')}?tab=members")
                if target.id == request.user.id:
                    messages.error(request, 'You cannot delete your own account.')
                    return redirect(f"{reverse('dashboard')}?tab=members")
                if target.is_staff:
                    messages.error(request, 'Staff accounts cannot be deleted from here.')
                    return redirect(f"{reverse('dashboard')}?tab=members")
                target.delete()
                messages.success(request, 'Member deleted successfully.')
                return redirect(f"{reverse('dashboard')}?tab=members")

        context.update({
            'all_profiles': all_profiles_list,
            'admin_stats': {'total_members': Profile.objects.count()},
            'member_search': member_search,
            'member_form': member_form,
            'edit_member_form': edit_member_form,
            'dash_stats': {
                'videos': Video.objects.count(),
                'pdfs': PDFGuide.objects.count(),
                'slides': Slide.objects.count(),
                'members': Profile.objects.count(),
            },
        })

        if active_tab == 'site_settings':
            site = SiteSettings.load()
            if request.method == 'POST':
                form = SiteSettingsForm(request.POST, request.FILES, instance=site)
                if form.is_valid():
                    site = form.save()

                    def _read_list(key):
                        raw = request.POST.getlist(key)
                        out = []
                        for v in raw:
                            v = (v or '').strip()
                            if v:
                                out.append(v)
                        return out

                    method_titles = request.POST.getlist('donation_title[]')
                    method_icons = request.POST.getlist('donation_icon[]')
                    r1_labels = request.POST.getlist('donation_row1_label[]')
                    r1_values = request.POST.getlist('donation_row1_value[]')
                    r2_labels = request.POST.getlist('donation_row2_label[]')
                    r2_values = request.POST.getlist('donation_row2_value[]')
                    r3_labels = request.POST.getlist('donation_row3_label[]')
                    r3_values = request.POST.getlist('donation_row3_value[]')

                    pillar_names = request.POST.getlist('pillar_name[]')
                    pillar_descs = request.POST.getlist('pillar_desc[]')
                    pillar_accents = request.POST.getlist('pillar_accent[]')
                    pillars = []
                    for name, desc, accent in zip(pillar_names, pillar_descs, pillar_accents):
                        name = (name or '').strip()
                        desc = (desc or '').strip()
                        accent = (accent or '').strip() or '#245A42'
                        if not name and not desc:
                            continue
                        pillars.append({'name': name, 'description': desc, 'accent': accent})

                    site.home_pillars = pillars

                    methods = []
                    rows_len = max(len(method_titles), len(method_icons), len(r1_labels), len(r1_values), len(r2_labels), len(r2_values), len(r3_labels), len(r3_values))
                    for i in range(rows_len):
                        title = (method_titles[i] if i < len(method_titles) else '').strip()
                        icon = (method_icons[i] if i < len(method_icons) else '').strip() or 'bi-bank2'
                        row1 = {
                            'label': (r1_labels[i] if i < len(r1_labels) else '').strip(),
                            'value': (r1_values[i] if i < len(r1_values) else '').strip(),
                        }
                        row2 = {
                            'label': (r2_labels[i] if i < len(r2_labels) else '').strip(),
                            'value': (r2_values[i] if i < len(r2_values) else '').strip(),
                        }
                        row3 = {
                            'label': (r3_labels[i] if i < len(r3_labels) else '').strip(),
                            'value': (r3_values[i] if i < len(r3_values) else '').strip(),
                        }
                        rows = [r for r in [row1, row2, row3] if r.get('label') or r.get('value')]
                        if not title and not rows:
                            continue
                        methods.append({'title': title or 'Payment method', 'icon': icon, 'rows': rows})

                    site.donation_methods = methods

                    site.video_categories = _read_list('video_category[]')
                    site.pdf_categories = _read_list('pdf_category[]')
                    site.slide_categories = _read_list('slide_category[]')
                    site.gallery_categories = _read_list('gallery_category[]')
                    site.save(update_fields=[
                        'home_pillars',
                        'donation_methods',
                        'video_categories',
                        'pdf_categories',
                        'slide_categories',
                        'gallery_categories',
                    ])
                    messages.success(request, 'Site settings saved successfully.')
                    return redirect(f"{reverse('dashboard')}?tab=site_settings")
                messages.error(request, 'Please correct the errors below.')
            else:
                form = SiteSettingsForm(instance=site)
            context['site_settings_form'] = form
            context['home_pillars'] = site.home_pillars or []
            context['donation_methods'] = site.donation_methods or []
            context['video_categories'] = site.video_categories or []
            context['pdf_categories'] = site.pdf_categories or []
            context['slide_categories'] = site.slide_categories or []
            context['gallery_categories'] = site.gallery_categories or []

        elif active_tab == 'landing_page':
            all_videos = Video.objects.order_by(
                'homepage_order', '-created_at'
            )
            all_services = ProfessionalSupportService.objects.order_by(
                'homepage_order', 'order', '-created_at'
            )
            context['all_videos'] = all_videos
            context['all_services'] = all_services
            context['featured_videos_count'] = all_videos.filter(show_on_homepage=True).count()
            context['featured_services_count'] = all_services.filter(show_on_homepage=True).count()

            if request.method == 'POST':
                action = request.POST.get('action', 'save_selection')

                if action == 'add_service':
                    service_form = HomepageServiceForm(request.POST)
                    if service_form.is_valid():
                        service = service_form.save(commit=False)
                        if not service.show_on_homepage:
                            service.show_on_homepage = True
                        service.save()
                        messages.success(request, f'Service "{service.title}" added.')
                        return redirect(f"{reverse('dashboard')}?tab=landing_page")
                    context['service_form'] = service_form
                    messages.error(request, 'Could not add service. Check the form below.')

                else:
                    save_homepage_selection(request)
                    messages.success(request, 'Landing page selection saved.')
                    return redirect(f"{reverse('dashboard')}?tab=landing_page")

            if 'service_form' not in context:
                context['service_form'] = HomepageServiceForm(initial={'show_on_homepage': True})

        elif active_tab == 'resources':
            video_q = request.GET.get('video_q', '').strip()
            pdf_q = request.GET.get('pdf_q', '').strip()
            slide_q = request.GET.get('slide_q', '').strip()
            manage_section = request.GET.get('section', 'videos')

            videos_qs = Video.objects.order_by('-created_at')
            pdfs_qs = PDFGuide.objects.order_by('-created_at')
            slides_qs = Slide.objects.order_by('-created_at')

            if video_q:
                videos_qs = videos_qs.filter(
                    Q(title__icontains=video_q) | Q(description__icontains=video_q) | Q(instructor__icontains=video_q)
                )
            if pdf_q:
                pdfs_qs = pdfs_qs.filter(
                    Q(title__icontains=pdf_q) | Q(description__icontains=pdf_q) | Q(author__icontains=pdf_q)
                )
            if slide_q:
                slides_qs = slides_qs.filter(
                    Q(title__icontains=slide_q) | Q(description__icontains=slide_q) | Q(presenter__icontains=slide_q)
                )

            context.update({
                'resource_stats': {
                    'videos': Video.objects.count(),
                    'pdfs': PDFGuide.objects.count(),
                    'slides': Slide.objects.count(),
                },
                'library_videos': videos_qs,
                'library_pdfs': pdfs_qs,
                'library_slides': slides_qs,
                'video_q': video_q,
                'pdf_q': pdf_q,
                'slide_q': slide_q,
                'manage_section': manage_section,
            })

            video_form = VideoForm()
            pdf_form = PDFGuideForm()
            slide_form = SlideForm()

            if request.method == 'POST':
                action = request.POST.get('action', '')

                if action == 'add_video':
                    video_form = VideoForm(request.POST, request.FILES)
                    if video_form.is_valid():
                        video = video_form.save()
                        if request.POST.get('feature_on_homepage') == 'on':
                            video.show_on_homepage = True
                            video.homepage_order = int(request.POST.get('homepage_order', 0) or 0)
                            video.save(update_fields=['show_on_homepage', 'homepage_order'])
                        messages.success(request, 'Video added successfully.')
                        return redirect(f"{reverse('dashboard')}?tab=resources&section=videos")
                    messages.error(request, 'Fix errors in the video form.')

                elif action == 'add_pdf':
                    pdf_form = PDFGuideForm(request.POST, request.FILES)
                    if pdf_form.is_valid():
                        pdf_form.save()
                        messages.success(request, 'PDF guide added successfully.')
                        return redirect(f"{reverse('dashboard')}?tab=resources&section=pdfs")
                    messages.error(request, 'Fix errors in the PDF form.')

                elif action == 'add_slide':
                    slide_form = SlideForm(request.POST, request.FILES)
                    if slide_form.is_valid():
                        slide_form.save()
                        messages.success(request, 'Slides added successfully.')
                        return redirect(f"{reverse('dashboard')}?tab=resources&section=slides")
                    messages.error(request, 'Fix errors in the slides form.')

                elif action == 'toggle_video_home':
                    video = get_object_or_404(Video, pk=request.POST.get('video_id'))
                    video.show_on_homepage = not video.show_on_homepage
                    video.save(update_fields=['show_on_homepage'])
                    state = 'featured on' if video.show_on_homepage else 'removed from'
                    messages.success(request, f'"{video.title}" {state} the homepage.')
                    return redirect(f"{reverse('dashboard')}?tab=resources&section=videos")

            context['video_form'] = video_form
            context['pdf_form'] = pdf_form
            context['slide_form'] = slide_form
    
    return render(request, 'users/dashboard.html', context)


@staff_member_required
def admin_dashboard(request):
    """Redirect to the unified dashboard."""
    return redirect(f"{reverse('dashboard')}?tab=members")