from django import forms
from .models import GalleryItem, Video, PDFGuide, Slide, SiteSettings, ProfessionalSupportService


def _json_list_to_choices(items):
    items = items or []
    cleaned = []
    for v in items:
        if not isinstance(v, str):
            continue
        v = v.strip()
        if v:
            cleaned.append(v)
    return [(v, v) for v in cleaned]

class GalleryItemForm(forms.ModelForm):
    class Meta:
        model = GalleryItem
        fields = ['title', 'image', 'category', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter image title'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Kigali, 2024'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = SiteSettings.load()
        choices = _json_list_to_choices(site.gallery_categories)
        if choices and 'category' in self.fields:
            self.fields['category'].choices = choices


class HomepageServiceForm(forms.ModelForm):
    class Meta:
        model = ProfessionalSupportService
        fields = [
            'title', 'description', 'image_url', 'image_alt',
            'tag_label', 'icon_class', 'show_on_homepage', 'homepage_order',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'image_alt': forms.TextInput(attrs={'class': 'form-control'}),
            'tag_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Data-Driven'}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-briefcase-fill'}),
            'show_on_homepage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'homepage_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'youtube_url', 'category', 'instructor', 'duration', 'description', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = SiteSettings.load()
        choices = _json_list_to_choices(site.video_categories)
        if choices and 'category' in self.fields:
            self.fields['category'].choices = choices

class PDFGuideForm(forms.ModelForm):
    class Meta:
        model = PDFGuide
        fields = ['title', 'category', 'author', 'pages', 'description', 'thumbnail', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = SiteSettings.load()
        choices = _json_list_to_choices(site.pdf_categories)
        if choices and 'category' in self.fields:
            self.fields['category'].choices = choices

class SlideForm(forms.ModelForm):
    class Meta:
        model = Slide
        fields = ['title', 'category', 'presenter', 'slides_count', 'description', 'thumbnail', 'slide_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'presenter': forms.TextInput(attrs={'class': 'form-control'}),
            'slides_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'slide_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = SiteSettings.load()
        choices = _json_list_to_choices(site.slide_categories)
        if choices and 'category' in self.fields:
            self.fields['category'].choices = choices


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = [
            'updated_at',
            'donation_methods',
            'home_pillars',
            'video_categories',
            'pdf_categories',
            'slide_categories',
            'gallery_categories',
        ]
        widgets = {
            'footer_tagline': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'home_hero_subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_hero_subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_vision_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_mission_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_history_paragraph_1': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_history_paragraph_2': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_cta_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs.setdefault('class', 'form-control')
                else:
                    field.widget.attrs.setdefault('class', 'form-control')
