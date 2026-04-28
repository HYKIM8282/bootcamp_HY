from django import forms
from .models import BrokerImage


class BrokerImageForm(forms.ModelForm):
    """detail 페이지에서 이미지 업로드할 때 쓰는 폼"""

    class Meta:
        model  = BrokerImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control form-control-sm',
                'accept': 'image/*',
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '사진 설명 (선택사항)',
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'image':      '이미지 파일',
            'caption':    '사진 설명',
            'is_primary': '대표 이미지로 설정',
        }