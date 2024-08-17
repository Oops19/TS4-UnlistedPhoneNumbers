#
# LICENSE https://creativecommons.org/licenses/by/4.0/ https://creativecommons.org/licenses/by/4.0/legalcode
# © 2024 https://github.com/Oops19
#

# Reviving:
"""
Unlisted Phone Numbers Mod
by Scumbumbo @ ModTheSims

Version 1 - 01/05/17
  - Initial version
"""


import services
import drama_scheduler.drama_node
from filters.tunable import FilterResult
from relationships.compatibility import Compatibility
from sims4.resources import Types, get_resource_key
from sims4.tuning.instance_manager import InstanceManager
from sims4communitylib.utils.common_injection_utils import CommonInjectionUtils
from sims4communitylib.utils.common_log_registry import CommonLogRegistry, CommonLog
from unlisted_phone_numbers.modinfo import ModInfo

log: CommonLog = CommonLogRegistry.get().register_log(ModInfo.get_identity(), ModInfo.get_identity().name)
log.enable()
log.debug(f"Starting {ModInfo.get_identity().name} v{ModInfo.get_identity().version} ")


class UnlistedPhoneNumbers:

    # <I c="PieMenuCategory" i="pie_menu_category" m="interactions.pie_menu_category" n="sim_SubCat_Friendly_Affection" s="318318">
    # <I c="PieMenuCategory" i="pie_menu_category" m="interactions.pie_menu_category" n="sim_Friendly" s="15507">

    EXCH_SIM_FILTER = 12075896583642316319  # o19_UPN_TunableSimFilter
    EXCH_NUM_RELBIT = 1513518307
    EXCH_NUM_SI = 10739892915446548452
    EXCH_NUM_RELPANEL = 14904983510535615869
    REVOKE_NUM_RELPANEL = 13005930575841500223
    MIXERS_SNIPPET_FRIENDLY = 24508  # <I c="AffordanceList" i="snippet" m="snippets" n="social_Mixers_Friendly_NonTouching" s="24508">
    OBJECT_SIM = 14965  # <I c="Sim" i="object" m="sims.sim" n="object_sim" s="14965">

    # Check whether this drama node should have an override.
    ALLOWED_NAME_SUBSTRINGS = ['Intro', 'MusicProductionStation', 'clubGatheringDramaNode_Default', 'Quirk_PublicNumber']

    @staticmethod
    def should_filter_node(node_name):
        for name_substring in UnlistedPhoneNumbers.ALLOWED_NAME_SUBSTRINGS:
            if name_substring in node_name:
                return False
        return True

    @staticmethod
    def add_filter_term(sim_filter, new_filter_term):
        # Adds a new filter term to a sim_filter object
        sim_filter._filter_terms += (new_filter_term,)

    @staticmethod
    def remove_filter_term(sim_filter, new_filter_term):
        # Removes a filter term from a sim_filter object

        # Convert the tuple to a list so we can remove an item from it
        filter_terms = list(sim_filter._filter_terms)
        # Remove the filter term from the list
        filter_terms.remove(new_filter_term)
        # Convert the list back to a tuple and overwrite the _filter_terms
        sim_filter._filter_terms = tuple(filter_terms)

    @staticmethod
    def calculate_score(*args, **kwargs):
        return FilterResult(score=0)

    @staticmethod
    def minimum_filter_score(*args, **kwargs):
        return 0

    @staticmethod
    @CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(), drama_scheduler.drama_node.BaseDramaNode, drama_scheduler.drama_node.BaseDramaNode._resolve_drama_participant.__name__)
    def UPN_resolve_drama_participant(original, self, drama_participant, resolver, *args, **kwargs):
        # This defines a new filter term prior to calling the original drama node scheduler
        # then removes the term again (in case that sim_filter is used by another non-drama picker)
        log.debug(f"UPN_resolve_drama_participant({self}, {drama_participant}, {resolver}, {args}, {kwargs})")

        (result, sim_info, score) = False, None, 0
        new_filter_term = None
        # Only add the new filter term if there is a sim_filter associated with this drama node
        if hasattr(drama_participant, 'sim_filter') and UnlistedPhoneNumbers.should_filter_node(str(self)):
            log.debug(f"Adding phone filter ...")

            # Define the new filter term - an inverted black_list of Sim's that have the Exchanged Numbers relationship bit
            # In other words, those who do not share that relationship bit will be rejected from consideration by the filter.
            # tuning_manager = services.get_instance_manager(Types.RELATIONSHIP_BIT)
            # relbit = tuning_manager.get(UnlistedPhoneNumbers.EXCH_NUM_RELBIT)

            tuning_manager_2 = services.get_instance_manager(Types.SIM_FILTER)
            new_filter_term = tuning_manager_2.get(UnlistedPhoneNumbers.EXCH_SIM_FILTER)

            # Append a suitable calculate_score()
            new_filter_term.calculate_score = UnlistedPhoneNumbers.calculate_score
            new_filter_term.minimum_filter_score = 0

            # Add our newly tuned filter_term to the existing sim_filter
            UnlistedPhoneNumbers.add_filter_term(drama_participant.sim_filter, new_filter_term)

        # Run the original _resolve_drama_participant method
        (result, sim_info, score) = original(self, drama_participant, resolver, *args, **kwargs)
        log.debug(f" --> ({result}, {sim_info}, {score})")

        # Remove the newly defined filter term (in case this sim_filter is used elsewhere) if one was defined
        if new_filter_term is not None:
            UnlistedPhoneNumbers.remove_filter_term(drama_participant.sim_filter, new_filter_term)

        # Return the results from calling the original method
        return (result, sim_info, score)

    @staticmethod
    @CommonInjectionUtils.inject_safely_into(ModInfo.get_identity(), InstanceManager, InstanceManager.load_data_into_class_instances.__name__)
    def EXCH_load_data_into_class_instances(original, self, *args, **kwargs):
        # Add our superinteractions to the friendly mixer snippet and the Sim object's relationship panel
        original(self, *args, **kwargs)
        # Add mixer interaction to the friendly mixers snippet
        if self.TYPE == Types.SNIPPET:
            # Get the superinteraction tuning
            si_exchange_numbers = services.affordance_manager().get(UnlistedPhoneNumbers.EXCH_NUM_SI)
            if si_exchange_numbers is None:
                return

            # Get the friendly mixer snippet
            tuning_manager = services.get_instance_manager(Types.SNIPPET)
            mixer_snippet = tuning_manager.get(UnlistedPhoneNumbers.MIXERS_SNIPPET_FRIENDLY)

            # And add our new superinteraction
            mixer_snippet.value += (si_exchange_numbers,)


        # Add the exchange numbers superinteractions to the Sim's relationship panel
        if self.TYPE == Types.OBJECT:
            # Get the two superinteractions to place on the Sim's relationship panels
            si_exchange_numbers = services.affordance_manager().get(UnlistedPhoneNumbers.EXCH_NUM_RELPANEL)
            if si_exchange_numbers is None:
                return
            si_revoke_number = services.affordance_manager().get(UnlistedPhoneNumbers.REVOKE_NUM_RELPANEL)
    
            # Get the sim_object tuning, retrieving this tuning requires accessing the
            # _tuned_classes of the object instance_tuning manager directly using the resource key.
            tuning_manager = services.get_instance_manager(Types.OBJECT)
            object_sim_key = get_resource_key(UnlistedPhoneNumbers.OBJECT_SIM, Types.OBJECT)
            object_sim = tuning_manager._tuned_classes[object_sim_key]
    
            # Add our two superinteractions to the _relation_panel_affordances of object_sim
            object_sim._relation_panel_affordances += (si_exchange_numbers, si_revoke_number)
