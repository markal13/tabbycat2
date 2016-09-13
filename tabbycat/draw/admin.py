from django.contrib import admin
from django.core.exceptions import MultipleObjectsReturned


from adjallocation.models import DebateAdjudicator
from participants.models import Team
from utils.admin import TabbycatModelAdminFieldsMixin

from .models import Debate, DebateTeam


# ==============================================================================
# DebateTeam
# ==============================================================================

class DebateTeamAdmin(TabbycatModelAdminFieldsMixin, admin.ModelAdmin):
    list_display = ('team', 'position', 'debate', 'get_tournament', 'get_round')
    search_fields = ('team', )
    raw_id_fields = ('debate', 'team', )

    def get_queryset(self, request):
        return super(DebateTeamAdmin, self).get_queryset(request).select_related(
                'debate__round', 'debate__round__tournament', 'team__tournament').prefetch_related(
                'debate__debateteam_set__team')


admin.site.register(DebateTeam, DebateTeamAdmin)


# ==============================================================================
# Debate
# ==============================================================================

class DebateTeamInline(admin.TabularInline):
    model = DebateTeam
    extra = 1
    raw_id_fields = ('team', )


class DebateAdjudicatorInline(admin.TabularInline):
    model = DebateAdjudicator
    extra = 1


class DebateAdmin(admin.ModelAdmin):
    list_display = ('id', 'round', 'bracket', 'get_aff_team', 'get_neg_team',
                    'result_status')
    list_filter = ('round__tournament', 'round', 'division')
    inlines = (DebateTeamInline, DebateAdjudicatorInline)
    raw_id_fields = ('venue', 'division')

    def get_queryset(self, request):
        return super(DebateAdmin, self).get_queryset(request).select_related(
            'round__tournament', 'division__tournament', 'venue__group').prefetch_related(
            'debateteam_set__team__tournament')

    def get_aff_team(self, obj):
        try:
            return obj.aff_team
        except MultipleObjectsReturned:
            return "<multiple affirmative teams>"
    get_aff_team.short_description = "Affirmative team"

    def get_neg_team(self, obj):
        try:
            return obj.neg_team
        except MultipleObjectsReturned:
            return "<multiple negative teams>"
    get_neg_team.short_description = "Negative team"

    actions = list()
    for value, verbose_name in Debate.STATUS_CHOICES:

        def _make_set_result_status(value, verbose_name):
            def _set_result_status(modeladmin, request, queryset):
                count = queryset.update(result_status=value)
                message_bit = "1 debate had its" if count == 1 else "{:d} debates had their".format(
                    count)
                modeladmin.message_user(
                    request, message_bit + " status set to " + verbose_name)

            # so that they look different to DebateAdmin
            _set_result_status.__name__ = "set_result_status_%s" % verbose_name.lower()
            _set_result_status.short_description = "Set result status to %s" % verbose_name.lower()
            return _set_result_status

        actions.append(_make_set_result_status(value, verbose_name))
    del value, verbose_name  # for fail-fast


admin.site.register(Debate, DebateAdmin)
