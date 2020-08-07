from django.dispatch import Signal

to_bind_user = Signal(providing_args=["old_user", "new_user"])
to_get_user_profile = Signal(providing_args=["user", "request"])
to_save_user_profile = Signal(providing_args=['user', 'profile'])
