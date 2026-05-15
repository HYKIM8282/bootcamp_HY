from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):

    class Meta:
        model  = Review
        fields = ['score', 'content', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ 별점 선택 위젯
        self.fields['score'].widget = forms.Select(
            choices=Review.SCORE_CHOICES,
            attrs={
                'class': 'form-select form-select-sm',
            }
        )

        # ✅ 리뷰 내용 위젯
        self.fields['content'].widget = forms.Textarea(
            attrs={
                'class': 'form-control form-control-sm',
                'rows': 3,
                'placeholder': '리뷰를 작성해주세요.',
            }
        )

        # ✅ 리뷰 이미지 위젯
        self.fields['image'].widget = forms.ClearableFileInput(
            attrs={
                'class': 'form-control form-control-sm',
                'accept': 'image/*',
            }
        )
        self.fields['image'].required = False