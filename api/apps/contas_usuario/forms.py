from django import forms


class SignupForm(forms.Form):
    """Extra allauth signup fields (Q12-2). The name is optional and editable later in Perfil."""

    nome = forms.CharField(max_length=150, required=False)

    def signup(self, request, user):
        # Required by allauth; AccountAdapter.save_user already stored the name.
        pass
