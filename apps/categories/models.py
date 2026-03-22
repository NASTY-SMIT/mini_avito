from django.db import models


class Category(models.Model):
    name = models.CharField(verbose_name="Category Name", max_length=100)
    slug = models.SlugField()

    def __str__(self):
        return f"Category of {self.slug}"

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
