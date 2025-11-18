from django.db.models import TextChoices

class GenderChoice(TextChoices):
	Male = "Male"
	Female = "Female"
 
class AuthTypeChoice(TextChoices):
	Email = "Email"
	Phone = "Phone"
 
class AuthStatusChoice(TextChoices):
	New = "New"
	CodeVerified = "CodeVerified"
	Done = "Done"
	Finished = "Finished"