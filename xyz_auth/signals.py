from django.dispatch import Signal

to_bind_user = Signal()
to_get_user_profile = Signal()
to_get_user_roles = Signal()
to_save_user_profile = Signal()
to_get_role_model_map = Signal()
to_change_user_name = Signal()
