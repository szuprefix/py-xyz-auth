from django.dispatch import Signal

to_bind_user = Signal(providing_args=["old_user", "new_user"])
to_get_user_profile = Signal(providing_args=["user", "request"])
to_get_user_roles = Signal(providing_args=["user"])
to_save_user_profile = Signal(providing_args=['user', 'profile'])
to_get_role_model_map = Signal(providing_args=[])
to_change_user_name = Signal(providing_args=["user", "created"])