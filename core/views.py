from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import OperationalError
from .models import GalleryItem, Video, PDFGuide, Slide, ProfessionalSupportService
from .forms import GalleryItemForm, VideoForm, PDFGuideForm, SlideForm
from .resource_redirect import redirect_after_resource_action

HOME_VIDEOS_PER_PAGE = 3
HOME_SERVICES_PER_PAGE = 3


# Create your views here.
def home_view(request):
    videos_qs = (
        Video.objects.filter(show_on_homepage=True)
        .order_by('homepage_order', '-created_at')
    )
    videos_paginator = Paginator(videos_qs, HOME_VIDEOS_PER_PAGE)
    featured_videos = videos_paginator.get_page(request.GET.get('videos_page'))

    try:
        services_qs = (
            ProfessionalSupportService.objects.filter(show_on_homepage=True)
            .order_by('homepage_order', 'order', '-created_at')
        )
        services_paginator = Paginator(services_qs, HOME_SERVICES_PER_PAGE)
        services = services_paginator.get_page(request.GET.get('services_page'))
    except OperationalError:
        services = []

    return render(request, 'core/index.html', {
        'featured_videos': featured_videos,
        'services': services,
        'videos_page_num': request.GET.get('videos_page', '1'),
        'services_page_num': request.GET.get('services_page', '1'),
    })


def gallery_view(request):
    if request.method == 'POST' and request.user.is_staff:
        form = GalleryItemForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
            except Exception:
                messages.error(
                    request,
                    'Could not upload the image. Check Cloudinary settings on the server, then try again.',
                )
            else:
                messages.success(request, 'Image uploaded successfully!')
                return redirect('gallery')
        else:
            messages.error(request, 'Please fix the errors in the upload form.')
    else:
        form = GalleryItemForm()
        
    active_category = request.GET.get('category')
    if active_category:
        gallery_items_list = GalleryItem.objects.filter(category=active_category)
    else:
        gallery_items_list = GalleryItem.objects.all()
        
    paginator = Paginator(gallery_items_list, 6)
    page_number = request.GET.get('page')
    gallery_items = paginator.get_page(page_number)
        
    return render(request, 'core/gallery.html', {
        'gallery_items': gallery_items,
        'gallery_form': form,
        'active_category': active_category
    })


def edit_gallery_item(request, pk):
    if not request.user.is_staff:
        return redirect('gallery')
    
    item = get_object_or_404(GalleryItem, pk=pk)
    if request.method == 'POST':
        form = GalleryItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            try:
                form.save()
            except Exception:
                messages.error(
                    request,
                    'Could not upload the image. Check Cloudinary settings on the server, then try again.',
                )
            else:
                messages.success(request, 'Image updated successfully!')
                return redirect('gallery')
        else:
            messages.error(request, 'Please fix the errors in the form.')
    else:
        form = GalleryItemForm(instance=item)
    
    return render(request, 'core/edit_gallery.html', {'form': form, 'item': item})


def delete_gallery_item(request, pk):
    if not request.user.is_staff:
        return redirect('gallery')
    
    item = get_object_or_404(GalleryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('gallery')
    
    return render(request, 'core/delete_gallery_confirm.html', {'item': item})


def pdf_view(request):
    if request.method == 'POST' and request.user.is_staff:
        form = PDFGuideForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'PDF Guide added successfully!')
            return redirect('pdf_list')
    else:
        form = PDFGuideForm()

    query = request.GET.get('q')
    if query:
        pdfs_list = PDFGuide.objects.filter(title__icontains=query) | PDFGuide.objects.filter(description__icontains=query)
    else:
        pdfs_list = PDFGuide.objects.all()

    paginator = Paginator(pdfs_list, 6)
    page_number = request.GET.get('page')
    pdfs = paginator.get_page(page_number)

    return render(request, 'core/pdf_list.html', {
        'pdfs': pdfs,
        'pdf_form': form,
        'query': query
    })


def edit_pdf_view(request, pk):
    if not request.user.is_staff:
        return redirect('pdf_list')
    
    pdf = get_object_or_404(PDFGuide, pk=pk)
    if request.method == 'POST':
        form = PDFGuideForm(request.POST, request.FILES, instance=pdf)
        if form.is_valid():
            form.save()
            messages.success(request, 'PDF Guide updated successfully!')
            return redirect(redirect_after_resource_action(request, 'pdf_list'))
    else:
        form = PDFGuideForm(instance=pdf)

    return render(request, 'core/edit_pdf.html', {
        'form': form,
        'pdf': pdf,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def delete_pdf_view(request, pk):
    if not request.user.is_staff:
        return redirect('pdf_list')
    
    pdf = get_object_or_404(PDFGuide, pk=pk)
    if request.method == 'POST':
        pdf.delete()
        messages.success(request, 'PDF Guide deleted successfully!')
        return redirect(redirect_after_resource_action(request, 'pdf_list'))

    return render(request, 'core/delete_pdf_confirm.html', {
        'pdf': pdf,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def video_view(request):
    if request.method == 'POST' and request.user.is_staff:
        form = VideoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video added successfully!')
            return redirect('video_list')
    else:
        form = VideoForm()

    query = request.GET.get('q')
    if query:
        videos_list = Video.objects.filter(title__icontains=query) | Video.objects.filter(description__icontains=query)
    else:
        videos_list = Video.objects.all()

    paginator = Paginator(videos_list, 6)
    page_number = request.GET.get('page')
    videos = paginator.get_page(page_number)

    return render(request, 'core/video_list.html', {
        'videos': videos,
        'video_form': form,
        'query': query
    })


def edit_video_view(request, pk):
    if not request.user.is_staff:
        return redirect('video_list')
    
    video = get_object_or_404(Video, pk=pk)
    if request.method == 'POST':
        form = VideoForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video updated successfully!')
            return redirect(redirect_after_resource_action(request, 'video_list'))
    else:
        form = VideoForm(instance=video)

    return render(request, 'core/edit_video.html', {
        'form': form,
        'video': video,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def delete_video_view(request, pk):
    if not request.user.is_staff:
        return redirect('video_list')
    
    video = get_object_or_404(Video, pk=pk)
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Video deleted successfully!')
        return redirect(redirect_after_resource_action(request, 'video_list'))

    return render(request, 'core/delete_video_confirm.html', {
        'video': video,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def slides_view(request):
    if request.method == 'POST' and request.user.is_staff:
        form = SlideForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Presentation added successfully!')
            return redirect('slides_list')
    else:
        form = SlideForm()

    query = request.GET.get('q')
    if query:
        slides_list = Slide.objects.filter(title__icontains=query) | Slide.objects.filter(description__icontains=query)
    else:
        slides_list = Slide.objects.all()

    paginator = Paginator(slides_list, 6)
    page_number = request.GET.get('page')
    slides = paginator.get_page(page_number)

    return render(request, 'core/slides_list.html', {
        'slides': slides,
        'slide_form': form,
        'query': query
    })


def edit_slide_view(request, pk):
    if not request.user.is_staff:
        return redirect('slides_list')
    
    slide = get_object_or_404(Slide, pk=pk)
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Presentation updated successfully!')
            return redirect(redirect_after_resource_action(request, 'slides_list'))
    else:
        form = SlideForm(instance=slide)

    return render(request, 'core/edit_slide.html', {
        'form': form,
        'slide': slide,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def delete_slide_view(request, pk):
    if not request.user.is_staff:
        return redirect('slides_list')
    
    slide = get_object_or_404(Slide, pk=pk)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Presentation deleted successfully!')
        return redirect(redirect_after_resource_action(request, 'slides_list'))

    return render(request, 'core/delete_slide_confirm.html', {
        'slide': slide,
        'return_to_dashboard': request.GET.get('return') == 'dashboard',
    })


def professional_support_view(request):
    services_qs = ProfessionalSupportService.objects.order_by('order', 'homepage_order', '-created_at')
    paginator = Paginator(services_qs, 9)
    services = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/professional_support.html', {'services': services})


def about_view(request):
    return render(request, 'core/about.html')


def partners_view(request):
    return render(request, 'core/partners.html')

