"""
Copyright 2020 ООО «Верме»
"""

from django.db import models
from django.db.models.expressions import RawSQL
from django.db.models import Q


class OrganizationQuerySet(models.QuerySet):
    def tree_downwards(self, root_org_id):
        """
        Возвращает корневую организацию с запрашиваемым root_org_id и всех её детей любого уровня вложенности
        Метод запрашивает все объекты базы и на основе root_org_id выстраивает дерево зависимостей, собирая id 
        всех потомков искомого объекта в списке children_id.

        :type root_org_id: int
        """
        values_vault = list(self.all().values('id', 'parent_id').order_by('id'))
        children_id = [root_org_id, ]
        for item in values_vault:
            if item['parent_id'] in children_id:
                children_id.append(item['id'])
        values_vault.clear() # очищаем первичный список что бы не засорять память
        return self.filter(id__in=children_id)

    def tree_upwards(self, child_org_id):
        """
        Возвращает корневую организацию с запрашиваемым child_org_id и всех её родителей любого уровня вложенности
        Метод запрашивает все объекты базы и на основе child_org_id выстраивает дерево зависимостей, собирая id 
        всех родителей искомого объекта в списке parents_id

        :type child_org_id: int
        """
        values_vault = list(self.all().values('id', 'parent_id').order_by('-id'))
        parents_id = [child_org_id, ]
        for item in values_vault:
            if item['id'] in parents_id:
                parents_id.append(item['parent_id'])
        values_vault.clear() # очищаем первичный список что бы не засорять память
        return self.filter(id__in=parents_id)


class Organization(models.Model):
    """ Организаци """

    objects = OrganizationQuerySet.as_manager()

    name = models.CharField(max_length=1000, blank=False, null=False, verbose_name="Название")
    code = models.CharField(max_length=1000, blank=False, null=False, unique=True, verbose_name="Код")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, verbose_name="Вышестоящая организация",
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Организация"
        verbose_name = "Организации"

    def parents(self):
        """
        Возвращает всех родителей любого уровня вложенности

        :rtype: django.db.models.QuerySet
        """
        return type(self).objects.tree_upwards(self.id).exclude(id=self.id)

    def children(self):
        """
        Возвращает всех детей любого уровня вложенности

        :rtype: django.db.models.QuerySet
        """
        return type(self).objects.tree_downwards(self.id).exclude(id=self.id)

    def __str__(self):
       return self.name