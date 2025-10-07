from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile, BankAccount, CryptoWallet

class CustomUserCreationForm(UserCreationForm):
    referral_code = forms.CharField(required=False, help_text="Optional referral code from another user")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'referral_code')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'subscription_level')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('bio', 'profile_picture', 'country', 'phone_number')
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself, your skills, and experience...'
            }),
            'country': forms.TextInput(attrs={
                'placeholder': 'e.g., Nigeria, United States...'
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'e.g., +2348012345678'
            }),
        }
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.startswith('+'):
            raise forms.ValidationError("Please include country code (e.g., +2348012345678)")
        return phone_number

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ('bank_name', 'account_number', 'account_name', 'account_type', 'is_primary')
        widgets = {
            'bank_name': forms.TextInput(attrs={'placeholder': 'e.g., GTBank, Zenith Bank'}),
            'account_number': forms.TextInput(attrs={'placeholder': '10-digit account number'}),
            'account_name': forms.TextInput(attrs={'placeholder': 'Name as it appears on bank account'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        is_primary = cleaned_data.get('is_primary')
        user = getattr(self, 'user', None)
        
        if is_primary and user:
            BankAccount.objects.filter(user=user, is_primary=True).update(is_primary=False)
        
        return cleaned_data

class CryptoWalletForm(forms.ModelForm):
    class Meta:
        model = CryptoWallet
        fields = ('crypto_type', 'wallet_address', 'network', 'is_primary')
        widgets = {
            'wallet_address': forms.TextInput(attrs={'placeholder': 'Your cryptocurrency wallet address'}),
            'network': forms.TextInput(attrs={'placeholder': 'e.g., ERC20, BEP20, TRC20'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        is_primary = cleaned_data.get('is_primary')
        user = getattr(self, 'user', None)
        
        if is_primary and user:
            CryptoWallet.objects.filter(user=user, is_primary=True).update(is_primary=False)
        
        return cleaned_data